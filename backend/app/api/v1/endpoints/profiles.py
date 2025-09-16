"""
Profile management API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from app.models.v1.pydantic_.profiles import (
    CreateProfileRequest,
    UpdateVoiceRequest,
    UserProfileResponse
)
from app.services.profile_api import ProfileAPI
from app.services.v1.livekit.room_manager import PatternBRoomManager


def get_profile_api() -> ProfileAPI:
    """Dependency to get profile API service."""
    # This will be replaced with proper dependency injection
    from app.main import app
    return app.state.profile_api


router = APIRouter()

@router.get("/{user_identity}", response_model=UserProfileResponse)
async def get_user_profile(
    user_identity: str,
    profile_api: ProfileAPI = Depends(get_profile_api)
):
    """Get user profile - creates default profile if none exists."""
    from app.main import app
    # Use room_manager to get or create profile (it has the get-or-create logic)
    profile = await app.state.room_manager.get_user_profile(user_identity)
    # print(profile)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    return UserProfileResponse(
        user_identity=profile.user_identity,
        native_language=profile.native_language.value,
        voice_avatar={
            "voice_id": profile.preferred_voice_avatar.voice_id,
            "provider": profile.preferred_voice_avatar.provider,
            "name": profile.preferred_voice_avatar.name,
            "gender": profile.preferred_voice_avatar.gender,
            "accent": profile.preferred_voice_avatar.accent,
            "description": profile.preferred_voice_avatar.description,
        },
        translation_preferences=profile.translation_preferences
    )

@router.post("/", response_model=UserProfileResponse)
async def create_user_profile(
    request: CreateProfileRequest,
    profile_api: ProfileAPI = Depends(get_profile_api)
):
    """Create a user language profile."""
    try:
        profile = await profile_api.create_user_profile(
            user_identity=request.user_identity,
            native_language=request.native_language,
            voice_avatar_id=request.voice_avatar_id,
            translation_preferences={
                "formal_tone": request.formal_tone,
                "preserve_emotion": request.preserve_emotion
            }
        )
        return UserProfileResponse(
            user_identity=profile.user_identity,
            native_language=profile.native_language.value,
            voice_avatar={
                "voice_id": profile.preferred_voice_avatar.voice_id,
                "provider": profile.preferred_voice_avatar.provider,
                "name": profile.preferred_voice_avatar.name,
                "gender": profile.preferred_voice_avatar.gender,
                "accent": profile.preferred_voice_avatar.accent,
                "description": profile.preferred_voice_avatar.description,
            },
            translation_preferences=profile.translation_preferences
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_identity}/voice")
async def update_voice_avatar(
    user_identity: str,
    request: UpdateVoiceRequest,
    profile_api: ProfileAPI = Depends(get_profile_api)
):
    """Update user's voice avatar."""
    success = await profile_api.update_user_voice_avatar(user_identity, request.voice_avatar_id)
    if not success:
        raise HTTPException(status_code=404, detail="User profile not found")

    return {"success": True, "message": "Voice avatar updated"}


