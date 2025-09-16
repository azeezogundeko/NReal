"""
API endpoints for creating and managing multi-user translation rooms.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.db.v1.models import DatabaseService
from app.services.v1.livekit.room_manager import PatternBRoomManager
from app.services.v1.livekit.agent import LiveKitService
from app.models.v1.domain.profiles import SupportedLanguage, UserLanguageProfile, VOICE_AVATARS
from app.core.dependencies import get_room_manager, get_livekit_service


router = APIRouter(prefix="/translation-rooms", tags=["Translation Rooms"])


class CreateTranslationRoomRequest(BaseModel):
    user_a_identity: str
    user_a_language: str
    user_a_name: str
    user_b_identity: str
    user_b_language: str
    user_b_name: str
    room_name: Optional[str] = None


class JoinTranslationRoomRequest(BaseModel):
    room_name: str
    user_identity: str
    user_language: str
    user_name: str


@router.post("/create")
async def create_translation_room(
    request: CreateTranslationRoomRequest,
    room_manager: PatternBRoomManager = Depends(get_room_manager),
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """
    Create a new multi-user translation room for two participants.
    
    This creates a room specifically designed for real-time translation
    between two users speaking different languages.
    """
    try:
        # Validate languages
        try:
            user_a_lang = SupportedLanguage(request.user_a_language)
            user_b_lang = SupportedLanguage(request.user_b_language)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {e}")
        
        # Generate room name if not provided
        room_name = request.room_name or f"translation_room_{request.user_a_identity}_{request.user_b_identity}"
        
        # Create user profiles
        user_a_profile = UserLanguageProfile(
            user_identity=request.user_a_identity,
            native_language=user_a_lang,
            preferred_voice_avatar=VOICE_AVATARS[user_a_lang.value][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        user_b_profile = UserLanguageProfile(
            user_identity=request.user_b_identity,
            native_language=user_b_lang,
            preferred_voice_avatar=VOICE_AVATARS[user_b_lang.value][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        # Register profiles
        await room_manager.create_user_profile(user_a_profile)
        await room_manager.create_user_profile(user_b_profile)
        
        # Create room using RoomCreateRequest
        from app.models.domain.rooms import RoomCreateRequest
        from app.services.livekit.room_manager import RoomType
        
        room_request = RoomCreateRequest(
            host_identity=request.user_a_identity,
            room_name=room_name,
            max_participants=4  # 2 users + 2 agents
        )
        
        room = await room_manager.create_room(room_request, RoomType.TRANSLATION)
        
        # Generate tokens for both users
        user_a_token = await livekit_service.generate_room_token(
            user_identity=request.user_a_identity,
            room_name=room_name,
            metadata={
                "language": user_a_lang.value,
                "name": request.user_a_name,
                "role": "translator_user",
                "room_type": "translation"
            }
        )
        
        user_b_token = await livekit_service.generate_room_token(
            user_identity=request.user_b_identity,
            room_name=room_name,
            metadata={
                "language": user_b_lang.value,
                "name": request.user_b_name,
                "role": "translator_user",
                "room_type": "translation"
            }
        )
        
        return {
            "success": True,
            "room": {
                "room_name": room_name,
                "room_id": room.room_id,
                "room_type": "translation",
                "max_participants": 4
            },
            "user_a": {
                "identity": request.user_a_identity,
                "name": request.user_a_name,
                "language": user_a_lang.value,
                "token": user_a_token["token"],
                "server_url": user_a_token["ws_url"]
            },
            "user_b": {
                "identity": request.user_b_identity,
                "name": request.user_b_name,
                "language": user_b_lang.value,
                "token": user_b_token["token"],
                "server_url": user_b_token["ws_url"]
            },
            "instructions": {
                "user_a": f"{request.user_a_name} speaks {user_a_lang.value} → {request.user_b_name} hears in {user_b_lang.value}",
                "user_b": f"{request.user_b_name} speaks {user_b_lang.value} → {request.user_a_name} hears in {user_a_lang.value}",
                "note": "Both users will hear translations in real-time, but not the agent voices"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating translation room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create translation room")


@router.post("/join")
async def join_translation_room(
    request: JoinTranslationRoomRequest,
    room_manager: PatternBRoomManager = Depends(get_room_manager),
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """
    Join an existing translation room.
    """
    try:
        # Validate language
        try:
            user_language = SupportedLanguage(request.user_language)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {e}")
        
        # Check if room exists
        room = await room_manager.get_room_by_name(request.room_name)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Create or get user profile
        user_profile = await room_manager.get_user_profile(request.user_identity)
        if not user_profile:
            user_profile = UserLanguageProfile(
                user_identity=request.user_identity,
                native_language=user_language,
                preferred_voice_avatar=VOICE_AVATARS[user_language.value][0],
                translation_preferences={"formal_tone": False, "preserve_emotion": True}
            )
            await room_manager.create_user_profile(user_profile)
        
        # Generate token
        token_data = await livekit_service.generate_room_token(
            user_identity=request.user_identity,
            room_name=request.room_name,
            metadata={
                "language": user_language.value,
                "name": request.user_name,
                "role": "translator_user",
                "room_type": "translation"
            }
        )
        
        return {
            "success": True,
            "user": {
                "identity": request.user_identity,
                "name": request.user_name,
                "language": user_language.value,
                "token": token_data["token"],
                "server_url": token_data["ws_url"]
            },
            "room": {
                "room_name": request.room_name,
                "room_type": "translation"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error joining translation room: {e}")
        raise HTTPException(status_code=500, detail="Failed to join translation room")


@router.get("/test-room")
async def create_test_translation_room(
    room_manager: PatternBRoomManager = Depends(get_room_manager),
    livekit_service: LiveKitService = Depends(get_livekit_service)
):
    """
    Create a test translation room with English and Spanish users.
    """
    try:
        request = CreateTranslationRoomRequest(
            user_a_identity="alice_english",
            user_a_language="en",
            user_a_name="Alice",
            user_b_identity="bob_spanish",
            user_b_language="es",
            user_b_name="Bob",
            room_name="test_translation_room"
        )
        
        result = await create_translation_room(request, room_manager, livekit_service)
        
        # Add helpful testing instructions
        result["testing_instructions"] = {
            "step_1": "Alice joins with English token and speaks English",
            "step_2": "Bob joins with Spanish token and speaks Spanish",
            "step_3": "Alice hears Bob's Spanish translated to English",
            "step_4": "Bob hears Alice's English translated to Spanish",
            "expected_behavior": "Both users hear each other's translations but NOT the agent voices"
        }
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating test translation room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test room")
