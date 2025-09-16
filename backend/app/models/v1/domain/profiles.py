"""
Domain models for user profiles and language configuration.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class SupportedLanguage(str, Enum):
    """Supported languages for translation."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    IGBO = "ig"
    YORUBA = "yo"
    HAUSA = "ha"


@dataclass
class VoiceAvatar:
    """Voice avatar configuration."""
    voice_id: str
    provider: str  # "elevenlabs", "openai", "google", "spitch"
    model: str
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
            voice_id="aura-2-thalia-en",
            provider="deepgram",
            model="aura-2-thalia-en",
            name="Thalia",
            gender="female",
            accent="american",
            description="Clear, confident, energetic voice for casual chat and customer service"
        ),
        VoiceAvatar(
            voice_id="aura-2-apollo-en",
            provider="deepgram",
            model="aura-2-apollo-en",
            name="Apollo",
            gender="male",
            accent="american",
            description="Confident, comfortable, casual voice"
        ),
        VoiceAvatar(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
            provider="elevenlabs",
            model="eleven_turbo_v2_5",
            name="Rachel",
            gender="female",
            accent="american",
            description="Warm and professional female voice"
        ),
        VoiceAvatar(
            voice_id="29vD33N1CtxCmqQRPOHJ",  # Drew
            provider="elevenlabs",
            model="eleven_turbo_v2_5",
            name="Drew",
            gender="male",
            accent="american",
            description="Confident and clear male voice"
        ),
        VoiceAvatar(
            voice_id="John",
            provider="spitch",
            model="spitch-tts",
            name="John",
            gender="male",
            accent="nigerian",
            description="Loud and clear English voice"
        ),
        VoiceAvatar(
            voice_id="Lucy",
            provider="spitch",
            model="spitch-tts",
            name="Lucy",
            gender="female",
            accent="nigerian",
            description="Very clear English voice"
        ),
        VoiceAvatar(
            voice_id="Lina",
            provider="spitch",
            model="spitch-tts",
            name="Lina",
            gender="female",
            accent="nigerian",
            description="Clear, loud English voice"
        ),
        VoiceAvatar(
            voice_id="Jude",
            provider="spitch",
            model="spitch-tts",
            name="Jude",
            gender="male",
            accent="nigerian",
            description="Deep voice, smooth English"
        ),
        VoiceAvatar(
            voice_id="Henry",
            provider="spitch",
            model="spitch-tts",
            name="Henry",
            gender="male",
            accent="nigerian",
            description="Soft voice, cool tone English"
        ),
        VoiceAvatar(
            voice_id="Kani",
            provider="spitch",
            model="spitch-tts",
            name="Kani",
            gender="female",
            accent="nigerian",
            description="Soft voice, cool tone English"
        ),
    ],
    "es": [
        VoiceAvatar(
            voice_id="aura-2-celeste-es",
            provider="deepgram",
            model="aura-2-celeste-es",
            name="Celeste",
            gender="female",
            accent="colombian",
            description="Clear, energetic, positive Colombian Spanish voice"
        ),
        VoiceAvatar(
            voice_id="aura-2-nestor-es",
            provider="deepgram",
            model="aura-2-nestor-es",
            name="Nestor",
            gender="male",
            accent="peninsular",
            description="Calm, professional Peninsular Spanish voice"
        ),
    ],
    "fr": [
        VoiceAvatar(
            voice_id="aura-2-pandora-en",  # Using British accent as closest to French sophistication
            provider="deepgram",
            model="aura-2-pandora-en",
            name="Pandora",
            gender="female",
            accent="british",
            description="Smooth, calm, melodic British voice (multilingual capable)"
        ),
    ],
    "ig": [
        VoiceAvatar(
            voice_id="Obinna",
            provider="spitch",
            model="spitch-tts",
            name="Obinna",
            gender="male",
            accent="nigerian",
            description="Loud and clear Igbo voice"
        ),
        VoiceAvatar(
            voice_id="Ngozi",
            provider="spitch",
            model="spitch-tts",
            name="Ngozi",
            gender="female",
            accent="nigerian",
            description="A bit quiet and soft Igbo voice"
        ),
        VoiceAvatar(
            voice_id="Amara",
            provider="spitch",
            model="spitch-tts",
            name="Amara",
            gender="female",
            accent="nigerian",
            description="Clear, loud Igbo voice"
        ),
        VoiceAvatar(
            voice_id="Ebuka",
            provider="spitch",
            model="spitch-tts",
            name="Ebuka",
            gender="male",
            accent="nigerian",
            description="Soft voice, cool tone Igbo"
        ),
    ],
    "yo": [
        VoiceAvatar(
            voice_id="Sade",
            provider="spitch",
            model="spitch-tts",
            name="Sade",
            gender="female",
            accent="nigerian",
            description="Energetic, but breezy Yoruba voice"
        ),
        VoiceAvatar(
            voice_id="Funmi",
            provider="spitch",
            model="spitch-tts",
            name="Funmi",
            gender="female",
            accent="nigerian",
            description="Calm, can sometimes be fun Yoruba voice"
        ),
        VoiceAvatar(
            voice_id="Segun",
            provider="spitch",
            model="spitch-tts",
            name="Segun",
            gender="male",
            accent="nigerian",
            description="Vibrant, yet cool Yoruba voice"
        ),
        VoiceAvatar(
            voice_id="Femi",
            provider="spitch",
            model="spitch-tts",
            name="Femi",
            gender="male",
            accent="nigerian",
            description="Really fun guy to interact with - Yoruba"
        ),
    ],
    "ha": [
        VoiceAvatar(
            voice_id="Hasan",
            provider="spitch",
            model="spitch-tts",
            name="Hasan",
            gender="male",
            accent="nigerian",
            description="Loud and clear Hausa voice"
        ),
        VoiceAvatar(
            voice_id="Amina",
            provider="spitch",
            model="spitch-tts",
            name="Amina",
            gender="female",
            accent="nigerian",
            description="A bit quiet and soft Hausa voice"
        ),
        VoiceAvatar(
            voice_id="Zainab",
            provider="spitch",
            model="spitch-tts",
            name="Zainab",
            gender="female",
            accent="nigerian",
            description="Clear, loud Hausa voice"
        ),
        VoiceAvatar(
            voice_id="Aliyu",
            provider="spitch",
            model="spitch-tts",
            name="Aliyu",
            gender="male",
            accent="nigerian",
            description="Soft voice, cool tone Hausa"
        ),
    ],
}
