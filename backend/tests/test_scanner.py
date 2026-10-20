"""Scanner module: QR check-in, RBAC-gated by the ticket's own event,
with duplicate-scan protection."""


def _issue_ticket(client, event, attendee_headers, suffix):
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": f"Scan {suffix}", "email": f"scan{suffix}@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()
    ticket = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers).json()
    return registration, ticket


def test_scan_unknown_qr_code_returns_404(client, make_user):
    _, staff_headers = make_user("scanstaff1")
    resp = client.post("/scanner/scan", json={"qr_code": "does-not-exist"}, headers=staff_headers)
    assert resp.status_code == 404


def test_scan_blocks_non_organiser(client, make_user, make_event):
    _, owner_headers = make_user("scanhost1")
    _, attendee_headers = make_user("scanattendee1")
    _, stranger_headers = make_user("scanstranger1")
    event = make_event(owner_headers, price=0)
    _, ticket = _issue_ticket(client, event, attendee_headers, "1")

    resp = client.post("/scanner/scan", json={"qr_code": ticket["qr_code"]}, headers=stranger_headers)
    assert resp.status_code == 403


def test_scan_allows_volunteer_and_records_checkin(client, make_user, make_event):
    _, owner_headers = make_user("scanhost2")
    volunteer, volunteer_headers = make_user("scanvol2")
    _, attendee_headers = make_user("scanattendee2")
    event = make_event(owner_headers, price=0)

    client.post(
        f"/events/{event['event_id']}/organisers",
        json={"user_id": volunteer["user_id"], "role": "volunteer"},
        headers=owner_headers,
    )
    _, ticket = _issue_ticket(client, event, attendee_headers, "2")

    resp = client.post(
        "/scanner/scan",
        json={"qr_code": ticket["qr_code"], "gate": "North"},
        headers=volunteer_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["gate"] == "North"


def test_scanning_same_ticket_twice_is_rejected(client, make_user, make_event):
    _, owner_headers = make_user("scanhost3")
    _, attendee_headers = make_user("scanattendee3")
    event = make_event(owner_headers, price=0)
    _, ticket = _issue_ticket(client, event, attendee_headers, "3")

    first = client.post("/scanner/scan", json={"qr_code": ticket["qr_code"]}, headers=owner_headers)
    second = client.post("/scanner/scan", json={"qr_code": ticket["qr_code"]}, headers=owner_headers)
    assert first.status_code == 201
    assert second.status_code == 409
