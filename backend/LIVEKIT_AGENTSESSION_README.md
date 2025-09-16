# LiveKit AgentSession Translation Implementation

## Overview

This document explains the updated LiveKit-based real-time translation system using `AgentSession` instead of the deprecated `VoicePipelineAgent`.

## Architecture

### New Implementation (AgentSession-based)

```
LiveKit Room → AgentSession → STT → Agent with Function Tools → TTS → Audio Output
```

### Key Components

1. **TranslationAgent (extends Agent)**: Custom agent with translation function tools
2. **AgentSession**: Manages the voice pipeline (STT, LLM, TTS, VAD)
3. **LiveKitTranslationService**: Service layer managing agents and sessions

## Files

### `backend/app/services/realtime/livekit_translation_agent.py`

#### TranslationAgent Class

```python
class TranslationAgent(Agent):
    """
    LiveKit Agent that handles real-time translation.
    
    Features:
    - Custom instructions for translation behavior
    - Function tool for translation logic
    - Participant language tracking
    """
```

**Key Methods:**
- `translate_speech()`: Function tool that performs translation
- `register_participant()`: Tracks participant languages
- `unregister_participant()`: Cleans up participant data

#### LiveKitTranslationService Class

```python
class LiveKitTranslationService:
    """
    Service for managing LiveKit-based translation agents with AgentSession.
    """
```

**Key Methods:**
- `create_agent()`: Creates TranslationAgent
- `start_agent()`: Creates and starts AgentSession
- `stop_agent()`: Cleans up session and agent

## How It Works

### 1. Agent Creation
```python
# Create agent with translation instructions
agent = TranslationAgent(user_profile)

# Agent is initialized with:
# - Translation instructions
# - Function tool for translate_speech
# - Participant language tracking
```

### 2. Session Setup
```python
# Create AgentSession with voice pipeline components
session = AgentSession(
    stt=deepgram.STT(),      # Speech-to-text
    llm=openai.LLM(),        # Language model
    tts=deepgram.TTS(),      # Text-to-speech
    vad=silero.VAD.load(),   # Voice activity detection
)

# Start session with room and agent
await session.start(ctx.room, agent)
```

### 3. Translation Flow

1. **Audio Input**: Participant speaks in their language
2. **STT**: Speech is transcribed to text
3. **Agent Processing**: Agent receives transcribed text
4. **Function Tool**: Agent calls `translate_speech()` function
5. **Translation**: Function performs translation using TranslationService
6. **TTS**: Translated text is converted to speech
7. **Audio Output**: User hears translated speech

## Function Tool Approach

Instead of custom LLM logic, we use LiveKit's function tools:

```python
@function_tool()
async def translate_speech(self, speech_text: str, speaker_identity: str = "unknown") -> str:
    """
    Translate speech from a participant into the user's native language.
    """
    # Translation logic here
    translated_text = await self.translation_service.translate_text(...)
    return translated_text
```

**Benefits:**
- More reliable than custom LLM responses
- Direct integration with existing TranslationService
- Better error handling
- Cleaner separation of concerns

## Configuration

### STT Configuration
```python
deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-general",
    language=lang_code,
    interim_results=True,
    punctuate=False,
    smart_format=False,
)
```

### TTS Configuration
```python
deepgram.TTS(
    api_key=settings.deepgram_api_key,
    model=user_profile.preferred_voice_avatar.model,
)
```

### VAD Configuration
```python
silero.VAD.load(
    min_speech_duration=0.1,
    min_silence_duration=0.5,
)
```

## Event Handling

### Participant Events
```python
@ctx.room.on("participant_connected")
def on_participant_connected(participant: rtc.RemoteParticipant):
    # Extract language from metadata
    # Register participant with agent
    
@ctx.room.on("participant_disconnected") 
def on_participant_disconnected(participant: rtc.RemoteParticipant):
    # Clean up participant data
```

## Advantages Over Previous Implementation

### ✅ Proper LiveKit Integration
- Uses official AgentSession API
- Follows LiveKit best practices
- Automatic audio pipeline management

### ✅ Function Tools
- Reliable translation triggering
- Direct service integration
- Better error handling

### ✅ Simplified Architecture
- No manual track subscription
- No custom audio processing
- LiveKit handles all audio routing

### ✅ Better Performance
- Optimized STT/TTS configurations
- Efficient VAD
- Reduced latency

## Testing

Run the test script:
```bash
cd backend
python test_livekit_translation.py
```

Expected output:
```
✅ Successfully created agent: TranslationAgent
✅ Agent user profile: test_user
✅ Agent language: en
✅ Agent has translate_speech tool: True
🎉 LiveKit Translation Agent test PASSED!
```

## Deployment

The updated worker entrypoint in `backend/agents/worker_entrypoint.py` now uses:

1. Creates user profile from job metadata
2. Creates TranslationAgent
3. Starts AgentSession
4. Handles participant events
5. Manages cleanup

## Expected Logs

With the new implementation, you should see:
```
INFO - TranslationAgent initialized for James
INFO - Created TranslationAgent for James  
INFO - Started AgentSession for James
INFO - Registered participant: John (es)
INFO - Translated: 'Hola' -> 'Hello' (es -> en)
```

## Migration Notes

### From VoicePipelineAgent to AgentSession

| Old | New |
|-----|-----|
| `VoicePipelineAgent` | `AgentSession` |
| Custom LLM class | Function tools |
| Manual audio processing | Automatic pipeline |
| Complex event handling | Simple room events |

### Breaking Changes
- `VoicePipelineAgent` is no longer used
- Custom `TranslationLLM` replaced with function tools
- Simplified service interface
- Updated worker entrypoint

This implementation provides a robust, maintainable, and efficient real-time translation system using LiveKit's latest APIs.
