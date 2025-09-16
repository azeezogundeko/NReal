#!/usr/bin/env python3
"""
Voice Configuration Example for Multilingual Agent

This script demonstrates how the voice selection system works
with different user preferences and voice characteristics.
"""

from multilingual_agent import (
    MultilingualData, 
    get_voice_for_language, 
    get_voice_options_text,
    AVAILABLE_VOICES
)

def demonstrate_voice_selection():
    """Demonstrate different voice selection scenarios."""
    
    print("🎤 Multilingual Agent Voice Configuration Demo\n")
    
    # Create user data
    userdata = MultilingualData()
    
    # Scenario 1: Default voice selection
    print("📋 Scenario 1: Default Voice Selection")
    print("=" * 50)
    for language in ["english", "yoruba", "hausa", "igbo"]:
        voice = get_voice_for_language(language, userdata)
        print(f"{language.title()}: {voice.title()}")
    print()
    
    # Scenario 2: Gender preference
    print("📋 Scenario 2: Gender Preference (Feminine)")
    print("=" * 50)
    userdata.preferred_voice_gender = "feminine"
    for language in ["english", "yoruba", "hausa", "igbo"]:
        voice = get_voice_for_language(language, userdata)
        print(f"{language.title()}: {voice.title()}")
    print()
    
    # Scenario 3: Characteristic preference
    print("📋 Scenario 3: Characteristic Preference (Breezy)")
    print("=" * 50)
    userdata.preferred_voice_gender = None  # Reset gender
    userdata.preferred_voice_characteristic = "breezy"
    for language in ["english", "yoruba", "hausa", "igbo"]:
        voice = get_voice_for_language(language, userdata)
        print(f"{language.title()}: {voice.title()}")
    print()
    
    # Scenario 4: Combined preferences
    print("📋 Scenario 4: Combined Preferences (Masculine + Loud)")
    print("=" * 50)
    userdata.preferred_voice_gender = "masculine"
    userdata.preferred_voice_characteristic = "loud"
    for language in ["english", "yoruba", "hausa", "igbo"]:
        voice = get_voice_for_language(language, userdata)
        print(f"{language.title()}: {voice.title()}")
    print()
    
    # Scenario 5: Specific voice selection
    print("📋 Scenario 5: Specific Voice Selection")
    print("=" * 50)
    userdata.selected_voice = "sade"  # Override all other preferences
    for language in ["english", "yoruba", "hausa", "igbo"]:
        voice = get_voice_for_language(language, userdata)
        print(f"{language.title()}: {voice.title()}")
    print()
    
    # Show available voices for each language
    print("📋 Available Voices by Language")
    print("=" * 50)
    for language, voices in AVAILABLE_VOICES.items():
        print(f"\n{language.title()}:")
        print(get_voice_options_text(language))

def demonstrate_user_interactions():
    """Show example user interactions and expected voice selections."""
    
    print("\n🎯 Example User Interactions")
    print("=" * 50)
    
    examples = [
        {
            "user_input": "I want a female voice",
            "preference": "preferred_voice_gender = 'feminine'",
            "result": "Selects first available feminine voice for each language"
        },
        {
            "user_input": "I prefer a breezy voice",
            "preference": "preferred_voice_characteristic = 'breezy'",
            "result": "Selects Sade for Yoruba (only breezy voice available)"
        },
        {
            "user_input": "I want a calm male voice",
            "preference": "gender='masculine', characteristic='calm'",
            "result": "Selects masculine voices with 'calm' in description"
        },
        {
            "user_input": "Can I use Hasan's voice?",
            "preference": "selected_voice = 'hasan'",
            "result": "Uses Hasan for Hausa, falls back to default for other languages"
        },
        {
            "user_input": "I want a soft voice in English",
            "preference": "characteristic='soft' for English only",
            "result": "Selects Henry or Kani (soft voices) for English"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. User: \"{example['user_input']}\"")
        print(f"   → Sets: {example['preference']}")
        print(f"   → Result: {example['result']}")

if __name__ == "__main__":
    demonstrate_voice_selection()
    demonstrate_user_interactions()
    
    print("\n✨ Voice Configuration Features:")
    print("• Users can specify voice preferences by gender (masculine/feminine)")
    print("• Users can specify voice characteristics (breezy, calm, loud, soft, etc.)")
    print("• Users can select specific voices by name")
    print("• Preferences can be combined for more specific selection")
    print("• Voice preferences persist across language switches")
    print("• Users can change voice preferences during conversation")
    print("• Each language has multiple authentic voices to choose from")
    print("• Each language uses Spitch STT optimized for native language recognition")
    print("• Each language uses Spitch TTS with authentic pronunciation")
