"""
FastAPI application factory for the Translation Service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.models import DatabaseService
from app.services.livekit.room_manager import PatternBRoomManager
from app.services.profile_api import ProfileAPI
from app.services.livekit.agent import LiveKitService

from supabase import create_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    print("Translation Service API starting...")

    # Initialize services
    settings = get_settings()

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)
    db_service = DatabaseService(supabase)

    # Create service instances with database support
    room_manager = PatternBRoomManager(db_service)
    profile_api = ProfileAPI(room_manager, db_service)
    livekit_service = LiveKitService(room_manager)

    # Store services in app state for dependency injection
    app.state.room_manager = room_manager
    app.state.profile_api = profile_api
    app.state.livekit_service = livekit_service
    app.state.db_service = db_service

    yield

    # Shutdown
    print("Translation Service API shutting down...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Health check endpoint
    @app.get("/")
    async def root():
        """Health check endpoint."""
        return {
            "message": "Translation Service API",
            "status": "running",
            "version": settings.app_version
        }

    return app


# Create the FastAPI application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
