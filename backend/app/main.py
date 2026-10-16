"""TaskFlow API: users own their tasks; no unauthenticated task access."""
import logging
import json
import secrets
import time
from urllib.parse import urlencode
from starlette.requests import Request
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import text
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "method",
            "path",
            "status_code",
            "duration_ms",
        ):
            if hasattr(record, key):
                data[key] = getattr(record, key)

        return json.dumps(data, ensure_ascii=False)
handler=logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'), handlers=[handler], force=True)
logger = logging.getLogger('taskflow')
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///./taskflow.db')
if DB_URL.startswith('postgres://'):
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgres://'):]
elif DB_URL.startswith('postgresql://'):
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgresql://'):]
SECRET = os.getenv('JWT_SECRET', '')
if not SECRET or len(SECRET) < 32:
    raise RuntimeError('JWT_SECRET must contain at least 32 characters')
if DB_URL.startswith('sqlite'):
    engine = create_engine(DB_URL, connect_args={'check_same_thread': False}, poolclass=StaticPool if DB_URL.endswith(':memory:') else None)
else:
    engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
ph = PasswordHasher()
bearer = HTTPBearer(auto_error=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tasks: Mapped[list['Task']] = relationship(back_populates='owner', cascade='all, delete-orphan')

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner: Mapped[User] = relationship(back_populates='tasks')

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    completed: bool

app = FastAPI(title='TaskFlow API', version='6.0.0')
@app.middleware("http")
async def log_http_requests(request: Request, call_next):
    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = round(
            (time.perf_counter() - start) * 1000, 2
        )

        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )
# Session cookie only holds a short-lived OAuth state; tokens never go into it.
app.add_middleware(SessionMiddleware, secret_key=SECRET, same_site='lax', https_only=os.getenv('COOKIE_SECURE', 'false').lower()=='true')
GOOGLE_ID=os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_SECRET=os.getenv('GOOGLE_CLIENT_SECRET', '')
FRONTEND_URL=os.getenv('FRONTEND_URL','http://localhost:8080').rstrip('/')
oauth=OAuth()
if GOOGLE_ID and GOOGLE_SECRET:
    oauth.register('google',client_id=GOOGLE_ID,client_secret=GOOGLE_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope':'openid email profile'})
# Temporary single-use exchange tickets; multi-worker deployments should use Redis.
oauth_tickets: dict[str, tuple[int,float]] = {}
origins = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'], allow_headers=['Authorization','Content-Type'])

def db_session():
    with SessionLocal() as db:
        yield db

DB = Annotated[Session, Depends(db_session)]

@app.get('/health/ready')
def ready(db: DB):
    try:
        db.execute(text('SELECT 1'))
    except Exception:
        raise HTTPException(503, 'Database unavailable')
    return {'status':'ready', 'database':'ok'}

def normalized_title(title: str) -> str:
    value = title.strip()
    if not value:
        raise HTTPException(422, 'Название задачи не может быть пустым')
    return value

def issue_token(user_id: int) -> Token:
    return Token(access_token=jwt.encode({'sub': str(user_id), 'exp': datetime.now(timezone.utc) + timedelta(hours=8)}, SECRET, algorithm='HS256'))

def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: DB) -> User:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(401, 'Требуется авторизация', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=['HS256'])
        user = db.get(User, int(payload['sub']))
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        user = None
    if user is None:
        raise HTTPException(401, 'Недействительный токен', headers={'WWW-Authenticate': 'Bearer'})
    return user

UserAuth = Annotated[User, Depends(current_user)]

@app.get('/auth/google/login')
async def google_login(request: Request):
    if not GOOGLE_ID or not GOOGLE_SECRET:
        raise HTTPException(503,'Google OAuth is not configured')
    callback=str(request.url_for('google_callback'))
    return await oauth.google.authorize_redirect(request, callback)
@app.get('/auth/google/callback', name='google_callback')
async def google_callback(request: Request, db: DB):
    if not GOOGLE_ID or not GOOGLE_SECRET:
        raise HTTPException(503,'Google OAuth is not configured')
    try:
        tokens=await oauth.google.authorize_access_token(request)
        claims=tokens.get('userinfo')
        if not claims or not claims.get('email_verified'):
            raise ValueError('Email not verified')
        email=claims['email'].strip().lower()
    except Exception:
        logger.warning('OAuth callback rejected')
        return RedirectResponse(FRONTEND_URL+'/?oauth_error=login_failed',status_code=303)
    user=db.scalar(select(User).where(User.email==email))
    if not user:
        user=User(email=email,password_hash=ph.hash(secrets.token_urlsafe(48)))
        db.add(user);db.commit();db.refresh(user)
    ticket=secrets.token_urlsafe(32)
    oauth_tickets[ticket]=(user.id,time.monotonic()+60)
    return RedirectResponse(FRONTEND_URL+'/?'+urlencode({'oauth_ticket':ticket}),status_code=303)
class OAuthTicket(BaseModel):
    ticket: str = Field(min_length=30, max_length=150)
@app.post('/auth/google/exchange', response_model=Token)
def exchange_oauth(payload: OAuthTicket):
    item=oauth_tickets.pop(payload.ticket,None)
    if item is None or item[1] < time.monotonic():
        raise HTTPException(401,'Invalid or expired ticket')
    return issue_token(item[0])

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/auth/register', response_model=Token, status_code=201)
def register(payload: Credentials, db: DB):
    email = payload.email.strip().lower()
    if '@' not in email or email.startswith('@') or email.endswith('@'):
        raise HTTPException(422, 'Некорректный email')
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, 'Пользователь существует')
    user = User(email=email, password_hash=ph.hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception('Registration DB error')
        raise HTTPException(409, 'Не удалось зарегистрировать пользователя')
    db.refresh(user)
    logger.info('New user registered id=%s', user.id)
    return issue_token(user.id)

@app.post('/auth/login', response_model=Token)
def login(payload: Credentials, db: DB):
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    try:
        valid = bool(user and ph.verify(user.password_hash, payload.password))
    except (VerifyMismatchError, VerificationError):
        valid = False
    if not valid:
        raise HTTPException(401, 'Неверный email или пароль')
    return issue_token(user.id)

@app.get('/tasks', response_model=list[TaskOut])
def list_tasks(db: DB, user: UserAuth, completed: bool | None = None, search: str | None = Query(default=None, max_length=120)):
    stmt = select(Task).where(Task.user_id == user.id)
    if completed is not None:
        stmt = stmt.where(Task.completed == completed)
    if search and search.strip():
        stmt = stmt.where(Task.title.ilike(f'%{search.strip().replace("%", r"\%").replace("_", r"\_")}%'))
    return db.scalars(stmt.order_by(Task.id.desc())).all()

@app.post('/tasks', response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: DB, user: UserAuth):
    task = Task(user_id=user.id, title=normalized_title(payload.title), completed=False)
    db.add(task); db.commit(); db.refresh(task)
    logger.info('Task created id=%s user=%s', task.id, user.id)
    return task

def get_owned_task(task_id: int, db: Session, user: User) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if not task:
        raise HTTPException(404, 'Задача не найдена')
    return task

@app.get('/tasks/{task_id}', response_model=TaskOut)
def get_task(task_id: int, db: DB, user: UserAuth):
    return get_owned_task(task_id, db, user)

@app.patch('/tasks/{task_id}', response_model=TaskOut)
def patch_task(task_id: int, payload: TaskPatch, db: DB, user: UserAuth):
    task = get_owned_task(task_id, db, user)
    if payload.title is not None:
        task.title = normalized_title(payload.title)
    if payload.completed is not None:
        task.completed = payload.completed
    db.commit(); db.refresh(task)
    return task

@app.delete('/tasks/{task_id}', status_code=204)
def delete_task(task_id: int, db: DB, user: UserAuth):
    db.delete(get_owned_task(task_id, db, user)); db.commit()
