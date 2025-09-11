"""
Room management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.pydantic.rooms import (
    CreateRoomRequest,
    RoomInfoResponse,
    RoomListResponse
)
from app.services.livekit.room_manager import PatternBRoomManager


def get_room_manager() -> PatternBRoomManager:
    """Dependency to get room manager."""
    from app.main import app
    return app.state.room_manager


router = APIRouter()


@router.post("/")
async def create_room(
    request: CreateRoomRequest,
    room_manager: PatternBRoomManager = Depends(get_room_manager)
):
    """Create a new meeting room."""
    try:
        room = await room_manager.create_room(request)

        # Create a default profile for the host if they don't have one
        profile = await room_manager.get_user_profile(request.host_identity)

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
