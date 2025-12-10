# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.databse import engine
from app.modules.users.models import Base
from app.modules.users.auth import router as auth_router

def create_app():
    app = FastAPI(
        title="Event Management Backend",
        description="FastAPI backend with JWT auth and PostgreSQL",
        version="1.0.0"
    )

    # -------------------------------
    # CORS configuration
    # -------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change to specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------
    # Database Table Creation
    # -------------------------------
    Base.metadata.create_all(bind=engine)

    # -------------------------------
    # Routers
    # -------------------------------
    app.include_router(auth_router)

    @app.get("/", tags=["Root"])
    def root():
        return {"message": "Backend is running successfully!"}

    return app


app = create_app()
