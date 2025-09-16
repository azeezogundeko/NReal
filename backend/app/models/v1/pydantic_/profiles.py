"""
Pydantic models for profile API endpoints.
"""
from typing import Dict, Optional
from pydantic import BaseModel


class CreateProfileRequest(BaseModel):
    """Request model for creating a user profile."""
    user_identity: str
    native_language: str
    voice_avatar_id: Optional[str] = None
    formal_tone: bool = False
    preserve_emotion: bool = True


class UpdateVoiceRequest(BaseModel):
    """Request model for updating voice avatar."""
    voice_avatar_id: str


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_identity: str
    native_language: str
    voice_avatar: dict
    translation_preferences: Dict[str, bool]

    class Config:
        from_attributes = True
