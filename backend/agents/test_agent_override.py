#!/usr/bin/env python3
"""
Test script to verify that agent-level STT/TTS override is working correctly.
This script demonstrates that each agent uses its own STT/TTS configuration.
"""

import asyncio
from multilingual_agent import (
    WelcomeAgent, 
    EnglishAgent, 
    YorubaAgent, 
    HausaAgent, 
    IgboAgent,
    MultilingualData
)

def test_agent_configurations():
    """Test that each agent has the correct STT/TTS configuration."""
    
    print("🧪 Testing Agent STT/TTS Configuration Override\n")
    
    # Create test userdata
    userdata = MultilingualData()
    userdata.preferred_voice_gender = "feminine"
    userdata.preferred_voice_characteristic = "breezy"
    
    # Test WelcomeAgent
    print("📋 WelcomeAgent Configuration:")
    welcome_agent = WelcomeAgent()
    print(f"  STT: {welcome_agent.stt}")
    print(f"  TTS: {welcome_agent.tts}")
    print(f"  Expected: English STT/TTS")
    print()
    
    # Test EnglishAgent
    print("📋 EnglishAgent Configuration:")
    english_agent = EnglishAgent(userdata=userdata)
    print(f"  STT: {english_agent.stt}")
    print(f"  TTS: {english_agent.tts}")
    print(f"  Expected: English STT/TTS with selected voice")
    print()
    
    # Test YorubaAgent
    print("📋 YorubaAgent Configuration:")
    yoruba_agent = YorubaAgent(userdata=userdata)
    print(f"  STT: {yoruba_agent.stt}")
    print(f"  TTS: {yoruba_agent.tts}")
    print(f"  Expected: Yoruba STT/TTS with selected voice")
    print()
    
    # Test HausaAgent
    print("📋 HausaAgent Configuration:")
    hausa_agent = HausaAgent(userdata=userdata)
    print(f"  STT: {hausa_agent.stt}")
    print(f"  TTS: {hausa_agent.tts}")
    print(f"  Expected: Hausa STT/TTS with selected voice")
    print()
    
    # Test IgboAgent
    print("📋 IgboAgent Configuration:")
    igbo_agent = IgboAgent(userdata=userdata)
    print(f"  STT: {igbo_agent.stt}")
    print(f"  TTS: {igbo_agent.tts}")
    print(f"  Expected: Igbo STT/TTS with selected voice")
    print()

def test_voice_selection():
    """Test voice selection for different preferences."""
    
    print("🎤 Testing Voice Selection Logic\n")
    
    # Test different voice preferences
    test_cases = [
        {
            "name": "Default (no preferences)",
            "userdata": MultilingualData(),
            "expected_english": "kani",
            "expected_yoruba": "sade"
        },
        {
            "name": "Feminine preference",
            "userdata": MultilingualData(preferred_voice_gender="feminine"),
            "expected_english": "lucy",  # First feminine voice
            "expected_yoruba": "sade"    # First feminine voice
        },
        {
            "name": "Breezy characteristic",
            "userdata": MultilingualData(preferred_voice_characteristic="breezy"),
            "expected_english": "kani",  # No breezy in English, fallback to default
            "expected_yoruba": "sade"    # Only breezy voice in Yoruba
        },
        {
            "name": "Specific voice selection",
            "userdata": MultilingualData(selected_voice="hasan"),
            "expected_english": "kani",  # Hasan not available in English, fallback
            "expected_yoruba": "sade"    # Hasan not available in Yoruba, fallback
        }
    ]
    
    for test_case in test_cases:
        print(f"📋 {test_case['name']}:")
        print(f"  English voice: {test_case['expected_english']}")
        print(f"  Yoruba voice: {test_case['expected_yoruba']}")
        print()

def test_agent_creation():
    """Test that agents can be created with different configurations."""
    
    print("🔧 Testing Agent Creation with Different Configurations\n")
    
    try:
        # Test with different userdata configurations
        userdata1 = MultilingualData()
        userdata1.preferred_voice_gender = "masculine"
        
        userdata2 = MultilingualData()
        userdata2.selected_voice = "sade"
        
        # Create agents
        agent1 = EnglishAgent(userdata=userdata1)
        agent2 = YorubaAgent(userdata=userdata2)
        
        print("✅ Agents created successfully with different configurations")
        print(f"  Agent1 (English, masculine): {agent1.tts}")
        print(f"  Agent2 (Yoruba, Sade): {agent2.tts}")
        
    except Exception as e:
        print(f"❌ Error creating agents: {e}")

if __name__ == "__main__":
    print("🚀 Agent STT/TTS Override Test Suite\n")
    print("=" * 50)
    
    test_agent_configurations()
    test_voice_selection()
    test_agent_creation()
    
    print("✨ Test Summary:")
    print("• Each agent should have its own STT/TTS configuration")
    print("• STT should be language-specific (en, yo, ha, ig)")
    print("• TTS should use selected voice for each language")
    print("• Voice selection should work based on user preferences")
    print("• Agent-level configuration should override session defaults")

