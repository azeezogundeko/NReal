"""
Debug script to test the translation flow and identify issues.
"""
import asyncio
import logging
import json
from app.api.translation_rooms import TranslationRoomAPI
from app.services.realtime.audio_filter_agent import AudioFilteredTranslationService
from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage, VOICE_AVATARS

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s %(name)s - %(message)s'
)

async def test_translation_room_creation():
    """Test creating a translation room and check the flow."""
    
    print("🧪 TESTING TRANSLATION ROOM CREATION")
    print("=" * 50)
    
    # Test room creation via API
    try:
        # Create test room
        from app.api.translation_rooms import create_test_translation_room
        from app.core.dependencies import get_room_manager, get_livekit_service
        from app.db.models import DatabaseService
        from app.services.livekit.room_manager import PatternBRoomManager
        from app.services.livekit.agent import LiveKitService
        from app.core.config import get_settings
        from supabase import create_client
        
        # Initialize dependencies
        settings = get_settings()
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        db_service = DatabaseService(supabase)
        room_manager = PatternBRoomManager(db_service)
        livekit_service = LiveKitService(room_manager)
        
        print("✅ Dependencies initialized")
        
        # Create test room
        result = await create_test_translation_room(room_manager, livekit_service)
        
        print("✅ Test room created successfully")
        print(f"   - Room: {result['room']['room_name']}")
        print(f"   - User A: {result['user_a']['name']} ({result['user_a']['language']})")
        print(f"   - User B: {result['user_b']['name']} ({result['user_b']['language']})")
        
        return result
        
    except Exception as e:
        print(f"❌ Error creating test room: {e}")
        return None

def test_audio_filter_agent():
    """Test the AudioFilteredTranslationAgent configuration."""
    
    print("\n🔧 TESTING AUDIO FILTER AGENT")
    print("=" * 50)
    
    try:
        # Create test user profiles
        user_a = UserLanguageProfile(
            user_identity="test_user_a",
            native_language=SupportedLanguage.ENGLISH,
            preferred_voice_avatar=VOICE_AVATARS["en"][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        user_b = UserLanguageProfile(
            user_identity="test_user_b", 
            native_language=SupportedLanguage.SPANISH,
            preferred_voice_avatar=VOICE_AVATARS["es"][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        print("✅ User profiles created")
        print(f"   - User A: {user_a.user_identity} ({user_a.native_language})")
        print(f"   - User B: {user_b.user_identity} ({user_b.native_language})")
        
        # Create audio filter service
        service = AudioFilteredTranslationService()
        print("✅ AudioFilteredTranslationService created")
        
        # Test agent creation
        agent_a = asyncio.run(service.create_agent(user_a))
        agent_b = asyncio.run(service.create_agent(user_b))
        
        print("✅ Agents created successfully")
        print(f"   - Agent A for: {agent_a.user_profile.user_identity}")
        print(f"   - Agent B for: {agent_b.user_profile.user_identity}")
        
        # Test participant registration
        agent_a.register_participant("test_user_b", SupportedLanguage.SPANISH)
        agent_b.register_participant("test_user_a", SupportedLanguage.ENGLISH)
        
        print("✅ Participants registered")
        print(f"   - Agent A will translate for: {list(agent_a.target_participants.keys())}")
        print(f"   - Agent B will translate for: {list(agent_b.target_participants.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing audio filter agent: {e}")
        return False

def test_speech_event_simulation():
    """Simulate speech events to test the flow."""
    
    print("\n🎤 SIMULATING SPEECH EVENTS")
    print("=" * 50)
    
    try:
        # Create a mock speech event
        class MockSpeechEvent:
            def __init__(self, user_transcript, participant_identity):
                self.user_transcript = user_transcript
                self.participant = MockParticipant(participant_identity)
        
        class MockParticipant:
            def __init__(self, identity):
                self.identity = identity
        
        # Create test agents
        user_a = UserLanguageProfile(
            user_identity="alice_english",
            native_language=SupportedLanguage.ENGLISH,
            preferred_voice_avatar=VOICE_AVATARS["en"][0],
            translation_preferences={"formal_tone": False, "preserve_emotion": True}
        )
        
        service = AudioFilteredTranslationService()
        agent_a = asyncio.run(service.create_agent(user_a))
        
        # Register Spanish speaker
        agent_a.register_participant("bob_spanish", SupportedLanguage.SPANISH)
        
        print("✅ Agent created and participant registered")
        
        # Simulate speech event
        mock_event = MockSpeechEvent("Hola, ¿cómo estás?", "bob_spanish")
        
        # Test translation
        async def test_translation():
            translated = await agent_a.translate_speech("Hola, ¿cómo estás?", "bob_spanish")
            return translated
        
        result = asyncio.run(test_translation())
        
        print(f"✅ Translation test completed")
        print(f"   - Original: 'Hola, ¿cómo estás?'")
        print(f"   - Translated: '{result}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error simulating speech events: {e}")
        return False

def main():
    """Run all debug tests."""
    
    print("🔍 TRANSLATION FLOW DEBUG SCRIPT")
    print("=" * 50)
    print("This script will test the translation flow and identify issues.")
    print()
    
    # Test 1: Room creation
    room_result = asyncio.run(test_translation_room_creation())
    
    # Test 2: Agent configuration
    agent_result = test_audio_filter_agent()
    
    # Test 3: Speech simulation
    speech_result = test_speech_event_simulation()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Room Creation: {'✅ PASS' if room_result else '❌ FAIL'}")
    print(f"Agent Config:  {'✅ PASS' if agent_result else '❌ FAIL'}")
    print(f"Speech Events: {'✅ PASS' if speech_result else '❌ FAIL'}")
    
    if all([room_result, agent_result, speech_result]):
        print("\n🎉 ALL TESTS PASSED - Translation flow should work!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Check the logs above for issues")
    
    print("\n📋 NEXT STEPS:")
    print("1. Start your backend server")
    print("2. Create a test translation room via API")
    print("3. Connect two users and check terminal logs for:")
    print("   - 🏠 ROOM ANALYSIS logs")
    print("   - 🔗 PARTICIPANT CONNECTED logs") 
    print("   - 👥 PARTICIPANT REGISTERED logs")
    print("   - 🎤 SPEECH RECEIVED logs")
    print("   - 🔄 PROCESSING TRANSLATION logs")

if __name__ == "__main__":
    main()
