"""
Events module: categories, event CRUD, per-event RBAC (organisers),
sessions, registrations, and manual check-ins.
"""

from unittest.mock import patch

from starlette.testclient import TestClient

from main import app


def test_duplicate_event_title_is_a_clean_400(client, make_user):
    _, headers = make_user("duphost1")
    cat = client.post("/events/categories", json={"name": "DupCat"}, headers=headers).json()
    body = {
        "title": "Only One Of Me",
        "category_id": cat["category_id"],
        "start_date": "2027-01-01T18:00:00Z",
        "end_date": "2027-01-01T22:00:00Z",
        "venue": "V",
        "address": "A",
        "price": 0,
        "currency": "USD",
    }
    first = client.post("/events/events", json=body, headers=headers)
    assert first.status_code == 201

    second = client.post("/events/events", json=body, headers=headers)
    assert second.status_code == 400
    assert "already exists" in second.json()["detail"]


def test_unexpected_server_error_returns_safe_json_not_a_raw_crash(client, make_user):
    """
    Regression test for a real bug found while testing live: an unhandled
    exception bypassed CORSMiddleware entirely (Starlette's ServerError-
    Middleware sits outside it), so the browser saw a bare network/CORS
    failure instead of a real error, and a raw traceback could leak to the
    client. The global exception handler in main.py fixes this - verify it
    actually catches something unexpected and returns a safe response.
    """
    _, headers = make_user("crashhost1")
    cat = client.post("/events/categories", json={"name": "CrashCat"}, headers=headers).json()

    # TestClient re-raises unhandled exceptions into the test by default
    # (for debugging convenience) - raise_server_exceptions=False is the
    # documented way to instead observe the actual HTTP response, which is
    # what a real deployed server's caller always sees either way.
    with patch(
        "app.modules.events.services.EventRepository.create",
        side_effect=RuntimeError("something nobody anticipated"),
    ), TestClient(app, raise_server_exceptions=False) as crash_client:
        resp = crash_client.post(
            "/events/events",
            json={
                "title": "Crash Test Event",
                "category_id": cat["category_id"],
                "start_date": "2027-01-01T18:00:00Z",
                "end_date": "2027-01-01T22:00:00Z",
                "venue": "V",
                "address": "A",
                "price": 0,
                "currency": "USD",
            },
            headers=headers,
        )

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
    assert "something nobody anticipated" not in resp.text


def test_create_and_list_categories(client, make_user):
    _, headers = make_user("host1")
    created = client.post("/events/categories", json={"name": "Music"}, headers=headers)
    assert created.status_code == 201

    listing = client.get("/events/categories")
    assert listing.status_code == 200
    assert any(c["name"] == "Music" for c in listing.json())


def test_create_category_is_idempotent_by_name(client, make_user):
    _, headers = make_user("host2")
    first = client.post("/events/categories", json={"name": "Workshops"}, headers=headers)
    second = client.post("/events/categories", json={"name": "Workshops"}, headers=headers)
    assert first.json()["category_id"] == second.json()["category_id"]


def test_create_event_requires_auth(client):
    resp = client.post("/events/events", json={"title": "x"})
    assert resp.status_code == 401


def test_get_nonexistent_event_returns_404(client):
    resp = client.get("/events/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_register_for_nonexistent_event_returns_404(client, make_user):
    _, headers = make_user("ghost-registrant")
    resp = client.post(
        "/events/00000000-0000-0000-0000-000000000000/register",
        json={"name": "A", "email": "a@example.com", "phone": "555"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_create_event_rejects_non_url_banner(client, make_user):
    _, headers = make_user("bannerhost1")
    cat = client.post("/events/categories", json={"name": "BannerCat1"}, headers=headers).json()

    resp = client.post(
        "/events/events",
        json={
            "title": "Bad Banner Event",
            "category_id": cat["category_id"],
            "start_date": "2027-01-01T18:00:00Z",
            "end_date": "2027-01-01T22:00:00Z",
            "venue": "V",
            "address": "A",
            "price": 0,
            "currency": "USD",
            "banner_url": "string",  # not a real URL - the exact bad value seen in real data
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_event_rejects_negative_price(client, make_user):
    _, headers = make_user("bannerhost2")
    cat = client.post("/events/categories", json={"name": "BannerCat2"}, headers=headers).json()

    resp = client.post(
        "/events/events",
        json={
            "title": "Negative Price Event",
            "category_id": cat["category_id"],
            "start_date": "2027-01-01T18:00:00Z",
            "end_date": "2027-01-01T22:00:00Z",
            "venue": "V",
            "address": "A",
            "price": -10,
            "currency": "USD",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_list_events_respects_limit_and_offset(client, make_user, make_event):
    _, headers = make_user("pagehost1")
    for i in range(3):
        make_event(headers, title=f"Page Event {i}")

    first_page = client.get("/events/?limit=2&offset=0").json()
    second_page = client.get("/events/?limit=2&offset=2").json()

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {e["event_id"] for e in first_page}.isdisjoint({e["event_id"] for e in second_page})


def test_list_events_rejects_oversized_limit(client):
    resp = client.get("/events/?limit=1000")
    assert resp.status_code == 422


def test_list_and_get_event_are_public(client, make_user, make_event):
    _, headers = make_user("host3")
    event = make_event(headers, title="Public Event")

    listing = client.get("/events/")
    assert listing.status_code == 200
    assert any(e["event_id"] == event["event_id"] for e in listing.json())

    detail = client.get(f"/events/{event['event_id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Public Event"


def test_event_detail_never_leaks_registrations_or_organisers(client, make_user, make_event):
    """Regression test: public event detail must not expose attendee PII
    or organiser role assignments (both are only available via the
    RBAC-gated endpoints)."""
    _, headers = make_user("host4")
    event = make_event(headers)

    client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Some Attendee", "email": "attendee@example.com", "phone": "5550000"},
        headers=headers,
    )

    detail = client.get(f"/events/{event['event_id']}").json()
    assert "registrations" not in detail
    assert "organisers" not in detail


def test_creator_is_auto_assigned_as_admin_organiser(client, make_user, make_event):
    _, headers = make_user("host5")
    event = make_event(headers)

    organisers = client.get(f"/events/{event['event_id']}/organisers", headers=headers)
    assert organisers.status_code == 200
    roles = {o["role"] for o in organisers.json()}
    assert "admin" in roles


def test_delete_event_requires_admin_organiser(client, make_user, make_event):
    _, owner_headers = make_user("host6")
    _, stranger_headers = make_user("stranger1")
    event = make_event(owner_headers)

    denied = client.delete(f"/events/events/{event['event_id']}", headers=stranger_headers)
    assert denied.status_code == 403

    allowed = client.delete(f"/events/events/{event['event_id']}", headers=owner_headers)
    assert allowed.status_code == 204

    assert client.get(f"/events/{event['event_id']}").status_code == 404


def test_add_organiser_requires_existing_admin(client, make_user, make_event):
    _, owner_headers = make_user("host7")
    staff_user, staff_headers = make_user("staffer1")
    _, outsider_headers = make_user("outsider1")
    event = make_event(owner_headers)

    denied = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": staff_user["user_id"], "role": "staff"},
        headers=outsider_headers,
    )
    assert denied.status_code == 403

    granted = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": staff_user["user_id"], "role": "staff"},
        headers=owner_headers,
    )
    assert granted.status_code == 201
    assert granted.json()["role"] == "staff"

    # staff can now see the organiser list (admin-or-staff gated)...
    listing = client.get(f"/events/{event['event_id']}/organisers", headers=staff_headers)
    assert listing.status_code == 200

    # ...but cannot grant roles to others, since that's admin-only.
    escalation_attempt = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": staff_user["user_id"], "role": "admin"},
        headers=staff_headers,
    )
    assert escalation_attempt.status_code == 403


def test_granting_organiser_role_twice_upserts_not_duplicates(client, make_user, make_event):
    _, owner_headers = make_user("host8")
    volunteer, _ = make_user("vol1")
    event = make_event(owner_headers)

    client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "volunteer"},
        headers=owner_headers,
    )
    second = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "staff"},
        headers=owner_headers,
    )
    assert second.status_code == 201

    listing = client.get(f"/events/{event['event_id']}/organisers", headers=owner_headers).json()
    rows = [o for o in listing if o["user_id"] == volunteer["user_id"]]
    assert len(rows) == 1
    assert rows[0]["role"] == "staff"


def test_create_session_allowed_for_staff_not_volunteer(client, make_user, make_event):
    _, owner_headers = make_user("host9")
    staff, staff_headers = make_user("staffer2")
    volunteer, volunteer_headers = make_user("vol2")
    event = make_event(owner_headers)

    client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": staff["user_id"], "role": "staff"},
        headers=owner_headers,
    )
    client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "volunteer"},
        headers=owner_headers,
    )

    session_body = {
        "title": "Opening Keynote",
        "speaker": "Jane Doe",
        "start_time": "2027-01-01T18:00:00Z",
        "end_time": "2027-01-01T18:30:00Z",
    }

    as_staff = client.post(
        f"/events/events/{event['event_id']}/sessions", json=session_body, headers=staff_headers
    )
    assert as_staff.status_code == 201

    as_volunteer = client.post(
        f"/events/events/{event['event_id']}/sessions", json=session_body, headers=volunteer_headers
    )
    assert as_volunteer.status_code == 403


def test_register_for_free_event_confirms_instantly(client, make_user, make_event):
    _, owner_headers = make_user("host10")
    attendee, attendee_headers = make_user("attendee1")
    event = make_event(owner_headers, price=0)

    resp = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee One", "email": "a1@example.com", "phone": "5551111"},
        headers=attendee_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["user_id"] == attendee["user_id"]


def test_register_for_paid_event_stays_pending(client, make_user, make_event):
    _, owner_headers = make_user("host11")
    _, attendee_headers = make_user("attendee2")
    event = make_event(owner_headers, price=25)

    resp = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Two", "email": "a2@example.com", "phone": "5552222"},
        headers=attendee_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_register_uses_jwt_identity_not_request_body(client, make_user, make_event):
    """A client cannot register a booking on behalf of another user_id."""
    _, owner_headers = make_user("host12")
    attacker, attacker_headers = make_user("attacker1")
    victim, _ = make_user("victim1")
    event = make_event(owner_headers)

    resp = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attacker", "email": "attack@example.com", "phone": "5553333", "user_id": victim["user_id"]},
        headers=attacker_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] == attacker["user_id"]


def test_my_registrations_lists_own_bookings_with_event_nested(client, make_user, make_event):
    _, owner_headers = make_user("host13")
    _, attendee_headers = make_user("attendee3")
    event = make_event(owner_headers, title="Nested Event Test")

    client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Three", "email": "a3@example.com", "phone": "5554444"},
        headers=attendee_headers,
    )

    mine = client.get("/events/me/registrations", headers=attendee_headers)
    assert mine.status_code == 200
    rows = mine.json()
    assert len(rows) == 1
    assert rows[0]["event"]["title"] == "Nested Event Test"
    assert rows[0]["ticket"] is None


def test_list_event_registrations_is_organiser_only(client, make_user, make_event):
    _, owner_headers = make_user("host14")
    _, attendee_headers = make_user("attendee4")
    _, stranger_headers = make_user("stranger2")
    event = make_event(owner_headers)

    client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Four", "email": "a4@example.com", "phone": "5555555"},
        headers=attendee_headers,
    )

    denied = client.get(f"/events/{event['event_id']}/registrations", headers=stranger_headers)
    assert denied.status_code == 403

    allowed = client.get(f"/events/{event['event_id']}/registrations", headers=owner_headers)
    assert allowed.status_code == 200
    assert len(allowed.json()) == 1


def test_manual_checkin_allows_volunteer_blocks_outsider(client, make_user, make_event):
    _, owner_headers = make_user("host15")
    volunteer, volunteer_headers = make_user("vol3")
    _, attendee_headers = make_user("attendee5")
    _, stranger_headers = make_user("stranger3")
    event = make_event(owner_headers)

    client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "volunteer"},
        headers=owner_headers,
    )
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Five", "email": "a5@example.com", "phone": "5556666"},
        headers=attendee_headers,
    ).json()

    denied = client.post(
        f"/events/events/{event['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=stranger_headers,
    )
    assert denied.status_code == 403

    allowed = client.post(
        f"/events/events/{event['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=volunteer_headers,
    )
    assert allowed.status_code == 201
    assert allowed.json()["gate"] == "Main"


def test_manual_checkin_rejects_duplicate(client, make_user, make_event):
    _, owner_headers = make_user("host16")
    _, attendee_headers = make_user("attendee6")
    event = make_event(owner_headers)

    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Six", "email": "a6@example.com", "phone": "5557777"},
        headers=attendee_headers,
    ).json()

    first = client.post(
        f"/events/events/{event['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=owner_headers,
    )
    assert first.status_code == 201

    second = client.post(
        f"/events/events/{event['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=owner_headers,
    )
    assert second.status_code == 409


def test_manual_checkin_rejects_unconfirmed_registration(client, make_user, make_event):
    _, owner_headers = make_user("host17")
    _, attendee_headers = make_user("attendee7")
    event = make_event(owner_headers, price=20)

    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Attendee Seven", "email": "a7@example.com", "phone": "5558888"},
        headers=attendee_headers,
    ).json()
    assert registration["status"] == "pending"

    denied = client.post(
        f"/events/events/{event['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=owner_headers,
    )
    assert denied.status_code == 400


def test_manual_checkin_rejects_registration_from_a_different_event(client, make_user, make_event):
    _, owner_headers = make_user("host18")
    _, attendee_headers = make_user("attendee8")
    event_a = make_event(owner_headers, title="Event A")
    event_b = make_event(owner_headers, title="Event B")

    registration = client.post(
        f"/events/{event_a['event_id']}/register",
        json={"name": "Attendee Eight", "email": "a8@example.com", "phone": "5559999"},
        headers=attendee_headers,
    ).json()

    # Same admin, but tries to check this event-A registration in under event B.
    cross_event = client.post(
        f"/events/events/{event_b['event_id']}/checkins/{registration['registration_id']}",
        json={"gate": "Main"},
        headers=owner_headers,
    )
    assert cross_event.status_code == 404


def test_my_role_reflects_actual_organiser_status(client, make_user, make_event):
    owner, owner_headers = make_user("host19")
    _, outsider_headers = make_user("outsider2")
    event = make_event(owner_headers)

    mine = client.get(f"/events/{event['event_id']}/my-role", headers=owner_headers)
    assert mine.status_code == 200
    assert mine.json()["role"] == "admin"

    not_organiser = client.get(f"/events/{event['event_id']}/my-role", headers=outsider_headers)
    assert not_organiser.status_code == 200
    assert not_organiser.json()["role"] is None


def test_add_organiser_by_email(client, make_user, make_event):
    _, owner_headers = make_user("host20")
    staff_user, staff_headers = make_user("staffer3", email="staffer3@example.com")
    event = make_event(owner_headers)

    granted = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"email": "staffer3@example.com", "role": "staff"},
        headers=owner_headers,
    )
    assert granted.status_code == 201
    assert granted.json()["user_id"] == staff_user["user_id"]

    mine = client.get(f"/events/{event['event_id']}/my-role", headers=staff_headers)
    assert mine.json()["role"] == "staff"


def test_add_organiser_by_unknown_email_returns_404(client, make_user, make_event):
    _, owner_headers = make_user("host21")
    event = make_event(owner_headers)

    denied = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"email": "nobody-like-this-exists@example.com", "role": "staff"},
        headers=owner_headers,
    )
    assert denied.status_code == 404


def test_my_organised_events_lists_every_event_i_organise(client, make_user, make_event):
    host, host_headers = make_user("host23")
    volunteer, volunteer_headers = make_user("vol4")
    _, outsider_headers = make_user("outsider3")

    event_a = make_event(host_headers, title="Organised Event A")
    event_b = make_event(host_headers, title="Organised Event B")
    client.post(
        f"/events/{event_b['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "volunteer"},
        headers=host_headers,
    )

    host_list = client.get("/events/me/organised", headers=host_headers).json()
    assert {e["event"]["event_id"] for e in host_list} == {event_a["event_id"], event_b["event_id"]}
    assert all(e["role"] == "admin" for e in host_list)

    volunteer_list = client.get("/events/me/organised", headers=volunteer_headers).json()
    assert len(volunteer_list) == 1
    assert volunteer_list[0]["event"]["event_id"] == event_b["event_id"]
    assert volunteer_list[0]["role"] == "volunteer"

    outsider_list = client.get("/events/me/organised", headers=outsider_headers).json()
    assert outsider_list == []


def test_add_organiser_requires_user_id_or_email(client, make_user, make_event):
    _, owner_headers = make_user("host22")
    event = make_event(owner_headers)

    denied = client.post(
        f"/events/{event['event_id']}/organisers",
        json={"role": "staff"},
        headers=owner_headers,
    )
    assert denied.status_code == 422
