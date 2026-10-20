# Ripple — Test Report

**Run date:** 2026-10-21
**Environment:** Python 3.14.6 · FastAPI 0.122.0 · pytest 9.1.1 · Node v24.18.0 · Vitest 5.0.5
**Database under test:** a dedicated `event_management_test` Postgres database (never the dev/prod database)
**Stripe:** every test mocks the Stripe SDK directly — no test in this suite makes a real network call to Stripe

## Summary

| Suite | Framework | Tests | Passed | Failed | Statement coverage |
|---|---|---|---|---|---|
| Backend (`backend/tests/`) | pytest + Starlette `TestClient` | 62 | 62 | 0 | 94% |
| Frontend (`frontend/src/**/*.test.jsx`) | Vitest + React Testing Library | 42 | 42 | 0 | 27% (see note below) |
| **Total** | | **104** | **104** | **0** | |

Full raw output: [`backend-results.txt`](./backend-results.txt), [`frontend-results.txt`](./frontend-results.txt), and a browsable HTML report at [`backend-report.html`](./backend-report.html). Both suites now also run automatically on every push/PR via [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

**Frontend coverage note:** 27% is a true but incomplete picture — it reflects that this first pass tests every pure utility (`lib/format.js`, `lib/cover.js`, `lib/isUrl.js`), the two most reused UI primitives (`Button`, `EventCard`), `AuthContext` end-to-end, and the two auth pages (`Login`, `Register`). It does **not** yet cover the heavier pages (`Home`, `Events`, `EventDetail`, `Dashboard`, `CreateEvent`, `Checkout`, `Navbar`) — those need Stripe Elements, router, and multi-endpoint API mocking to test properly and are listed under Follow-ups.

## Security hardening pass (2026-10-21)

A full security/production-readiness audit was run against the live code (not memory), and everything it found was fixed in this pass:

| Issue | Fix |
|---|---|
| CORS wide open (`allow_origins=["*"]` + `allow_credentials=True`, an invalid combination) | Origins now read from `ALLOWED_ORIGINS` env var (comma-separated allowlist); `allow_credentials` dropped since this API uses Bearer tokens, not cookies |
| No rate limiting anywhere | Added `slowapi`. Limits: register 5/min, login 10/min, refresh 30/min, password-reset request 3/min, password-reset confirm 10/min, payment creation 10/min — all per client IP, returning the same `{"detail": ...}` error shape as the rest of the API |
| Passwords had zero server-side strength requirement | `UserRegister.password` now requires 8+ characters with a mix of letters and numbers (server-side; the 422 was previously bypassable via direct API calls even though the frontend showed a hint) |
| `POST /auth/password-reset/request` leaked whether an email was registered (404 vs 200) | Always returns the same generic response regardless; the reset token is only ever included in the response when `EXPOSE_PASSWORD_RESET_TOKEN=true` (dev/test only — there's no email-sending integration yet, so this is the opt-in way to still test the flow locally) |
| `SECRET_KEY` silently fell back to the literal string `"CHANGE_THIS_IN_PRODUCTION"` if the env var was missing | Now raises `RuntimeError` at startup if unset, instead of signing JWTs with a well-known default. The real key was also rotated, since the old one had been printed into a terminal transcript earlier in this project's history |
| Dead code: `users/routes.py` (unreachable, broken import) and `core/security.py` (orphaned duplicate of the JWT/password logic that caused the `SECRET_KEY` duplication bug earlier in this project) | Both deleted |
| `banner_url` had no server-side format validation | Pydantic validator now requires a real `http://`/`https://` URL (mirrors the frontend's existing `isImageUrl` check) |
| `price` accepted negative values | Pydantic validator rejects `price < 0` |
| `RoleUpdate.role` accepted any string | Constrained to `Literal["user", "admin"]` |
| No pagination — `GET /events/`, `/events/{id}/registrations`, `/events/me/registrations` returned unbounded result sets | Added `limit`/`offset` query params (default 50, max 100) to all three |
| No database migrations — `Base.metadata.create_all()` only creates missing tables, never alters existing ones | Set up Alembic. Generated the initial migration (reviewed, applied, round-trip tested upgrade→downgrade→upgrade against a scratch database) and a second real migration that dropped a stray `payments.transaction_id` column that had drifted out of sync with the model. `create_all()` stays as a harmless no-op convenience for brand-new databases; any schema change to an existing one now goes through Alembic |
| No error monitoring | Optional Sentry init, active only when `SENTRY_DSN` is set |
| No CI | Added `.github/workflows/ci.yml` — runs both test suites (with a real Postgres service container for the backend) on every push/PR |

**A bug found while writing this pass's migration**: Alembic's autogenerate produced an `upgrade()` that created three Postgres native enum types but a `downgrade()` that only dropped the tables, not the enum types themselves. Verified via a full upgrade → downgrade → upgrade round-trip against a scratch database, which failed the second upgrade with `type "organiser_role_enum" already exists`. Fixed by adding explicit `sa.Enum(...).drop(op.get_bind(), checkfirst=True)` calls to the downgrade — a known Alembic/Postgres-enum gap, not something autogenerate catches on its own.

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

## Backend test cases (62)

### `tests/test_auth.py` — registration, login, sessions, global RBAC, password reset (23)

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
| `test_password_reset_request_does_not_leak_whether_email_exists` | Known and unknown emails get the identical response; a token is only actually created for the real one (regression test) |
| `test_password_reset_rejects_bad_token` | 400 on a garbage reset token |
| `test_register_rejects_weak_passwords` *(×3)* | 422 for too-short, all-letters, and all-digits passwords |
| `test_promote_rejects_invalid_role_value` | 422 if a role other than `"user"`/`"admin"` is sent |

### `tests/test_events.py` — categories, event CRUD, per-event RBAC, sessions, registrations, check-ins (26)

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
| `test_create_event_rejects_non_url_banner` | 422 for a `banner_url` that isn't a real URL (e.g. the literal `"string"` seen in real data) |
| `test_create_event_rejects_negative_price` | 422 for a negative price |
| `test_list_events_respects_limit_and_offset` | Pagination actually slices the result set |
| `test_list_events_rejects_oversized_limit` | 422 for `limit=1000` (max is 100) |

### `tests/test_rate_limiting.py` — rate limiting (2)

Disabled globally for the rest of the suite (every request from `TestClient` shares one "IP"), and turned on just for these two tests against the same shared limiter singleton every route uses.

| Test | Verifies |
|---|---|
| `test_register_is_rate_limited` | 6th registration attempt in a burst gets 429 (limit is 5/min) |
| `test_password_reset_request_is_rate_limited` | 4th reset request in a burst gets 429 (limit is 3/min) |

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
- **Rate limit storage is in-memory**: correct for a single process, but if this is ever deployed as multiple worker processes/instances behind a load balancer, each would count its own limits separately. Point `app/core/limiter.py` at Redis (`storage_uri="redis://..."`) before scaling out horizontally.
- **No real email sending**: password reset tokens have nowhere to go except the API response (gated behind `EXPOSE_PASSWORD_RESET_TOKEN`, dev-only). Wiring up an actual email provider is required before this flow is usable by real users.
- **First platform admin still requires direct DB access** — `UPDATE users SET role='admin' WHERE email=...` — by design, since there's deliberately no self-service or bootstrap-via-API path. Document this in whatever deploy runbook exists so a fresh production database doesn't get stuck with no admin.
