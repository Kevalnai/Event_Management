"""
Shared pytest fixtures for the whole backend test suite.

IMPORTANT: this file sets environment variables *before* anything under
`app/` is imported, so the app wires itself up against a dedicated test
database (`event_management_test`) instead of the real dev database, and
against dummy Stripe keys so no test can ever reach the real Stripe API
by accident. Every real-looking Stripe call in the test suite is mocked.
"""

import os

os.environ["DB_NAME"] = "event_management_test"
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy_not_real"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_dummy_not_real"
os.environ.setdefault("SECRET_KEY", "test-suite-secret-key-not-for-production")

import pytest
from starlette.testclient import TestClient

from main import app
from app.core.database import Base, engine, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Tables are created once per test session against the test database."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _clean_db():
    """
    Every test starts with every app table empty. Truncating (rather than
    re-creating tables) keeps this fast while still giving each test a
    blank slate, independent of test order.
    """
    with engine.begin() as conn:
        table_names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        conn.exec_driver_sql(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE;")
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(client):
    """Registers + logs in a fresh user, returns (user_json, auth_headers)."""

    def _make(username="alice", email=None, password="Passw0rd!"):
        email = email or f"{username}@example.com"
        resp = client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()

        login = client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers

    return _make


@pytest.fixture
def make_event(client):
    """Creates a category + event as the given user, returns the event JSON."""

    def _make(headers, price=0, currency="USD", title="Test Event", **overrides):
        cat = client.post(
            "/events/categories",
            json={"name": overrides.pop("category_name", "General")},
            headers=headers,
        )
        assert cat.status_code == 201, cat.text
        category_id = cat.json()["category_id"]

        body = {
            "title": title,
            "description": "A test event",
            "category_id": category_id,
            "start_date": "2027-01-01T18:00:00Z",
            "end_date": "2027-01-01T22:00:00Z",
            "venue": "Test Venue",
            "address": "1 Test St",
            "price": price,
            "currency": currency,
            **overrides,
        }
        resp = client.post("/events/events", json=body, headers=headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make
