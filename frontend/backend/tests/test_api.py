import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET'] = 'unit-test-secret-which-is-longer-than-32-chars'
from fastapi.testclient import TestClient
from app.main import app, Base, engine
import pytest

@pytest.fixture(autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

def auth(client, email='first@example.com'):
    r = client.post('/auth/register', json={'email':email, 'password':'password123'})
    assert r.status_code == 201, r.text
    return {'Authorization': f"Bearer {r.json()['access_token']}"}

def test_registration_login_and_duplicate(client):
    headers=auth(client)
    assert client.post('/auth/register', json={'email':'first@example.com','password':'password123'}).status_code == 409
    assert client.post('/auth/login', json={'email':'first@example.com','password':'wrongpassword'}).status_code == 401
    assert client.post('/auth/login', json={'email':'first@example.com','password':'password123'}).status_code == 200
    assert client.get('/tasks', headers=headers).json() == []

def test_unauthorized(client):
    assert client.get('/tasks').status_code == 401
    assert client.get('/tasks',headers={'Authorization':'Bearer invalid'}).status_code == 401

def test_full_crud(client):
    h=auth(client)
    r=client.post('/tasks', json={'title':' Write tests '},headers=h)
    assert r.status_code == 201
    task=r.json(); assert task['title']=='Write tests'
    assert client.get(f"/tasks/{task['id']}",headers=h).status_code == 200
    assert client.patch(f"/tasks/{task['id']}",json={'completed':True},headers=h).json()['completed']
    assert len(client.get('/tasks?completed=true&search=WRITE',headers=h).json()) == 1
    assert client.delete(f"/tasks/{task['id']}",headers=h).status_code == 204
    assert client.get(f"/tasks/{task['id']}",headers=h).status_code == 404

def test_isolation(client):
    h1=auth(client)
    task=client.post('/tasks',json={'title':'private'},headers=h1).json()['id']
    h2=auth(client,'second@example.com')
    assert client.get('/tasks',headers=h2).json() == []
    for method in ('get','patch','delete'):
        kwargs={'json':{'completed':True}} if method=='patch' else {}
        assert getattr(client,method)(f'/tasks/{task}',headers=h2,**kwargs).status_code==404
    assert len(client.get('/tasks',headers=h1).json())==1

def test_validation(client):
    h=auth(client)
    assert client.post('/tasks',json={'title':'  '},headers=h).status_code==422
    assert client.post('/tasks',json={'title':'x'*201},headers=h).status_code==422
    assert client.get('/tasks?search=' + 'x'*121,headers=h).status_code==422
    assert client.get('/tasks?completed=maybe',headers=h).status_code==422

def test_search_filter(client):
    h=auth(client)
    for name in ('Fix API', 'Review PR'):
        client.post('/tasks',json={'title':name},headers=h)
    assert len(client.get('/tasks?search=%20%20',headers=h).json())==2
    assert len(client.get('/tasks?search=fIx',headers=h).json())==1
    assert len(client.get('/tasks?completed=false',headers=h).json())==2
