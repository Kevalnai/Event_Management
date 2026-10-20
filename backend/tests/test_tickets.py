"""Tickets module: issuance requires a confirmed registration, is
ownership-checked, and is idempotent."""


def test_cannot_issue_ticket_for_pending_registration(client, make_user, make_event):
    _, owner_headers = make_user("tickhost1")
    _, attendee_headers = make_user("ticker1")
    event = make_event(owner_headers, price=20)  # paid -> stays pending
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "A", "email": "t1@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()

    resp = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers)
    assert resp.status_code == 400


def test_issue_ticket_for_confirmed_registration(client, make_user, make_event):
    _, owner_headers = make_user("tickhost2")
    _, attendee_headers = make_user("ticker2")
    event = make_event(owner_headers, price=0)  # free -> auto-confirmed
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "B", "email": "t2@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()

    resp = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["registration_id"] == registration["registration_id"]
    assert body["qr_code"]


def test_issuing_ticket_twice_is_idempotent(client, make_user, make_event):
    _, owner_headers = make_user("tickhost3")
    _, attendee_headers = make_user("ticker3")
    event = make_event(owner_headers, price=0)
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "C", "email": "t3@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()

    first = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers)
    second = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers)
    assert first.json()["ticket_id"] == second.json()["ticket_id"]


def test_cannot_issue_ticket_for_someone_elses_registration(client, make_user, make_event):
    _, owner_headers = make_user("tickhost4")
    _, attendee_headers = make_user("ticker4")
    _, stranger_headers = make_user("tickstranger4")
    event = make_event(owner_headers, price=0)
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "D", "email": "t4@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()

    resp = client.post(f"/tickets/{registration['registration_id']}", headers=stranger_headers)
    assert resp.status_code == 403
