"""
Payments module. Every test mocks the Stripe SDK directly - no test in
this suite ever makes a real network call to Stripe.
"""

from unittest.mock import patch, Mock

from app.modules.events.models import EventRegistration
from app.modules.payments.models import Payment, PaymentStatus


def _register(client, event, headers, suffix="1"):
    resp = client.post(
        f"/events/{event['event_id']}/register",
        json={"name": f"Attendee {suffix}", "email": f"pay{suffix}@example.com", "phone": "5550000"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


@patch("app.modules.payments.services.stripe.PaymentIntent.create")
def test_initiate_payment_creates_intent_with_server_side_amount(mock_create, client, make_user, make_event):
    mock_create.return_value = Mock(id="pi_test_1", client_secret="secret_1")

    _, owner_headers = make_user("payhost1")
    _, attendee_headers = make_user("payer1")
    event = make_event(owner_headers, price=42.50, currency="USD")
    registration = _register(client, event, attendee_headers)

    resp = client.post(
        "/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["client_secret"] == "secret_1"
    assert body["payment"]["amount"] == 42.50
    assert body["payment"]["status"] == "pending"

    # The amount Stripe was actually told about is the event's price, in cents -
    # never anything the client could have supplied.
    _, kwargs = mock_create.call_args
    assert kwargs["amount"] == 4250
    assert kwargs["currency"] == "usd"

    # Regression test: without allow_redirects="never", Stripe rejects the
    # frontend's confirmPayment() call (redirect="if_required", no return_url)
    # for any account with a redirect-capable method (e.g. Link) enabled -
    # i.e. every real card payment would fail at the final step. Verified
    # against the real Stripe test API, not just this mock.
    assert kwargs["automatic_payment_methods"] == {"enabled": True, "allow_redirects": "never"}


@patch("app.modules.payments.services.stripe.PaymentIntent.create")
def test_initiate_payment_rejects_non_owner(mock_create, client, make_user, make_event):
    mock_create.return_value = Mock(id="pi_test_2", client_secret="secret_2")

    _, owner_headers = make_user("payhost2")
    _, attendee_headers = make_user("payer2")
    _, stranger_headers = make_user("paystranger2")
    event = make_event(owner_headers, price=10)
    registration = _register(client, event, attendee_headers)

    resp = client.post(
        "/payments/", json={"registration_id": registration["registration_id"]}, headers=stranger_headers
    )
    assert resp.status_code == 403
    mock_create.assert_not_called()


def test_initiate_payment_rejects_free_event(client, make_user, make_event):
    _, owner_headers = make_user("payhost3")
    _, attendee_headers = make_user("payer3")
    event = make_event(owner_headers, price=0)
    registration = _register(client, event, attendee_headers)

    resp = client.post(
        "/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers
    )
    assert resp.status_code == 400


@patch("app.modules.payments.services.stripe.PaymentIntent.retrieve")
@patch("app.modules.payments.services.stripe.PaymentIntent.create")
def test_initiate_payment_reuses_pending_intent(mock_create, mock_retrieve, client, make_user, make_event):
    mock_create.return_value = Mock(id="pi_test_4", client_secret="secret_first")
    mock_retrieve.return_value = Mock(status="requires_payment_method", client_secret="secret_refreshed")

    _, owner_headers = make_user("payhost4")
    _, attendee_headers = make_user("payer4")
    event = make_event(owner_headers, price=15)
    registration = _register(client, event, attendee_headers)

    first = client.post(
        "/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers
    )
    second = client.post(
        "/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers
    )

    assert first.json()["client_secret"] == "secret_first"
    assert second.json()["client_secret"] == "secret_refreshed"
    assert mock_create.call_count == 1
    assert mock_retrieve.call_count == 1


@patch("app.modules.payments.routes.stripe.Webhook.construct_event")
@patch("app.modules.payments.services.stripe.PaymentIntent.create")
def test_webhook_marks_payment_and_registration_confirmed(mock_create, mock_construct, client, make_user, make_event, db):
    mock_create.return_value = Mock(id="pi_webhook_1", client_secret="secret_wh1")

    _, owner_headers = make_user("payhost5")
    _, attendee_headers = make_user("payer5")
    event = make_event(owner_headers, price=30)
    registration = _register(client, event, attendee_headers)

    client.post("/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers)

    mock_construct.return_value = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_webhook_1"}},
    }
    resp = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "fake"})
    assert resp.status_code == 200

    payment = db.query(Payment).filter(Payment.stripe_payment_intent_id == "pi_webhook_1").first()
    assert payment.status == PaymentStatus.completed

    reg = db.query(EventRegistration).filter(
        EventRegistration.registration_id == registration["registration_id"]
    ).first()
    assert reg.status.value == "confirmed"


@patch("app.modules.payments.routes.stripe.Webhook.construct_event")
@patch("app.modules.payments.services.stripe.PaymentIntent.create")
def test_webhook_marks_payment_failed(mock_create, mock_construct, client, make_user, make_event, db):
    mock_create.return_value = Mock(id="pi_webhook_2", client_secret="secret_wh2")

    _, owner_headers = make_user("payhost6")
    _, attendee_headers = make_user("payer6")
    event = make_event(owner_headers, price=30)
    registration = _register(client, event, attendee_headers)

    client.post("/payments/", json={"registration_id": registration["registration_id"]}, headers=attendee_headers)

    mock_construct.return_value = {
        "type": "payment_intent.payment_failed",
        "data": {"object": {"id": "pi_webhook_2"}},
    }
    resp = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "fake"})
    assert resp.status_code == 200

    payment = db.query(Payment).filter(Payment.stripe_payment_intent_id == "pi_webhook_2").first()
    assert payment.status == PaymentStatus.failed


def test_webhook_rejects_bad_signature(client):
    import stripe

    with patch(
        "app.modules.payments.routes.stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("bad sig", "sig_header"),
    ):
        resp = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature": "bad"})
        assert resp.status_code == 400
