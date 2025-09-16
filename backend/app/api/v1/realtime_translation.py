"""
API endpoints for real-time translation rooms.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
import logging

from app.core.config import get_settings
from app.db.v1.models import DatabaseService
from app.services.v1.livekit.room_manager import PatternBRoomManager, RoomType
from app.services.v1.livekit.agent import LiveKitService
from app.models.v1.domain.profiles import SupportedLanguage, UserLanguageProfile
from app.models.v1.domain.rooms import RoomCreateRequest

router = APIRouter(prefix="/realtime-translation", tags=["realtime-translation"])


def get_room_manager():
    """Get room manager dependency."""
    from app.main import app
    return app.state.room_manager


def get_livekit_service(room_manager: PatternBRoomManager = Depends(get_room_manager)):
    """Get LiveKit service dependency."""
    from app.main import app
    return app.state.livekit_service


@router.post("/rooms/create")
async def create_translation_room(
    host_identity: str,
    host_language: str,
    participant_b_identity: str,
    participant_b_language: str,
    room_name: Optional[str] = None,
    room_manager: PatternBRoomManager = Depends(get_room_manager),
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """
    Create a 2-user real-time translation room.
    
    This creates a specialized room optimized for simultaneous interpretation
    between two users speaking different languages.
    """
    try:
        # Validate languages
        try:
            host_lang = SupportedLanguage(host_language)
            participant_b_lang = SupportedLanguage(participant_b_language)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language. Supported: {[lang.value for lang in SupportedLanguage]}"
            )
        
        # Ensure different languages for translation
        if host_lang == participant_b_lang:
            raise HTTPException(
                status_code=400,
                detail="Translation rooms require participants to speak different languages"
            )
        
        # Create the translation room
        room = await room_manager.create_translation_room(
            host_identity=host_identity,
            participant_b_identity=participant_b_identity,
            room_name=room_name
        )
        
        # Generate tokens for both participants
        host_token_data = await livekit_service.generate_room_token(
            user_identity=host_identity,
            room_name=room.room_name,
            metadata={
                "language": host_lang.value,
                "role": "host",
                "room_type": "translation"
            }
        )
        
        participant_b_token_data = await livekit_service.generate_room_token(
            user_identity=participant_b_identity,
            room_name=room.room_name,
            metadata={
                "language": participant_b_lang.value,
                "role": "participant",
                "room_type": "translation"
            }
        )
        
        return {
            "room": {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "room_type": "translation",
                "max_participants": 2,
                "join_url": room.join_url
            },
            "participants": {
                "host": {
                    "identity": host_identity,
                    "language": host_lang.value,
                    "token": host_token_data["token"],
                    "ws_url": host_token_data["ws_url"]
                },
                "participant_b": {
                    "identity": participant_b_identity,
                    "language": participant_b_lang.value,
                    "token": participant_b_token_data["token"],
                    "ws_url": participant_b_token_data["ws_url"]
                }
            },
            "translation_config": {
                "max_delay_ms": 500,
                "interim_results": True,
                "utterance_end_ms": 500,
                "audio_routing": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating translation room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create translation room")


@router.get("/rooms/{room_id}/stats")
async def get_room_translation_stats(
    room_id: str,
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """Get real-time translation statistics for a room."""
    try:
        # Get room info
        room_manager = livekit_service.room_manager
        room = await room_manager.get_room(room_id)
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get translation service stats
        service_stats = livekit_service.realtime_translation_service.get_service_stats()
        
        return {
            "room_id": room_id,
            "room_name": room.room_name,
            "is_active": room.is_active,
            "translation_stats": service_stats,
            "performance": {
                "target_delay_ms": 500,
                "audio_routing_enabled": True,
                "interim_results_enabled": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting room stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room statistics")


@router.post("/test-setup")
async def create_test_translation_setup(
    room_manager: PatternBRoomManager = Depends(get_room_manager),
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """
    Create a test setup for real-time translation.
    
    Creates:
    - User A (Spanish speaker)
    - User B (English speaker)  
    - Translation room
    - Tokens for both users
    """
    try:
        # Create test user profiles
        from app.models.domain.profiles import VOICE_AVATARS
        
        spanish_user = UserLanguageProfile(
            user_identity="user_spanish_test",
            native_language=SupportedLanguage.SPANISH,
            preferred_voice_avatar=VOICE_AVATARS["es"][0],  # Use default Spanish avatar
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        english_user = UserLanguageProfile(
            user_identity="user_english_test", 
            native_language=SupportedLanguage.ENGLISH,
            preferred_voice_avatar=VOICE_AVATARS["en"][0],  # Use default English avatar
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        # Register profiles
        room_manager.register_user_profile(spanish_user)
        room_manager.register_user_profile(english_user)
        
        # Create translation room
        room = await room_manager.create_translation_room(
            host_identity=spanish_user.user_identity,
            participant_b_identity=english_user.user_identity,
            room_name="Test-Translation-Room"
        )
        
        # Generate tokens
        spanish_token = await livekit_service.generate_room_token(
            user_identity=spanish_user.user_identity,
            room_name=room.room_name,
            metadata={
                "language": "es",
                "role": "host",
                "room_type": "translation"
            }
        )
        
        english_token = await livekit_service.generate_room_token(
            user_identity=english_user.user_identity,
            room_name=room.room_name,
            metadata={
                "language": "en", 
                "role": "participant",
                "room_type": "translation"
            }
        )
        
        return {
            "message": "Test translation setup created successfully",
            "room": {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "join_url": room.join_url
            },
            "spanish_user": {
                "identity": spanish_user.user_identity,
                "language": "Spanish",
                "token": spanish_token["token"],
                "ws_url": spanish_token["ws_url"]
            },
            "english_user": {
                "identity": english_user.user_identity,
                "language": "English", 
                "token": english_token["token"],
                "ws_url": english_token["ws_url"]
            },
            "instructions": {
                "spanish_user": "User A speaks Spanish → User B hears it in English",
                "english_user": "User B speaks English → User A hears it in Spanish",
                "features": [
                    "500ms max translation delay",
                    "No audio pollution",
                    "Interim results processing",
                    "Clean audio routing"
                ]
            }
        }
        
    except Exception as e:
        logging.error(f"Error creating test setup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test setup")


@router.get("/config")
async def get_translation_config():
    """Get the current real-time translation configuration."""
    return {
        "max_delay_ms": 500,
        "interim_results": True,
        "utterance_end_ms": 500,
        "punctuate": False,
        "smart_format": False,
        "profanity_filter": False,
        "redact": False,
        "diarize": False,
        "tier": "enhanced",
        "detect_language": False,
        "confidence_threshold": 0.7,
        "audio_routing": True,
        "vad_enabled": True,
        "supported_languages": [lang.value for lang in SupportedLanguage],
        "description": "Optimized for ultra-fast 2-user simultaneous interpretation"
    }
