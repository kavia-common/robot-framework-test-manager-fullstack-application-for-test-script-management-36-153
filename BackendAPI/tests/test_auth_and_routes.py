import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.api.database import Base, engine, SessionLocal
from src.api.models import User
from src.api.auth import get_password_hash

client = TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    # Ensure tables exist and create a default admin user
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=get_password_hash("admin"), role="admin"))
            db.commit()
    finally:
        db.close()


def test_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Healthy"


def test_login_and_me():
    r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["username"] == "admin"
    assert data["roles"][0] == "admin"


def test_testscript_crud():
    # login
    r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # create
    r = client.post("/tests", json={"name": "Script A", "description": "desc"}, headers=h)
    assert r.status_code == 201
    ts_id = r.json()["data"]["id"]

    # get
    r = client.get(f"/tests/{ts_id}", headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "Script A"

    # list
    r = client.get("/tests", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    # update
    r = client.put(f"/tests/{ts_id}", json={"name": "Script A2", "description": "d2"}, headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "Script A2"

    # delete
    r = client.delete(f"/tests/{ts_id}", headers=h)
    assert r.status_code == 204


def test_queue_and_execute_flow():
    # login
    r = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # create script
    r = client.post("/tests", json={"name": "Script Q", "description": ""}, headers=h)
    ts_id = r.json()["data"]["id"]
    # create case
    r = client.post("/cases", json={"test_script_id": ts_id, "name": "Case1"}, headers=h)
    case_id = r.json()["data"]["id"]

    # queue it
    r = client.post("/queue", json={"case_ids": [case_id]}, headers=h)
    assert r.status_code == 201

    # list queue
    r = client.get("/queue", headers=h)
    assert r.status_code == 200
    assert any(i["case_id"] == case_id for i in r.json())

    # Wait for worker to process
    time.sleep(1.0)

    # Check history
    r = client.get("/history", headers=h)
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(it["case_id"] == case_id for it in items)
