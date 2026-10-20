"""
Auth module: registration, login, session lifecycle, global RBAC,
and password reset.
"""

from app.modules.users.models import User


def test_register_creates_user(client):
    resp = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["role"] == "user"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_ignores_client_supplied_role(client):
    """A privilege-escalation regression test: role must never be client-settable."""
    resp = client.post(
        "/auth/register",
        json={
            "username": "wannabe-admin",
            "email": "wannabe@example.com",
            "password": "Passw0rd!",
            "role": "admin",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "user"


def test_register_rejects_duplicate_email(client, make_user):
    make_user("bob", email="bob@example.com")
    resp = client.post(
        "/auth/register",
        json={"username": "bob2", "email": "bob@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 400


def test_register_rejects_duplicate_username(client, make_user):
    make_user("carol", email="carol@example.com")
    resp = client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol2@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 400


def test_login_with_email_or_username(client, make_user):
    make_user("dave", email="dave@example.com", password="Passw0rd!")

    by_email = client.post("/auth/login", data={"username": "dave@example.com", "password": "Passw0rd!"})
    assert by_email.status_code == 200
    assert "access_token" in by_email.json()
    assert "refresh_token" in by_email.json()

    by_username = client.post("/auth/login", data={"username": "dave", "password": "Passw0rd!"})
    assert by_username.status_code == 200


def test_login_rejects_wrong_password(client, make_user):
    make_user("erin", email="erin@example.com", password="Passw0rd!")
    resp = client.post("/auth/login", data={"username": "erin", "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_rejects_unknown_user(client):
    resp = client.post("/auth/login", data={"username": "ghost", "password": "whatever"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, make_user):
    user, headers = make_user("frank")
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user["user_id"]


def test_update_profile_changes_username_and_email(client, make_user):
    _, headers = make_user("gary")
    resp = client.patch("/auth/me", json={"username": "gary2"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "gary2"


def test_update_profile_cannot_self_promote_role(client, make_user):
    """PATCH /auth/me must not accept a role field at all."""
    _, headers = make_user("hank")
    resp = client.patch("/auth/me", json={"username": "hank", "role": "admin"}, headers=headers)
    assert resp.status_code == 200
    me = client.get("/auth/me", headers=headers).json()
    assert me["role"] == "user"


def test_admin_only_route_blocks_regular_user(client, make_user):
    _, headers = make_user("ivan")
    resp = client.get("/auth/admin-only", headers=headers)
    assert resp.status_code == 403


def test_admin_can_promote_another_user(client, make_user, db):
    admin_user, admin_headers = make_user("root-admin")
    target_user, target_headers = make_user("target")

    # There is no self-service path to admin by design - the first admin
    # is promoted directly in the database, exactly as a real operator would.
    row = db.query(User).filter(User.user_id == admin_user["user_id"]).first()
    row.role = "admin"
    db.commit()

    resp = client.patch(
        f"/auth/users/{target_user['user_id']}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"

    # The promoted user can now reach the admin-only route too.
    admin_only = client.get("/auth/admin-only", headers=target_headers)
    assert admin_only.status_code == 200


def test_non_admin_cannot_promote_users(client, make_user):
    _, headers = make_user("jill")
    _, other_headers = make_user("kyle")
    other = client.get("/auth/me", headers=other_headers).json()

    resp = client.patch(f"/auth/users/{other['user_id']}/role", json={"role": "admin"}, headers=headers)
    assert resp.status_code == 403


def test_refresh_token_issues_new_access_token(client, make_user):
    make_user("liam", password="Passw0rd!")
    login = client.post("/auth/login", data={"username": "liam", "password": "Passw0rd!"})
    refresh_token = login.json()["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_logout_revokes_refresh_token(client, make_user):
    make_user("mia", password="Passw0rd!")
    login = client.post("/auth/login", data={"username": "mia", "password": "Passw0rd!"})
    refresh_token = login.json()["refresh_token"]

    logout = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


def test_password_reset_full_flow(client, make_user):
    make_user("nora", email="nora@example.com", password="OldPassw0rd!")

    req = client.post("/auth/password-reset/request", json={"email": "nora@example.com"})
    assert req.status_code == 200
    reset_token = req.json()["reset_token"]

    confirm = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": reset_token, "new_password": "NewPassw0rd!"},
    )
    assert confirm.status_code == 200

    old_login = client.post("/auth/login", data={"username": "nora", "password": "OldPassw0rd!"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", data={"username": "nora", "password": "NewPassw0rd!"})
    assert new_login.status_code == 200


def test_password_reset_rejects_bad_token(client):
    resp = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": "not-a-real-token", "new_password": "whatever1"},
    )
    assert resp.status_code == 400
