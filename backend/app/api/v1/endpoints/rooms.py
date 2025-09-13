"""
Room management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.pydantic_.rooms import (
    CreateRoomRequest,
    RoomInfoResponse,
    RoomListResponse
)
from app.services.livekit.room_manager import PatternBRoomManager
from app.services.livekit.agent import LiveKitService


def get_room_manager() -> PatternBRoomManager:
    """Dependency to get room manager."""
    from app.main import app
    return app.state.room_manager


def get_livekit_service() -> LiveKitService:
    """Dependency to get LiveKit service."""
    from app.main import app
    return app.state.livekit_service


router = APIRouter()


@router.post("/")
async def create_room(
    request: CreateRoomRequest,
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Create a new meeting room."""
    try:
        room = await room_manager.create_room(request)

        # Create and cache profile for the host if they don't have one
        profile = await room_manager.get_user_profile(request.host_identity)
        logging.info(f"Room created by {request.host_identity}, profile cached for 30 minutes")

        return {
            "success": True,
            "room": {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "join_url": room.join_url,
                "host_profile": {
                    "user_identity": profile.user_identity if profile else request.host_identity,
                    "native_language": profile.native_language.value if profile else "en",
                } if profile else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=RoomListResponse)
async def list_rooms(
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """List all active rooms."""
    rooms = await room_manager.list_rooms()
    room_responses = []

    for room in rooms:
        room_responses.append(RoomInfoResponse(
            room_id=room.room_id,
            room_name=room.room_name,
            host_identity=room.host_identity,
            created_at=room.created_at,
            max_participants=room.max_participants,
            participant_count=room.participant_count,
            join_url=room.join_url
        ))

    return RoomListResponse(rooms=room_responses)


@router.get("/{room_id}", response_model=RoomInfoResponse)
async def get_room(
    room_id: str,
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Get room information."""
    room = await room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return RoomInfoResponse(
        room_id=room.room_id,
        room_name=room.room_name,
        host_identity=room.host_identity,
        created_at=room.created_at,
        max_participants=room.max_participants,
        participant_count=room.participant_count,
        join_url=room.join_url
    )


@router.get("/cache/stats")
async def get_cache_stats(
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Get user profile cache statistics."""
    try:
        stats = room_manager.get_cache_stats()
        return {
            "success": True,
            "cache_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup")
async def cleanup_cache(
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Manually trigger cache cleanup of expired entries."""
    try:
        initial_count = len(room_manager.user_profiles_cache)
        room_manager._cleanup_expired_cache()
        final_count = len(room_manager.user_profiles_cache)
        cleaned_count = initial_count - final_count
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired cache entries",
            "initial_count": initial_count,
            "final_count": final_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{room_name}/dispatch-agent")
async def dispatch_agent_to_room(
    room_name: str,
    user_identity: str = None,
    livekit_service: LiveKitService = Depends(get_livekit_service),
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Manually dispatch a translation agent to an existing room."""
    try:
        # Verify room exists
        rooms = await room_manager.list_rooms()
        room_found = None
        for room in rooms:
            if room.room_name == room_name:
                room_found = room
                break
        
        if not room_found:
            raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")
        
        # Dispatch the agent
        result = await livekit_service.dispatch_agent_to_room(room_name, user_identity)
        
        return {
            "success": True,
            "message": f"Translation agent dispatched to room '{room_name}'",
            "dispatch_info": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch agent: {str(e)}")


@router.get("/{room_name}/dispatches")
async def list_room_dispatches(
    room_name: str,
    livekit_service: LiveKitService = Depends(get_livekit_service),
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """List all agent dispatches for a room."""
    try:
        # Verify room exists
        rooms = await room_manager.list_rooms()
        room_found = None
        for room in rooms:
            if room.room_name == room_name:
                room_found = room
                break
        
        if not room_found:
            raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")
        
        # Get dispatches
        dispatches = await livekit_service.list_agent_dispatches(room_name)
        
        return {
            "success": True,
            "room_name": room_name,
            "dispatches": dispatches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list dispatches: {str(e)}")
