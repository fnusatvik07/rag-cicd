"""Tests for FastAPI endpoints - uses TestClient (no server needed)."""

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_chat_requires_question():
    response = client.post("/chat", json={})
    assert response.status_code == 422  # validation error


def test_search_requires_query():
    response = client.post("/search", json={})
    assert response.status_code == 422
