"""
Pydantic models for token generation.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response model for LiveKit token."""
    token: str
    ws_url: str
    room_name: str
    user_profile: dict
