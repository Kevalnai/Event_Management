"""
Shared rate limiter (slowapi / Flask-Limiter style) for the whole API.

Uses in-memory storage, which is correct for a single-process deployment.
If this is ever run as multiple worker processes/instances behind a load
balancer, point it at Redis instead (`storage_uri="redis://..."`) so the
limits are shared across processes rather than counted separately by each.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Disabled only for the test suite (conftest.py sets this), since every
# request from Starlette's TestClient shares one "IP" and would otherwise
# all land in the same bucket.
_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false"

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
