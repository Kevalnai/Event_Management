# main.py

import logging
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logger = logging.getLogger("app")

from app.core.limiter import limiter
from app.core.database import Base ,engine
import app.core.model_registry 
from app.modules.users.models import Base
from app.modules.events.models import Base
from app.modules.tickets.models import Base
from app.modules.payments.models import Base
from app.modules.scanners.models import Base
from app.modules.users.auth import router as auth_router
from app.modules.events.routes import router as event_router
from app.modules.payments.routes import router as payment_router
from app.modules.tickets.routes import router as ticket_router
from app.modules.scanners.routes import router as scanner_router
def create_app():
    app = FastAPI(
        title="Event Management Backend",
        description="FastAPI backend with JWT auth and PostgreSQL",
        version="1.0.0"
    )

    # -------------------------------
    # Error monitoring (optional - only active if SENTRY_DSN is set)
    # -------------------------------
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.2, send_default_pii=False)

    # -------------------------------
    # Rate limiting (per client IP, applied per-route - see auth.py / payments/routes.py)
    # -------------------------------
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        # Match the {"detail": ...} shape every other error on this API uses.
        return JSONResponse(status_code=429, content={"detail": f"Too many requests: {exc.detail}"})

    # -------------------------------
    # Catch-all for genuinely unexpected errors (bugs, not HTTPExceptions -
    # those already have their own, more specific handler from FastAPI, so
    # this never changes their behavior).
    #
    # Without this, an unhandled exception propagates past CORSMiddleware
    # to Starlette's own ServerErrorMiddleware, which returns a response
    # with NO CORS headers at all - the browser reports that as a generic
    # "blocked by CORS policy" / network failure, hiding the real 500 and
    # making it much harder to debug. It also means a raw stack trace could
    # leak to the client. This handler runs inside CORSMiddleware's layer
    # (so headers are added correctly) and always returns a safe message.
    # -------------------------------
    @app.exception_handler(Exception)
    def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.add_middleware(SlowAPIMiddleware)

    # -------------------------------
    # CORS configuration
    # -------------------------------
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,  # Bearer-token auth, not cookies - credentials aren't needed
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------
    # Database Table Creation
    # -------------------------------
    # Safe no-op for an already-up-to-date database: this only *creates*
    # tables that don't exist yet, it never alters existing ones. Schema
    # changes to an existing database go through Alembic (see backend/alembic/)
    # - run `alembic upgrade head` after pulling migrations.
    Base.metadata.create_all(bind=engine)

    # -------------------------------
    # All Routers
    # -------------------------------
    app.include_router(auth_router)
    app.include_router(event_router)
    app.include_router(payment_router)
    app.include_router(ticket_router)
    app.include_router(scanner_router)

    @app.get("/", tags=["Root"])
    def root():
        return {"message": "Backend is running successfully!"}

    return app


app = create_app()
