"""
Database models for Supabase.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from supabase import Client


@dataclass
class UserProfile:
    """User profile database model."""
    id: Optional[int] = None
    user_identity: str = ""
    native_language: str = ""
    voice_avatar_id: Optional[str] = None
    voice_provider: str = "elevenlabs"
    formal_tone: bool = False
    preserve_emotion: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Room:
    """Room database model."""
    id: Optional[int] = None
    room_id: str = ""
    room_name: str = ""
    host_identity: str = ""
    max_participants: int = 50
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class VoiceAvatar:
    """Voice avatar database model."""
    id: Optional[int] = None
    voice_id: str = ""
    provider: str = ""
    name: str = ""
    gender: str = ""
    accent: str = ""
    description: str = ""
    language: str = ""
    created_at: Optional[datetime] = None


class DatabaseService:
    """Service for database operations."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    # User Profile Operations
    async def create_user_profile(self, profile: UserProfile) -> UserProfile:
        """Create a new user profile."""
        data = {
            "user_identity": profile.user_identity,
            "native_language": profile.native_language,
            "voice_avatar_id": profile.voice_avatar_id,
            "voice_provider": profile.voice_provider,
            "formal_tone": profile.formal_tone,
            "preserve_emotion": profile.preserve_emotion,
        }

        result = self.supabase.table("user_profiles").insert(data).execute()
        if result.data:
            profile_data = result.data[0]
            return UserProfile(
                id=profile_data["id"],
                user_identity=profile_data["user_identity"],
                native_language=profile_data["native_language"],
                voice_avatar_id=profile_data["voice_avatar_id"],
                voice_provider=profile_data["voice_provider"],
                formal_tone=profile_data["formal_tone"],
                preserve_emotion=profile_data["preserve_emotion"],
                created_at=profile_data["created_at"],
                updated_at=profile_data["updated_at"],
            )
        raise Exception("Failed to create user profile")

    async def get_user_profile(self, user_identity: str) -> Optional[UserProfile]:
        """Get user profile by identity."""
        result = self.supabase.table("user_profiles").select("*").eq("user_identity", user_identity).execute()
        if result.data:
            profile_data = result.data[0]
            return UserProfile(
                id=profile_data["id"],
                user_identity=profile_data["user_identity"],
                native_language=profile_data["native_language"],
                voice_avatar_id=profile_data["voice_avatar_id"],
                voice_provider=profile_data["voice_provider"],
                formal_tone=profile_data["formal_tone"],
                preserve_emotion=profile_data["preserve_emotion"],
                created_at=profile_data["created_at"],
                updated_at=profile_data["updated_at"],
            )
        return None

    async def update_user_profile(self, user_identity: str, updates: Dict[str, Any]) -> bool:
        """Update user profile."""
        result = self.supabase.table("user_profiles").update(updates).eq("user_identity", user_identity).execute()
        return len(result.data) > 0

    # Room Operations
    async def create_room(self, room: Room) -> Room:
        """Create a new room."""
        data = {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "host_identity": room.host_identity,
            "max_participants": room.max_participants,
            "is_active": room.is_active,
        }

        result = self.supabase.table("rooms").insert(data).execute()
        if result.data:
            room_data = result.data[0]
            return Room(
                id=room_data["id"],
                room_id=room_data["room_id"],
                room_name=room_data["room_name"],
                host_identity=room_data["host_identity"],
                max_participants=room_data["max_participants"],
                is_active=room_data["is_active"],
                created_at=room_data["created_at"],
                updated_at=room_data["updated_at"],
            )
        raise Exception("Failed to create room")

    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by room_id."""
        result = self.supabase.table("rooms").select("*").eq("room_id", room_id).eq("is_active", True).execute()
        if result.data:
            room_data = result.data[0]
            return Room(
                id=room_data["id"],
                room_id=room_data["room_id"],
                room_name=room_data["room_name"],
                host_identity=room_data["host_identity"],
                max_participants=room_data["max_participants"],
                is_active=room_data["is_active"],
                created_at=room_data["created_at"],
                updated_at=room_data["updated_at"],
            )
        return None

    async def list_active_rooms(self) -> list[Room]:
        """List all active rooms."""
        result = self.supabase.table("rooms").select("*").eq("is_active", True).execute()
        rooms = []
        for room_data in result.data:
            rooms.append(Room(
                id=room_data["id"],
                room_id=room_data["room_id"],
                room_name=room_data["room_name"],
                host_identity=room_data["host_identity"],
                max_participants=room_data["max_participants"],
                is_active=room_data["is_active"],
                created_at=room_data["created_at"],
                updated_at=room_data["updated_at"],
            ))
        return rooms

    async def deactivate_room(self, room_id: str) -> bool:
        """Deactivate a room."""
        result = self.supabase.table("rooms").update({"is_active": False}).eq("room_id", room_id).execute()
        return len(result.data) > 0

    # Voice Avatar Operations
    async def get_voice_avatars(self, language: Optional[str] = None) -> list[VoiceAvatar]:
        """Get voice avatars, optionally filtered by language."""
        query = self.supabase.table("voice_avatars").select("*")
        if language:
            query = query.eq("language", language)

        result = query.execute()
        avatars = []
        for avatar_data in result.data:
            avatars.append(VoiceAvatar(
                id=avatar_data["id"],
                voice_id=avatar_data["voice_id"],
                provider=avatar_data["provider"],
                name=avatar_data["name"],
                gender=avatar_data["gender"],
                accent=avatar_data["accent"],
                description=avatar_data["description"],
                language=avatar_data["language"],
                created_at=avatar_data["created_at"],
            ))
        return avatars
