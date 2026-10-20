"""
Rate limiting is disabled globally for the rest of the suite (every
request from TestClient shares one "IP", which would make every other
test flaky). This file turns it on just for itself, against the same
shared limiter singleton every route already uses, and turns it back off
afterward so it can't bleed into other tests.
"""

import pytest

from app.core.limiter import limiter


@pytest.fixture
def rate_limiting_enabled():
    limiter.enabled = True
    try:
        yield
    finally:
        limiter.enabled = False


def test_register_is_rate_limited(client, rate_limiting_enabled):
    # The route is limited to 5/minute; the 6th call in a burst should 429.
    responses = []
    for i in range(6):
        resp = client.post(
            "/auth/register",
            json={"username": f"burst{i}", "email": f"burst{i}@example.com", "password": "Passw0rd!"},
        )
        responses.append(resp.status_code)

    assert responses[:5] == [200] * 5
    assert responses[5] == 429


def test_password_reset_request_is_rate_limited(client, rate_limiting_enabled):
    # The route is limited to 3/minute; the 4th call should 429.
    responses = [
        client.post("/auth/password-reset/request", json={"email": "nobody@example.com"}).status_code
        for _ in range(4)
    ]
    assert responses[:3] == [200, 200, 200]
    assert responses[3] == 429
