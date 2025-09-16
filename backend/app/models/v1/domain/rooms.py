"""
Domain models for room management.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Room:
    """Room domain model."""
    room_id: str
    room_name: str
    host_identity: str
    created_at: datetime
    max_participants: int = 50
    participant_count: int = 0
    join_url: str = ""
    is_active: bool = True


@dataclass
class RoomJoinRequest:
    """Request to join a room."""
    user_identity: str
    room_name: Optional[str] = None
    user_metadata: Optional[dict] = None


@dataclass
class RoomCreateRequest:
    """Request to create a room."""
    host_identity: str
    room_name: Optional[str] = None
    max_participants: int = 50
