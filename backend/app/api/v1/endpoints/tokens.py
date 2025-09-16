"""
LiveKit token generation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.models.pydantic_.rooms import RoomJoinRequest
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


router = APIRouter()


@router.post("/")
async def generate_room_token(
    request: RoomJoinRequest,
    livekit_service: LiveKitService = Depends(get_livekit_service),
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Generate LiveKit room token with user metadata."""

    # Validate room exists
    if request.room_name:
        # Find the room by name
        rooms = await room_manager.list_rooms()
        room_found = None
        for room in rooms:
            if room.room_name == request.room_name:
                room_found = room
                break
        if not room_found:
            raise HTTPException(status_code=404, detail="Room not found")
        actual_room_name = room_found.room_name
    else:
        raise HTTPException(status_code=400, detail="room_name is required")

    # Get and cache user profile for the room
    profile = await room_manager.get_user_profile(request.user_identity)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    import logging
    logging.info(f"User {request.user_identity} joining room {actual_room_name}, profile cached for 30 minutes")

    try:
        # Add real-time translation metadata if this is a translation room
        enhanced_metadata = request.user_metadata or {}
        if "translation" in actual_room_name.lower():
            enhanced_metadata.update({
                "room_type": "translation",
                "use_realtime": True,
                "language": enhanced_metadata.get("language", profile.native_language.value)
            })
        
        token_data = await livekit_service.generate_room_token(
            request.user_identity,
            actual_room_name,
            enhanced_metadata
        )
        return token_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
