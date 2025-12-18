# Import ALL models here so SQLAlchemy can register them

from ..modules.users.models import User
from ..modules.users.models import User

from ..modules.events.models import (
    Event,
    EventCategory,
    EventOrganiser,
    EventSession,
    EventRegistration,
    CheckIn
)

from ..modules.tickets.models import Ticket
from ..modules.payments.models import Payment
