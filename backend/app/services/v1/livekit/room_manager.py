"""
LiveKit room management service with Supabase persistence.
Enhanced with real-time translation support.
"""
import time
from typing import Dict, Optional, NamedTuple
from enum import Enum

from app.db.v1.models import DatabaseService, UserProfile, Room
from app.models.v1.domain.profiles import UserLanguageProfile, SupportedLanguage, VoiceAvatar, VOICE_AVATARS
from app.models.v1.domain.rooms import RoomCreateRequest


class RoomType(Enum):
    """Types of rooms supported."""
    GENERAL = "general"
    TRANSLATION = "translation"  # 2-user real-time translation
    CONFERENCE = "conference"    # Multi-user conference


class CachedUserProfile(NamedTuple):
    """User profile with cache metadata."""
    profile: UserLanguageProfile
    cached_at: float  # Unix timestamp
    ttl_seconds: int = 1800  # 30 minutes
    
    @property
    def is_expired(self) -> bool:
        """Check if the cached profile has expired."""
        return time.time() - self.cached_at > self.ttl_seconds


class PatternBRoomManager:
    """Manager for LiveKit rooms and user agents with database persistence."""

    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        # TTL-based cache with 30-minute expiration
        self.user_profiles_cache: Dict[str, CachedUserProfile] = {}
        self.cache_ttl_seconds = 1800  # 30 minutes

    def register_user_profile(self, profile: UserLanguageProfile):
        """Register a user's language profile in cache with TTL."""
        cached_profile = CachedUserProfile(
            profile=profile,
            cached_at=time.time(),
            ttl_seconds=self.cache_ttl_seconds
        )
        self.user_profiles_cache[profile.user_identity] = cached_profile
        
    def cache_user_profile(self, profile: UserLanguageProfile):
        """Cache a user profile with current timestamp."""
        self.register_user_profile(profile)

    async def get_user_profile(self, user_identity: str) -> Optional[UserLanguageProfile]:
        """Get user profile from cache (with TTL) or database."""
        import logging
        
        # Check cache first and validate TTL
        if user_identity in self.user_profiles_cache:
            cached_entry = self.user_profiles_cache[user_identity]
            if not cached_entry.is_expired:
                logging.debug(f"Cache hit for user {user_identity}")
                return cached_entry.profile
            else:
                # Remove expired entry
                del self.user_profiles_cache[user_identity]
                logging.debug(f"Cache expired for user {user_identity}, removed from cache")

        # Clean up other expired entries while we're here
        self._cleanup_expired_cache()

        # Get from database with error handling
        try:
            db_profile = await self.db.get_user_profile(user_identity)
        except Exception as e:
            logging.error(f"Database error getting user profile for {user_identity}: {e}")
            # Fallback to creating default profile
            return await self._create_default_profile(user_identity)
            
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
            # Cache it with TTL
            self.cache_user_profile(profile)
            logging.info(f"Cached user profile for {user_identity} (30 min TTL)")
            return profile

        # Create default profile if none exists
        return await self._create_default_profile(user_identity)

    def _cleanup_expired_cache(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            user_identity for user_identity, cached_entry in self.user_profiles_cache.items()
            if cached_entry.is_expired
        ]
        
        for key in expired_keys:
            del self.user_profiles_cache[key]
            
        if expired_keys:
            import logging
            logging.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        total_entries = len(self.user_profiles_cache)
        expired_entries = sum(1 for entry in self.user_profiles_cache.values() if entry.is_expired)
        active_entries = total_entries - expired_entries
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }

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
            # Cache the default profile with TTL
            self.cache_user_profile(default_profile)
            import logging
            logging.info(f"Created and cached default profile for {user_identity}")
        except Exception as e:
            # If database fails, still cache the default profile
            self.cache_user_profile(default_profile)
            import logging
            logging.warning(f"Database save failed for default profile {user_identity}, but cached: {e}")

        return default_profile

    async def create_user_profile(self, profile: UserLanguageProfile) -> UserLanguageProfile:
        """Create and save a user profile."""
        # Save to database
        db_profile = UserProfile(
            user_identity=profile.user_identity,
            native_language=profile.native_language.value,
            voice_avatar_id=profile.preferred_voice_avatar.voice_id,
            voice_provider=profile.preferred_voice_avatar.provider,
            formal_tone=profile.translation_preferences.get("formal_tone", False),
            preserve_emotion=profile.translation_preferences.get("preserve_emotion", True),
        )

        try:
            await self.db.create_user_profile(db_profile)
            # Cache the profile with TTL
            self.cache_user_profile(profile)
            import logging
            logging.info(f"Created and cached profile for {profile.user_identity}")
        except Exception as e:
            # If database fails, still cache the profile
            self.cache_user_profile(profile)
            import logging
            logging.warning(f"Database save failed for profile {profile.user_identity}, but cached: {e}")

        return profile

    async def create_room(self, request: RoomCreateRequest, room_type: RoomType = RoomType.GENERAL) -> Room:
        """Create a new room in database with type specification."""
        from datetime import datetime
        import uuid

        room_id = str(uuid.uuid4())
        
        # Generate room name based on type
        if room_type == RoomType.TRANSLATION:
            room_name = request.room_name or f"Translation-{room_id[:8]}"
        elif room_type == RoomType.CONFERENCE:
            room_name = request.room_name or f"Conference-{room_id[:8]}"
        else:
            room_name = request.room_name or f"Meeting-{room_id[:8]}"

        # Set max participants based on room type
        if room_type == RoomType.TRANSLATION:
            max_participants = min(request.max_participants or 2, 2)  # Force 2 for translation
        else:
            max_participants = request.max_participants

        # Create room in database
        db_room = Room(
            room_id=room_id,
            room_name=room_name,
            host_identity=request.host_identity,
            max_participants=max_participants,
            is_active=True,
        )

        created_room = await self.db.create_room(db_room)
        created_room.join_url = f"/join/{created_room.room_id}"
        created_room.room_type = room_type.value  # Add room type info
        return created_room

    async def create_translation_room(self, 
                                    host_identity: str,
                                    participant_b_identity: str,
                                    room_name: Optional[str] = None) -> Room:
        """Create a specialized 2-user translation room."""
        import uuid
        
        room_id = str(uuid.uuid4())
        final_room_name = room_name or f"Translation-{host_identity}-{participant_b_identity}"
        
        # Create room request
        request = RoomCreateRequest(
            room_name=final_room_name,
            host_identity=host_identity,
            max_participants=2  # Exactly 2 participants for translation
        )
        
        # Create the room with translation type
        room = await self.create_room(request, RoomType.TRANSLATION)
        
        import logging
        logging.info(f"Created translation room {room.room_id} for {host_identity} <-> {participant_b_identity}")
        
        return room

    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID from database."""
        return await self.db.get_room(room_id)

    async def get_room_by_name(self, room_name: str) -> Optional[Room]:
        """Get room by name from database."""
        return await self.db.get_room_by_name(room_name)

    async def list_rooms(self) -> list[Room]:
        """List all active rooms from database."""
        return await self.db.list_active_rooms()

    async def delete_room(self, room_id: str):
        """Delete a room by deactivating it in database."""
        await self.db.deactivate_room(room_id)
