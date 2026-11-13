"""
Race-condition tests: fire many identical requests at the same instant and
check the database still only accepts one.

These call the service layer directly from real threads, each with its own
database session (so its own Postgres connection and transaction), and a
barrier makes every thread start at the same moment. That reproduces two
door scanners, or a double-clicked "Register" button, hitting the server
together - something the sequential TestClient tests can't do.
"""

import threading
from uuid import UUID

from fastapi import HTTPException

from app.core.database import SessionLocal
from app.modules.events.models import CheckIn, EventRegistration
from app.modules.events.schema import EventRegistrationCreate
from app.modules.events.services import EventService
from app.modules.scanners.services import ScannerService

THREADS = 20


def _race(fn):
    """Run fn(session) in THREADS threads at once; return their outcomes."""
    barrier = threading.Barrier(THREADS)
    outcomes = []
    lock = threading.Lock()

    def worker():
        session = SessionLocal()
        try:
            barrier.wait()
            fn(session)
            result = "ok"
        except HTTPException as exc:
            result = exc.status_code
        except Exception as exc:  # anything else is a bug (e.g. a raw IntegrityError -> 500)
            result = f"error: {type(exc).__name__}"
        finally:
            session.close()
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return outcomes


def test_concurrent_scans_of_one_ticket_check_in_exactly_once(client, make_user, make_event, db):
    owner, owner_headers = make_user("racehost")
    _, attendee_headers = make_user("raceattendee")
    event = make_event(owner_headers, price=0)
    registration = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": "Race", "email": "race@example.com", "phone": "555"},
        headers=attendee_headers,
    ).json()
    ticket = client.post(f"/tickets/{registration['registration_id']}", headers=attendee_headers).json()

    outcomes = _race(
        lambda session: ScannerService.scan_qr(
            db=session, qr_code=ticket["qr_code"], user_id=UUID(owner["user_id"])
        )
    )

    assert outcomes.count("ok") == 1, outcomes
    assert outcomes.count(409) == THREADS - 1, outcomes
    checkins = db.query(CheckIn).filter(
        CheckIn.registration_id == UUID(registration["registration_id"])
    ).count()
    assert checkins == 1


def test_concurrent_registrations_create_one_registration(client, make_user, make_event, db):
    _, owner_headers = make_user("regracehost")
    attendee, _ = make_user("regraceattendee")
    event = make_event(owner_headers, price=25)
    payload = EventRegistrationCreate(name="Race", email="race@example.com", phone="555")

    outcomes = _race(
        lambda session: EventService.register_user(
            db=session,
            event_id=UUID(event["event_id"]),
            user_id=UUID(attendee["user_id"]),
            payload=payload,
        )
    )

    # A paid event's pending registration is returned again (so the user can
    # resume checkout), never duplicated and never a 500.
    assert all(o == "ok" for o in outcomes), outcomes
    registrations = db.query(EventRegistration).filter(
        EventRegistration.event_id == UUID(event["event_id"]),
        EventRegistration.user_id == UUID(attendee["user_id"]),
    ).count()
    assert registrations == 1


def test_concurrent_registrations_for_free_event_confirm_once(client, make_user, make_event, db):
    _, owner_headers = make_user("freeracehost")
    attendee, _ = make_user("freeraceattendee")
    event = make_event(owner_headers, price=0)
    payload = EventRegistrationCreate(name="Race", email="race@example.com", phone="555")

    outcomes = _race(
        lambda session: EventService.register_user(
            db=session,
            event_id=UUID(event["event_id"]),
            user_id=UUID(attendee["user_id"]),
            payload=payload,
        )
    )

    assert outcomes.count("ok") == 1, outcomes
    assert outcomes.count(409) == THREADS - 1, outcomes
