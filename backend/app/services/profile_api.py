"""
Profile API service for managing user language profiles with Supabase persistence.
"""
from typing import Dict, List, Optional

from app.db.models import DatabaseService, UserProfile
from app.models.domain.profiles import (
    SupportedLanguage,
    UserLanguageProfile,
    VoiceAvatar,
    VOICE_AVATARS
)
from app.services.livekit.room_manager import PatternBRoomManager


class ProfileAPI:
    """API for managing user language profiles with database persistence."""

    def __init__(self, room_manager: PatternBRoomManager, db_service: DatabaseService):
        self.room_manager = room_manager
        self.db = db_service

    async def create_user_profile(
        self,
        user_identity: str,
        native_language: str,
        voice_avatar_id: Optional[str] = None,
        translation_preferences: Optional[Dict[str, bool]] = None
    ) -> UserLanguageProfile:
        """Create a user profile with language and voice preferences"""

        # Validate language
        try:
            lang = SupportedLanguage(native_language)
        except ValueError:
            lang = SupportedLanguage.ENGLISH

        # Select voice avatar
        if voice_avatar_id:
            avatar = self._find_voice_avatar(voice_avatar_id, lang)
        else:
            avatar = VOICE_AVATARS.get(lang.value, VOICE_AVATARS["en"])[0]

        # Set preferences
        preferences = translation_preferences or {
            "formal_tone": False,
            "preserve_emotion": True
        }

        # Create domain model
        profile = UserLanguageProfile(
            user_identity=user_identity,
            native_language=lang,
            preferred_voice_avatar=avatar,
            translation_preferences=preferences
        )

        # Save to database
        db_profile = UserProfile(
            user_identity=user_identity,
            native_language=lang.value,
            voice_avatar_id=avatar.voice_id,
            voice_provider=avatar.provider,
            formal_tone=preferences["formal_tone"],
            preserve_emotion=preferences["preserve_emotion"],
        )

        await self.db.create_user_profile(db_profile)

        # Register in room manager cache
        self.room_manager.register_user_profile(profile)
        return profile

    def _find_voice_avatar(self, voice_id: str, language: SupportedLanguage) -> VoiceAvatar:
        """Find voice avatar by ID within language"""
        avatars = VOICE_AVATARS.get(language.value, [])
        for avatar in avatars:
            if avatar.voice_id == voice_id:
                return avatar

        # Fallback to first available avatar for language
        if avatars:
            return avatars[0]

        # Ultimate fallback
        return VOICE_AVATARS["en"][0]

    async def list_available_voices(self, language: Optional[str] = None) -> Dict[str, List[VoiceAvatar]]:
        """List all available voice avatars from database"""
        # For now, return static voices. In production, you might want to store these in DB
        if language:
            try:
                lang = SupportedLanguage(language)
                return {lang.value: VOICE_AVATARS.get(lang.value, [])}
            except ValueError:
                return {}

        return VOICE_AVATARS

    async def update_user_voice_avatar(self, user_identity: str, voice_avatar_id: str) -> bool:
        """Update user's voice avatar in database"""
        # Get current profile
        profile = await self.room_manager.get_user_profile(user_identity)
        if not profile:
            return False

        new_avatar = self._find_voice_avatar(voice_avatar_id, profile.native_language)

        # Update in database
        updates = {
            "voice_avatar_id": new_avatar.voice_id,
            "voice_provider": new_avatar.provider,
        }

        success = await self.db.update_user_profile(user_identity, updates)

        if success:
            # Update in cache
            profile.preferred_voice_avatar = new_avatar
            self.room_manager.register_user_profile(profile)

        return success
