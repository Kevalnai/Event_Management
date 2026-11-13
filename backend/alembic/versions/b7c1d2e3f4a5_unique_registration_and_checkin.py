"""one registration per user per event, one check-in per registration

Closes two race conditions where an application-level "does it already
exist?" check could be passed by two simultaneous requests:
- two door scanners checking the same ticket in at the same instant
- a double-clicked / retried "Register" creating duplicate registrations

Revision ID: b7c1d2e3f4a5
Revises: ac8e74e8e731
Create Date: 2026-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c1d2e3f4a5'
down_revision: Union[str, Sequence[str], None] = 'ac8e74e8e731'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Duplicate check-ins carry no information beyond the first one (same
    # registration, same person through the door), so keep the earliest and
    # drop the rest - otherwise the constraint below can't be created.
    conn.execute(sa.text("""
        DELETE FROM checkins c
        USING checkins keep
        WHERE c.registration_id = keep.registration_id
          AND (c.checkin_time, c.checkin_id::text) > (keep.checkin_time, keep.checkin_id::text)
    """))

    # Duplicate registrations may each have their own payment or ticket, so
    # they are NOT deleted automatically - stop and let a human decide.
    duplicates = conn.execute(sa.text("""
        SELECT event_id, user_id, count(*)
        FROM event_registrations
        WHERE user_id IS NOT NULL
        GROUP BY event_id, user_id
        HAVING count(*) > 1
    """)).fetchall()
    if duplicates:
        rows = "\n".join(f"  event_id={e} user_id={u} count={n}" for e, u, n in duplicates)
        raise RuntimeError(
            "Cannot add uq_event_registrations_event_user: these users have more "
            "than one registration for the same event. Resolve them (keep the one "
            "with a payment/ticket) and re-run the migration:\n" + rows
        )

    op.create_unique_constraint(
        'uq_checkins_registration_id', 'checkins', ['registration_id']
    )
    op.create_unique_constraint(
        'uq_event_registrations_event_user', 'event_registrations', ['event_id', 'user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_event_registrations_event_user', 'event_registrations', type_='unique')
    op.drop_constraint('uq_checkins_registration_id', 'checkins', type_='unique')
