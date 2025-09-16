# Deepgram Multilingual Agent

This agent provides high-quality multilingual support for English and Spanish using Deepgram's Aura-2 voices and Nova-3 speech recognition.

## Features

- **High-Quality Voices**: Uses Deepgram's Aura-2 voices for natural-sounding speech synthesis
- **Advanced Speech Recognition**: Uses Nova-3 model for accurate speech-to-text
- **Bilingual Support**: Seamless switching between English and Spanish
- **Voice Customization**: Choose from multiple voices with different characteristics, accents, and genders
- **Cultural Sensitivity**: Provides contextually appropriate responses in each language

## Available Voices

### Featured English Voices
- **Thalia** (feminine, American): Clear, Confident, Energetic, Enthusiastic
- **Andromeda** (feminine, American): Casual, Expressive, Comfortable
- **Helena** (feminine, American): Caring, Natural, Positive, Friendly, Raspy
- **Apollo** (masculine, American): Confident, Comfortable, Casual
- **Arcas** (masculine, American): Natural, Smooth, Clear, Comfortable
- **Aries** (masculine, American): Warm, Energetic, Caring

### Featured Spanish Voices
- **Celeste** (feminine, Colombian): Clear, Energetic, Positive, Friendly, Enthusiastic
- **Estrella** (feminine, Mexican): Approachable, Natural, Calm, Comfortable, Expressive
- **Nestor** (masculine, Peninsular): Calm, Professional, Approachable, Clear, Confident

### Codeswitching Voices
These voices can seamlessly switch between English and Spanish:
- Aquila, Carina, Diana, Javier, Selena

## Setup

1. **Install Dependencies**:
   ```bash
   pip install livekit-agents livekit-plugins-deepgram
   ```

2. **Environment Variables**:
   ```bash
   # Required
   DEEPGRAM_API_KEY=your_deepgram_api_key
   GEMINI_API_KEY=your_gemini_api_key
   
   # LiveKit Configuration
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   ```

3. **Run the Agent**:
   ```bash
   python deepgram_multilingual_agent.py
   ```

## Usage

### Starting a Conversation
The agent begins with a welcome message in both English and Spanish, allowing users to choose their preferred language and voice.

### Voice Selection
Users can specify their voice preferences:
- **Gender**: masculine or feminine
- **Accent**: American, British, Mexican, Colombian, Peninsular, etc.
- **Characteristics**: energetic, calm, professional, friendly, etc.
- **Specific Voice**: by name (e.g., "thalia", "celeste")

### Language Switching
Users can switch between English and Spanish at any time using natural language commands.

### Voice Configuration
Users can change their voice preferences during the conversation using the `configure_voice` function.

## Voice Configuration Examples

```python
# Get featured voices
from deepgram_voice_config import get_featured_voices
english_voices = get_featured_voices("english")
spanish_voices = get_featured_voices("spanish")

# Find voices by characteristics
from deepgram_voice_config import get_voices_by_characteristic
energetic_voices = get_voices_by_characteristic("energetic", "english")
professional_voices = get_voices_by_characteristic("professional", "spanish")

# Check codeswitching capability
from deepgram_voice_config import is_codeswitching_voice
can_switch = is_codeswitching_voice("aquila")  # True
```

## Deepgram Models Used

- **Speech-to-Text**: `nova-3` (supports multilingual recognition)
- **Text-to-Speech**: `aura-2-*` models (high-quality neural voices)

## Language Support

- **English**: Full support with multiple accents (American, British, Australian)
- **Spanish**: Full support with multiple accents (Mexican, Colombian, Peninsular, Latin American)

## Advanced Features

### Multilingual Recognition
The Nova-3 model can automatically detect and transcribe both English and Spanish in the same conversation.

### Voice Characteristics
Each voice has specific characteristics that make it suitable for different use cases:
- **Customer Service**: Professional, clear voices
- **Casual Chat**: Friendly, energetic voices
- **Storytelling**: Smooth, melodic voices
- **IVR**: Clear, confident voices

### Cultural Context
The agent provides culturally appropriate responses and can handle regional variations in both languages.

## Troubleshooting

### Common Issues

1. **Deepgram Plugin Not Available**:
   - Ensure `livekit-plugins-deepgram` is installed
   - Check your Deepgram API key

2. **Voice Not Found**:
   - Use the voice configuration helper to find available voices
   - Check voice names are spelled correctly

3. **Language Detection Issues**:
   - Nova-3 should automatically detect language
   - You can explicitly set language in STT configuration

### Performance Tips

- Use featured voices for best performance
- Nova-3 provides the highest accuracy for multilingual scenarios
- Aura-2 voices offer the best quality for speech synthesis

## Integration

This agent can be integrated with:
- LiveKit rooms for real-time communication
- Web applications for voice interfaces
- Customer service systems
- Educational platforms
- Translation services

## API Reference

### Main Classes
- `DeepgramWelcomeAgent`: Initial language selection
- `DeepgramEnglishAgent`: English language processing
- `DeepgramSpanishAgent`: Spanish language processing

### Key Functions
- `get_voice_for_language()`: Select appropriate voice based on preferences
- `language_selected()`: Handle language switching
- `configure_voice()`: Update voice preferences
- `translate_to_spanish()` / `translate_to_english()`: Translation functions

## Contributing

To add new voices or languages:
1. Update the `DEEPGRAM_VOICES` dictionary in the main agent file
2. Add corresponding entries in `deepgram_voice_config.py`
3. Update the language agents as needed
4. Test with the new configuration
