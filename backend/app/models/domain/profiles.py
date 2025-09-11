"""
Domain models for user profiles and language configuration.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class SupportedLanguage(str, Enum):
    """Supported languages for translation."""
    ENGLISH = "en"
    IGBO = "ig"
    YORUBA = "yo"
    HAUSA = "ha"


@dataclass
class VoiceAvatar:
    """Voice avatar configuration."""
    voice_id: str
    provider: str  # "elevenlabs", "openai", "google"
    name: str
    gender: str
    accent: str
    description: str


@dataclass
class UserLanguageProfile:
    """User language profile with preferences."""
    user_identity: str
    native_language: SupportedLanguage
    preferred_voice_avatar: VoiceAvatar
    translation_preferences: Dict[str, bool]


# Voice Avatar Presets
VOICE_AVATARS = {
    "en": [
        VoiceAvatar(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
            provider="elevenlabs",
            name="Rachel",
            gender="female",
            accent="american",
            description="Warm and professional female voice"
        ),
        VoiceAvatar(
            voice_id="29vD33N1CtxCmqQRPOHJ",  # Drew
            provider="elevenlabs",
            name="Drew",
            gender="male",
            accent="american",
            description="Confident and clear male voice"
        ),
    ],
    "ig": [
        VoiceAvatar(
            voice_id="ig_female_1",
            provider="elevenlabs",
            name="Ada",
            gender="female",
            accent="nigerian",
            description="Native Igbo female voice"
        ),
    ],
    "yo": [
        VoiceAvatar(
            voice_id="yo_female_1",
            provider="elevenlabs",
            name="Funmi",
            gender="female",
            accent="nigerian",
            description="Native Yoruba female voice"
        ),
    ],
    "ha": [
        VoiceAvatar(
            voice_id="ha_female_1",
            provider="elevenlabs",
            name="Amina",
            gender="female",
            accent="nigerian",
            description="Native Hausa female voice"
        ),
    ],
}
