"""
Pydantic models for room API endpoints.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateRoomRequest(BaseModel):
    """Request model for creating a room."""
    host_identity: str
    room_name: Optional[str] = None
    max_participants: int = 50


class RoomJoinRequest(BaseModel):
    """Request model for joining a room."""
    user_identity: str
    room_name: Optional[str] = None
    user_metadata: Optional[dict] = None


class RoomInfoResponse(BaseModel):
    """Response model for room information."""
    room_id: str
    room_name: str
    host_identity: str
    created_at: datetime
    max_participants: int
    participant_count: int = 0
    join_url: str


class RoomListResponse(BaseModel):
    """Response model for room list."""
    rooms: list[RoomInfoResponse]
