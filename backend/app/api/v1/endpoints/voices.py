"""
Voice avatar management API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends

from app.services.profile_api import ProfileAPI
from app.services.livekit.room_manager import PatternBRoomManager


def get_profile_api(room_manager: PatternBRoomManager = Depends(lambda: None)) -> ProfileAPI:
    """Dependency to get profile API service."""
    from app.main import app
    return app.state.profile_api


router = APIRouter()


@router.get("/")
async def list_voices(
    language: Optional[str] = None,
    profile_api: ProfileAPI = Depends(get_profile_api)
):
    """List available voice avatars."""
    voices = await profile_api.list_available_voices(language)

    # Convert VoiceAvatar objects to dictionaries for JSON response
    result = {}
    for lang, avatar_list in voices.items():
        result[lang] = [
            {
                "voice_id": avatar.voice_id,
                "provider": avatar.provider,
                "name": avatar.name,
                "gender": avatar.gender,
                "accent": avatar.accent,
                "description": avatar.description,
            }
            for avatar in avatar_list
        ]

    return {"voices": result}
