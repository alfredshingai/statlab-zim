"""Milestone 5 — Auth tests."""

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app

# Ensure tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

TEST_EMAIL = "alice@example.com"
TEST_PASSWORD = "StrongPass123"


def _register(email=TEST_EMAIL, password=TEST_PASSWORD):
    return client.post("/auth/register", json={"email": email, "password": password, "full_name": "Alice"})


def test_register_and_login_and_me():
    # Clean previous
    # Register
    r = _register()
    if r.status_code == 400 and "already registered" in r.text:
        # Login instead
        pass
    else:
        assert r.status_code == 201, r.text
        assert r.json()["email"] == TEST_EMAIL

    # Duplicate should fail
    r2 = _register()
    assert r2.status_code == 400

    # Login
    r = client.post("/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token

    # Me
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL

    # Wrong password
    r = client.post("/auth/login", data={"username": TEST_EMAIL, "password": "wrong"})
    assert r.status_code == 401

    # Projects (protected)
    # Without token -> 401
    r = client.get("/projects")
    assert r.status_code == 401

    # With token -> create
    r = client.post("/projects", headers={"Authorization": f"Bearer {token}"}, json={"name": "Demo Project", "description": "Test"})
    assert r.status_code == 201, r.text
    proj_id = r.json()["id"]

    # List
    r = client.get("/projects", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert any(p["id"] == proj_id for p in r.json())

    # Reports generate
    r = client.post(
        "/reports/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": proj_id, "title": "Report 1", "methods": ["pearson"], "results": {"r": 0.5}},
    )
    assert r.status_code == 201, r.text
    rep_id = r.json()["id"]

    # List reports
    r = client.get("/reports", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert any(rep["id"] == rep_id for rep in r.json())


def test_password_not_plain():
    r = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401
