"""
Core dependencies for FastAPI application.
"""
from app.services.livekit.room_manager import PatternBRoomManager
from app.services.livekit.agent import LiveKitService


def get_livekit_service() -> LiveKitService:
    """Dependency to get LiveKit service."""
    from app.main import app
    return app.state.livekit_service


def get_room_manager() -> PatternBRoomManager:
    """Dependency to get room manager."""
    from app.main import app
    return app.state.room_manager


