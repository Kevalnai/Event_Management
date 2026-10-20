# Ripple — Test Report

**Run date:** 2026-10-20
**Environment:** Python 3.14.6 · FastAPI 0.122.0 · pytest 9.1.1 · Node v24.18.0 · Vitest 5.0.5
**Database under test:** a dedicated `event_management_test` Postgres database (never the dev/prod database)
**Stripe:** every test mocks the Stripe SDK directly — no test in this suite makes a real network call to Stripe

## Summary

| Suite | Framework | Tests | Passed | Failed | Statement coverage |
|---|---|---|---|---|---|
| Backend (`backend/tests/`) | pytest + Starlette `TestClient` | 51 | 51 | 0 | 94% |
| Frontend (`frontend/src/**/*.test.jsx`) | Vitest + React Testing Library | 42 | 42 | 0 | 27% (see note below) |
| **Total** | | **93** | **93** | **0** | |

Full raw output: [`backend-results.txt`](./backend-results.txt), [`frontend-results.txt`](./frontend-results.txt), and a browsable HTML report at [`backend-report.html`](./backend-report.html).

**Frontend coverage note:** 27% is a true but incomplete picture — it reflects that this first pass tests every pure utility (`lib/format.js`, `lib/cover.js`, `lib/isUrl.js`), the two most reused UI primitives (`Button`, `EventCard`), `AuthContext` end-to-end, and the two auth pages (`Login`, `Register`). It does **not** yet cover the heavier pages (`Home`, `Events`, `EventDetail`, `Dashboard`, `CreateEvent`, `Checkout`, `Navbar`) — those need Stripe Elements, router, and multi-endpoint API mocking to test properly and are listed under Follow-ups.

## A bug this test suite found

Writing `test_delete_event_requires_admin_organiser` immediately failed with a Postgres `IntegrityError`. Deleting an event now always has at least one `event_organisers` row (the creator, auto-assigned as admin per this session's earlier RBAC fix), and the `Event.organisers`/`.sessions`/`.registrations` relationships had no delete behavior configured at the ORM level, so SQLAlchemy tried to null out each child's `event_id` first — which is a `NOT NULL` column. Fixed in `app/modules/events/models.py` by adding `passive_deletes=True` to all three relationships, which defers to the `ON DELETE CASCADE` already declared on their foreign keys instead of the ORM trying to manage it in Python. This is exactly the kind of bug a real test suite exists to catch before a user does.

## How to reproduce

```bash
# Backend
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm install
npm run test            # or: npm run test:coverage
```

The backend suite creates its own tables in `event_management_test` on first run and truncates every table before each test, so it's safe to re-run repeatedly and never touches your dev database.

---

## Backend test cases (51)

### `tests/test_auth.py` — registration, login, sessions, global RBAC, password reset (18)

| Test | Verifies |
|---|---|
| `test_register_creates_user` | Registration succeeds and never returns the password/hash |
| `test_register_ignores_client_supplied_role` | A client cannot self-assign `role: admin` at signup (regression test) |
| `test_register_rejects_duplicate_email` | 400 on duplicate email |
| `test_register_rejects_duplicate_username` | 400 on duplicate username |
| `test_login_with_email_or_username` | Login accepts either identifier |
| `test_login_rejects_wrong_password` | 401 on wrong password |
| `test_login_rejects_unknown_user` | 401 on unknown identifier |
| `test_me_requires_auth` | `GET /auth/me` is 401 with no token |
| `test_me_returns_current_user` | `GET /auth/me` returns the right user |
| `test_update_profile_changes_username_and_email` | `PATCH /auth/me` updates allowed fields |
| `test_update_profile_cannot_self_promote_role` | `PATCH /auth/me` has no `role` field to exploit (regression test) |
| `test_admin_only_route_blocks_regular_user` | 403 for a non-admin on an admin-gated route |
| `test_admin_can_promote_another_user` | An admin can grant another user `role: admin`, and that takes effect immediately |
| `test_non_admin_cannot_promote_users` | 403 if a non-admin tries to change someone's role |
| `test_refresh_token_issues_new_access_token` | Refresh flow issues a usable new access token |
| `test_logout_revokes_refresh_token` | A revoked refresh token is rejected afterward |
| `test_password_reset_full_flow` | Request → confirm → old password stops working, new one logs in |
| `test_password_reset_rejects_bad_token` | 400 on a garbage reset token |

### `tests/test_events.py` — categories, event CRUD, per-event RBAC, sessions, registrations, check-ins (23)

| Test | Verifies |
|---|---|
| `test_create_and_list_categories` | Category creation + public listing |
| `test_create_category_is_idempotent_by_name` | Creating the same category name twice returns the same row |
| `test_create_event_requires_auth` | 401 without a token |
| `test_get_nonexistent_event_returns_404` | 404 for a made-up event id |
| `test_register_for_nonexistent_event_returns_404` | 404 registering against a made-up event id |
| `test_list_and_get_event_are_public` | Both endpoints work with no auth |
| `test_event_detail_never_leaks_registrations_or_organisers` | Public event detail excludes attendee PII and role assignments (security regression test) |
| `test_creator_is_auto_assigned_as_admin_organiser` | Creating an event grants the creator `admin` on it automatically |
| `test_delete_event_requires_admin_organiser` | 403 for a non-organiser, 204 for the admin, then 404 after |
| `test_add_organiser_requires_existing_admin` | Only an admin organiser can grant roles; staff can view but not grant (escalation blocked) |
| `test_granting_organiser_role_twice_upserts_not_duplicates` | Re-granting a role updates the existing row instead of duplicating it |
| `test_create_session_allowed_for_staff_not_volunteer` | Staff can add a session; a volunteer gets 403 |
| `test_register_for_free_event_confirms_instantly` | Free events skip payment and confirm immediately |
| `test_register_for_paid_event_stays_pending` | Paid events stay `pending` until payment completes |
| `test_register_uses_jwt_identity_not_request_body` | A client cannot register on behalf of another `user_id` (regression test) |
| `test_my_registrations_lists_own_bookings_with_event_nested` | `/events/me/registrations` nests the event and a null ticket correctly |
| `test_list_event_registrations_is_organiser_only` | 403 for a stranger, 200 with the right list for the organiser |
| `test_manual_checkin_allows_volunteer_blocks_outsider` | Volunteers can check attendees in; outsiders can't |

### `tests/test_payments.py` — Stripe PaymentIntents and webhook (7)

| Test | Verifies |
|---|---|
| `test_initiate_payment_creates_intent_with_server_side_amount` | The amount Stripe is told about comes from `event.price`, in cents — never the client |
| `test_initiate_payment_rejects_non_owner` | 403 if you try to pay for someone else's registration; Stripe is never called |
| `test_initiate_payment_rejects_free_event` | 400 — nothing to pay for a free event |
| `test_initiate_payment_reuses_pending_intent` | A second call reuses the existing PaymentIntent (`retrieve`) instead of creating a duplicate |
| `test_webhook_marks_payment_and_registration_confirmed` | `payment_intent.succeeded` flips both the payment and the registration to confirmed |
| `test_webhook_marks_payment_failed` | `payment_intent.payment_failed` marks the payment failed |
| `test_webhook_rejects_bad_signature` | An invalid Stripe signature is rejected with 400 |

### `tests/test_tickets.py` — ticket issuance (4)

| Test | Verifies |
|---|---|
| `test_cannot_issue_ticket_for_pending_registration` | 400 — no ticket before payment is confirmed |
| `test_issue_ticket_for_confirmed_registration` | A confirmed registration gets a ticket with a QR code |
| `test_issuing_ticket_twice_is_idempotent` | Calling it twice returns the same ticket, not a duplicate |
| `test_cannot_issue_ticket_for_someone_elses_registration` | 403 — ownership is enforced |

### `tests/test_scanner.py` — QR check-in (4)

| Test | Verifies |
|---|---|
| `test_scan_unknown_qr_code_returns_404` | An unrecognized QR code is rejected |
| `test_scan_blocks_non_organiser` | 403 for someone with no role on the ticket's event |
| `test_scan_allows_volunteer_and_records_checkin` | A volunteer can scan and the check-in is recorded (gate included) |
| `test_scanning_same_ticket_twice_is_rejected` | Second scan of the same ticket is 409, not a duplicate check-in |

---

## Frontend test cases (42)

### `src/lib/format.test.js` (13) — date/time/price/initials formatting, including empty-input and invalid-currency fallbacks

### `src/lib/isUrl.test.js` (4) — `isImageUrl` accepts only real `http(s)` URLs; rejects garbage strings like the literal `"string"` placeholder seen in real event data, and rejects `javascript:`/`ftp:` schemes

### `src/lib/cover.test.js` (3) — the deterministic placeholder-cover generator is stable per event id and never throws on empty input

### `src/components/ui/Button.test.jsx` (4) — renders as a native button, a router `Link`, or a plain `<a>` depending on props; respects `disabled`

### `src/components/ui/EventCard.test.jsx` (5) — shows "Free" vs. a formatted price, links to the right event, and falls back to the generated cover rather than trusting a non-URL `banner_url`

### `src/context/AuthContext.test.jsx` (5) — no user when no token is stored; loads the user on mount when one is; `login()` stores tokens and populates the user, or surfaces the server's error message; `logout()` clears everything

### `src/pages/Login.test.jsx` (3) — submits credentials, redirects to `/dashboard` on success, shows the error and does not navigate on failure

### `src/pages/Register.test.jsx` (3) — submits the three fields to `register()`, redirects on success, shows the error on failure

### `src/pages/NotFound.test.jsx` (1) — renders a 404 with a working link home

---

## Follow-ups (not in this pass)

- **Frontend page coverage**: `Home`, `Events`, `EventDetail`, `Dashboard`, `CreateEvent`, `Checkout`, `Navbar` are untested. These need heavier setup (mocked Axios responses for multiple endpoints, a mocked Stripe Elements provider, mocked `react-qr-code`) — worth a dedicated follow-up pass rather than rushing it here.
- **Backend**: no load/concurrency tests (e.g. two simultaneous `POST /payments/` for the same registration), and no test exercises `stripe.error.StripeError` being raised mid-call (the 502 paths in `payments/services.py`).
- **CI**: these suites run locally only right now — nothing runs them automatically on push. Wiring up a GitHub Actions workflow to run both suites on every PR is the natural next step so this report doesn't go stale.
