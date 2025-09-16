# Modern Multilingual Agent

This is a clean, modern implementation of a multilingual AI agent using the LiveKit Agents SDK, following the multi-agent pattern from the LiveKit blog.

## Features

✅ **Multi-Agent Architecture**: Each language has its own dedicated agent  
✅ **Seamless Language Switching**: Users can switch between languages mid-conversation  
✅ **Customizable Voice Selection**: Users can choose voices by gender and characteristics  
✅ **Language-Specific Voices**: Each language has multiple authentic voices to choose from  
✅ **Native Language STT**: Each agent uses Spitch STT optimized for its specific language  
✅ **Cultural Context**: Each agent understands cultural nuances of its language  
✅ **Function Tools**: LLM can call functions to switch languages, configure voices, or end conversations  
✅ **Shared State**: User information and voice preferences persist across language switches  
✅ **Metrics & Logging**: Built-in usage tracking and performance monitoring  

## Supported Languages & Voices

### English
- **John** (Masculine): Loud and clear voice
- **Lucy** (Feminine): Very clear voice
- **Lina** (Feminine): Clear, loud voice
- **Jude** (Masculine): Deep voice, smooth
- **Henry** (Masculine): Soft voice, cool tone
- **Kani** (Feminine): Soft voice, cool tone

### Yoruba
- **Sade** (Feminine): Energetic, but breezy
- **Funmi** (Feminine): Calm, can sometimes be fun
- **Segun** (Masculine): Vibrant, yet cool
- **Femi** (Masculine): Really fun guy to interact with

### Hausa
- **Hasan** (Masculine): Loud and clear voice
- **Amina** (Feminine): A bit quiet and soft
- **Zainab** (Feminine): Clear, loud voice
- **Aliyu** (Masculine): Soft voice, cool tone

### Igbo
- **Obinna** (Masculine): Loud and clear voice
- **Ngozi** (Feminine): A bit quiet and soft
- **Amara** (Feminine): Clear, loud voice
- **Ebuka** (Masculine): Soft voice, cool tone

## Architecture

### Agent Classes

1. **WelcomeAgent**: Initial greeting and language selection
2. **EnglishAgent**: English language assistance with Spitch STT/TTS
3. **YorubaAgent**: Yoruba language assistance with Spitch STT/TTS
4. **HausaAgent**: Hausa language assistance with Spitch STT/TTS
5. **IgboAgent**: Igbo language assistance with Spitch STT/TTS

### Key Features

- **Function Tools**: Each agent can call `switch_language()`, `configure_voice()`, and `end_conversation()`
- **Language-Specific STT**: Each agent uses Spitch STT optimized for its language:
  - English: `spitch.STT(language="en")`
  - Yoruba: `spitch.STT(language="yo")`
  - Hausa: `spitch.STT(language="ha")`
  - Igbo: `spitch.STT(language="ig")`
- **Customizable TTS**: Each language uses Spitch TTS with user-selected voices
- **Agent-Level Override**: Each agent configures its own STT/TTS (no session-level defaults)
- **Shared State**: `MultilingualData` dataclass holds user info and voice preferences across agents
- **Chat Context**: Conversation history is preserved when switching languages

## Usage

### Running the Agent

```bash
cd backend/agents
python multilingual_agent.py
```

### Environment Variables

Make sure you have these in your `.env` file:

```env
# LLM Configuration
GOOGLE_API_KEY=your_google_api_key

# STT/TTS Configuration (Spitch)
SPITCH_API_KEY=your_spitch_api_key

# LiveKit Configuration
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
```

### User Flow

1. **Welcome**: Agent greets in all four languages
2. **Language & Voice Selection**: User chooses preferred language and voice preferences
3. **Conversation**: Agent responds in selected language with chosen voice
4. **Voice Configuration**: User can change voice preferences during conversation
5. **Language Switch**: User can switch languages anytime (voice preferences persist)
6. **End**: User can end conversation naturally

### Voice Selection Options

Users can specify their voice preferences in multiple ways:

**By Gender:**
- "I want a female voice" → Selects feminine voices
- "I prefer a male voice" → Selects masculine voices

**By Characteristics:**
- "I want a breezy voice" → Selects voices with "breezy" in description
- "I prefer a calm voice" → Selects voices with "calm" in description
- "I want a loud voice" → Selects voices with "loud" in description
- "I prefer a soft voice" → Selects voices with "soft" in description

**By Specific Name:**
- "I want to use Sade's voice" → Directly selects Sade voice
- "Can I use Hasan?" → Directly selects Hasan voice

**Combined Preferences:**
- "I want a breezy female voice" → Selects feminine voices with "breezy" characteristic
- "I prefer a calm male voice" → Selects masculine voices with "calm" characteristic

### Example Interactions

**Welcome Message**: "Hello! Sannu! Ndewo! E ku aaro! Choose your language and voice preference!"

**Voice Selection Examples**:
- User: "I want to speak English with a female voice"
- Agent: "Switching to English mode with Lucy voice. How can I help you today?"

- User: "I prefer a breezy voice in Yoruba"
- Agent: "Switching to Yoruba mode with Sade voice. Bawo ni mo se le ran yin lowo?"

- User: "Can I use Hasan's voice for Hausa?"
- Agent: "Switching to Hausa mode with Hasan voice. Yaya zan iya taimaka maku?"

**Voice Change During Conversation**:
- User: "Can you switch to a softer voice?"
- Agent: "Voice updated to Amina!" (if in Hausa) or appropriate soft voice for current language

## Advantages Over Workflow Approach

### ✅ **Cleaner Code**
- No complex workflow state management
- No manual session recreation
- No transition evaluation logic

### ✅ **Better Performance** 
- No session recreation overhead
- Direct agent switching
- Preserved conversation context

### ✅ **More Maintainable**
- Each language is a separate class
- Clear separation of concerns
- Easy to add new languages

### ✅ **Native LiveKit Features**
- Built-in function tools
- Automatic metrics collection
- Proper error handling
- Room management

### ✅ **Flexible Configuration**
- Easy to change TTS voices per language
- Simple to modify agent instructions
- Straightforward to add new features

## Adding New Languages

To add a new language (e.g., French):

1. **Create Agent Class**:
```python
class FrenchAgent(Agent):
    def __init__(self, user_name=None, user_location=None, *, chat_ctx=None):
        super().__init__(
            instructions="French instructions here...",
            tts=openai.TTS(voice="fable", model="tts-1"),
            chat_ctx=chat_ctx,
        )
```

2. **Add to WelcomeAgent**:
```python
elif language.lower() in ["french", "fr"]:
    agent = FrenchAgent(context.userdata.user_name, context.userdata.user_location)
```

3. **Add Switch Logic** to all other agents

## Comparison with Workflow Agent

| Feature | Workflow Agent | Modern Agent |
|---------|---------------|--------------|
| Code Lines | ~940 | ~650 |
| Complexity | High | Low |
| Session Management | Manual | Automatic |
| Language Switching | Session Recreation | Direct Agent Switch |
| Voice Selection | Fixed per node | Dynamic user choice |
| STT Configuration | Deepgram only | Spitch per language |
| TTS Configuration | OpenAI only | Spitch per language |
| Voice Configuration | Not available | Real-time voice changes |
| Maintainability | Difficult | Easy |
| Performance | Slower | Faster |
| Error Handling | Manual | Built-in |

This modern approach is **significantly cleaner, faster, and more maintainable** than the workflow-based implementation.
