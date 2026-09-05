"""Backend tests — Milestone 1 health checks."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings

client = TestClient(app)


def test_health_root():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "service" in data
    assert data["service"] == get_settings().PROJECT_NAME


def test_health_versioned():
    settings = get_settings()
    r = client.get(f"{settings.API_V1_STR}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ping():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json()["message"] == "pong"
    r2 = client.get("/api/v1/ping")
    assert r2.status_code == 200


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()
    assert r.json()["health"] == "/health"


def test_docs_available():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == get_settings().PROJECT_NAME


def test_404_handler():
    r = client.get("/nonexistent")
    assert r.status_code == 404
    body = r.json()
    assert body["error"] == "http_error"
    assert body["status_code"] == 404


def test_cors_and_process_time_headers():
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert "X-Process-Time" in r.headers
