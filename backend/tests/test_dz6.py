import pytest
from fastapi.testclient import TestClient
from app.main import app, Base, engine

@pytest.fixture(autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

def test_readiness_database():
    with TestClient(app) as client:
        r=client.get('/health/ready')
        assert r.status_code==200
        assert r.json()['database']=='ok'

def test_invalid_oauth_ticket():
    with TestClient(app) as client:
        r=client.post('/auth/google/exchange',json={'ticket':'x'*40})
        assert r.status_code==401

def test_disabled_google_login(monkeypatch):
    import app.main as mod
    monkeypatch.setattr(mod,'GOOGLE_ID','')
    with TestClient(app) as client:
        assert client.get('/auth/google/login').status_code==503
