from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_shorten_url():
    r = client.post("/shorten", json={"url": "https://google.com"})
    assert r.status_code == 200
    assert "short_code" in r.json()

def test_redirect():
    r = client.post("/shorten", json={"url": "https://example.com"})
    code = r.json()["short_code"]
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 307

def test_stats():
    r = client.post("/shorten", json={"url": "https://github.com"})
    code = r.json()["short_code"]
    r2 = client.get(f"/stats/{code}")
    assert r2.status_code == 200
    assert r2.json()["clicks"] == 0

def test_not_found():
    r = client.get("/nonexistent")
    assert r.status_code == 404