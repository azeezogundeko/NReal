"""
LiveKit room management service with Supabase persistence.
"""
from typing import Dict, Optional

from app.db.models import DatabaseService, UserProfile, Room
from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage, VoiceAvatar, VOICE_AVATARS
from app.models.domain.rooms import RoomCreateRequest


class PatternBRoomManager:
    """Manager for LiveKit rooms and user agents with database persistence."""

    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.user_profiles_cache: Dict[str, UserLanguageProfile] = {}  # For performance

    def register_user_profile(self, profile: UserLanguageProfile):
        """Register a user's language profile in cache."""
        self.user_profiles_cache[profile.user_identity] = profile

    async def get_user_profile(self, user_identity: str) -> Optional[UserLanguageProfile]:
        """Get user profile from database or cache."""
        # Check cache first
        if user_identity in self.user_profiles_cache:
            return self.user_profiles_cache[user_identity]

        # Get from database
        db_profile = await self.db.get_user_profile(user_identity)
        if db_profile:
            # Convert to domain model
            profile = UserLanguageProfile(
                user_identity=db_profile.user_identity,
                native_language=SupportedLanguage(db_profile.native_language),
                preferred_voice_avatar=self._get_voice_avatar_from_db(db_profile),
                translation_preferences={
                    "formal_tone": db_profile.formal_tone,
                    "preserve_emotion": db_profile.preserve_emotion,
                }
            )
            # Cache it
            self.user_profiles_cache[user_identity] = profile
            return profile

        # Create default profile if none exists
        return await self._create_default_profile(user_identity)

    def _get_voice_avatar_from_db(self, db_profile: UserProfile) -> VoiceAvatar:
        """Get voice avatar from database profile."""
        if db_profile.voice_avatar_id:
            # Try to find in VOICE_AVATARS
            for lang_avatars in VOICE_AVATARS.values():
                for avatar in lang_avatars:
                    if avatar.voice_id == db_profile.voice_avatar_id:
                        return avatar

        # Return default avatar
        return VOICE_AVATARS["en"][0]

    async def _create_default_profile(self, user_identity: str) -> UserLanguageProfile:
        """Create a default user profile."""
        default_profile = UserLanguageProfile(
            user_identity=user_identity,
            native_language=SupportedLanguage.ENGLISH,
            preferred_voice_avatar=VOICE_AVATARS["en"][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )

        # Save to database
        db_profile = UserProfile(
            user_identity=user_identity,
            native_language=default_profile.native_language.value,
            voice_avatar_id=default_profile.preferred_voice_avatar.voice_id,
            voice_provider=default_profile.preferred_voice_avatar.provider,
            formal_tone=default_profile.translation_preferences["formal_tone"],
            preserve_emotion=default_profile.translation_preferences["preserve_emotion"],
        )

        try:
            await self.db.create_user_profile(db_profile)
            self.user_profiles_cache[user_identity] = default_profile
        except Exception as e:
            # If database fails, still return default profile
            pass

        return default_profile

    async def create_room(self, request: RoomCreateRequest) -> Room:
        """Create a new room in database."""
        from datetime import datetime
        import uuid

        room_id = str(uuid.uuid4())
        room_name = request.room_name or f"Meeting-{room_id[:8]}"

        # Create room in database
        db_room = Room(
            room_id=room_id,
            room_name=room_name,
            host_identity=request.host_identity,
            max_participants=request.max_participants,
            is_active=True,
        )

        created_room = await self.db.create_room(db_room)
        created_room.join_url = f"/join/{created_room.room_id}"
        return created_room

    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID from database."""
        return await self.db.get_room(room_id)

    async def list_rooms(self) -> list[Room]:
        """List all active rooms from database."""
        return await self.db.list_active_rooms()

    async def delete_room(self, room_id: str):
        """Delete a room by deactivating it in database."""
        await self.db.deactivate_room(room_id)
