# Real-Time Voice Translation Architecture

## Overview

This document explains how the LiveKit-based translation system handles simultaneous real-time voice translation for multiple participants in a meeting room. The system uses a sophisticated event-driven architecture with a single AgentSession per user to manage concurrent speech processing.

## Core Architecture

### 1. Single AgentSession Per User Pattern

Unlike naive implementations that create separate sessions for each participant, this system uses **one AgentSession per user** that handles all participants simultaneously:

```python
class UserTranslationAgent:
    def __init__(self, user_profile: UserLanguageProfile):
        self.session: Optional[AgentSession] = None  # Single session for this user
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        self.active_participants: Set[str] = set()
```

**Why this pattern works:**
- Efficient resource utilization (one session vs N sessions)
- Automatic participant management by LiveKit
- Simplified state management
- Better performance for multi-participant scenarios

### 2. Speech Processing Pipeline

Each user gets a complete STT → Translation → TTS pipeline:

```
Participant Speech → STT → Translation → TTS → User Hearing
     ↓              ↓         ↓          ↓         ↓
   Audio         Text    Translated    Audio   Translated
   Stream     Transcript    Text      Stream     Speech
```

#### Pipeline Components:

**Speech-to-Text (STT):**
```python
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-general",
    language="en",  # Adaptive per participant
    interim_results=False,
    punctuate=True,
)
```

**Translation Service:**
```python
translated_text = await self.translation_service.translate_text(
    user_message,
    participant_lang,
    self.user_profile.native_language,
    self.user_profile.translation_preferences
)
```

**Text-to-Speech (TTS):**
```python
self.tts = elevenlabs.TTS(
    api_key=settings.elevenlabs_api_key,
    voice=avatar.voice_id,
    model="eleven_turbo_v2_5",
)
```

## Concurrent Processing Flow

### 1. Room Connection & Initialization

When a user joins a room:

```python
async def start(self, ctx: JobContext):
    # 1. Connect to room with audio subscription
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 2. Register existing participants
    for participant in self.room.remote_participants.values():
        if participant.identity != self.user_profile.user_identity:
            self._register_participant(participant)

    # 3. Create single AgentSession for this user
    await self._create_agent_session(ctx)
```

### 2. Participant Registration

Each participant is registered with their language preference:

```python
def _register_participant(self, participant: rtc.RemoteParticipant):
    participant_lang = self._get_participant_language(participant)
    self.participant_languages[participant.identity] = participant_lang
    self.active_participants.add(participant_identity)
```

Language is extracted from participant metadata:
```python
def _get_participant_language(self, participant: rtc.RemoteParticipant) -> SupportedLanguage:
    try:
        metadata = json.loads(participant.metadata or "{}")
        lang = metadata.get("language", "en")
        return SupportedLanguage(lang)
    except:
        return SupportedLanguage.ENGLISH
```

### 3. AgentSession Creation

The core processing session is created with all components:

```python
async def _create_agent_session(self, ctx: JobContext):
    # Create STT, LLM, TTS components
    stt_instance = deepgram.STT(...)
    translation_llm = self._create_multi_language_llm()

    # Voice Activity Detection (with fallback)
    try:
        vad = silero.VAD.load()
    except Exception as e:
        logging.warning(f"VAD not available: {e}")
        vad = None

    # Create the main session
    self.session = AgentSession(
        vad=vad,
        stt=stt_instance,
        llm=translation_llm,
        tts=self.tts,
        chat_ctx=llm.ChatContext(),
    )

    # Set up speech event handler
    @self.session.on("user_speech_committed")
    def on_user_speech_committed(ev):
        asyncio.create_task(self._handle_user_speech(ev))

    # Start the session
    await self.session.start(room=self.room)
```

## Simultaneous Speech Handling

### Event-Driven Processing

The system uses LiveKit's event system to handle multiple concurrent speakers:

```python
@self.session.on("user_speech_committed")
def on_user_speech_committed(ev):
    """Handle speech from any participant"""
    asyncio.create_task(self._handle_user_speech(ev))
```

### Speech Processing Logic

When speech is detected from any participant:

```python
async def _handle_user_speech(self, ev):
    try:
        user_message = ev.user_transcript
        participant_identity = getattr(ev, 'participant_identity', None)

        # 1. Identify speaker
        if participant_identity == self.user_profile.user_identity:
            return  # Don't translate own speech

        # 2. Get speaker's language
        participant_lang = self.participant_languages.get(
            participant_identity,
            SupportedLanguage.ENGLISH
        )

        # 3. Skip if same language
        if participant_lang == self.user_profile.native_language:
            return

        # 4. Translate the speech
        translated_text = await self.translation_service.translate_text(
            user_message,
            participant_lang,
            self.user_profile.native_language,
            self.user_profile.translation_preferences
        )

        # 5. Synthesize and play translated speech
        if translated_text and translated_text != user_message:
            await self.session.say(translated_text)

    except Exception as e:
        logging.error(f"Error handling user speech: {e}")
```

## Concurrency Management

### Async Task Creation

Each speech event creates a separate async task:

```python
@self.session.on("user_speech_committed")
def on_user_speech_committed(ev):
    asyncio.create_task(self._handle_user_speech(ev))
```

This ensures:
- **Non-blocking processing** - Multiple speakers can be processed simultaneously
- **Independent error handling** - One failed translation doesn't affect others
- **Resource efficiency** - Tasks are created and destroyed as needed

### Task Lifecycle

```
Speech Event → Async Task Created → Translation → TTS → Task Complete
Speech Event → Async Task Created → Translation → TTS → Task Complete
Speech Event → Async Task Created → Translation → TTS → Task Complete
```

### Error Isolation

Each speech processing task is isolated:

```python
try:
    translated_text = await self.translation_service.translate_text(...)
    if translated_text:
        await self.session.say(translated_text)
except Exception as e:
    logging.error(f"Error processing speech: {e}")
    # Other concurrent tasks continue unaffected
```

## Dynamic Participant Management

### Participant Join/Leave Handling

The system dynamically manages participants as they join and leave:

```python
async def _on_participant_connected(self, participant: rtc.RemoteParticipant):
    """Handle new participant joining"""
    if participant.identity == self.user_profile.user_identity:
        return

    logging.info(f"New participant {participant.identity} connected")
    self._register_participant(participant)

async def _on_participant_disconnected(self, participant: rtc.RemoteParticipant):
    """Handle participant disconnecting"""
    if participant.identity in self.active_participants:
        self.active_participants.remove(participant.identity)
        self.participant_languages.pop(participant.identity, None)
        logging.info(f"Participant {participant.identity} disconnected")
```

### Real-time Language Updates

Participant languages can be updated dynamically through metadata changes, allowing for:
- Language preference changes during calls
- Automatic language detection improvements
- Fallback language handling

## Performance Optimizations

### 1. Voice Activity Detection (VAD)

```python
try:
    vad = silero.VAD.load()
except Exception as e:
    logging.warning(f"VAD not available: {e}")
    vad = None
```

**Benefits:**
- Reduces false positives from background noise
- Improves speech segmentation
- Lowers API costs by reducing unnecessary transcriptions

### 2. Efficient Resource Management

- **Single AgentSession** reduces memory footprint
- **Async task cleanup** prevents memory leaks
- **Connection pooling** for API services
- **Graceful fallbacks** for missing components

### 3. Smart Translation Skipping

```python
# Skip translation if same language
if participant_lang == self.user_profile.native_language:
    logging.debug(f"Skipping translation (same language)")
    return
```

**Benefits:**
- Reduces unnecessary API calls
- Faster response times for same-language conversations
- Lower costs for monolingual meetings

## Error Handling & Resilience

### Component Failure Handling

```python
try:
    vad = silero.VAD.load()
except Exception as e:
    logging.warning(f"VAD not available: {e}")
    vad = None
```

### Service Degradation

The system gracefully degrades when components fail:
- **VAD failure** → Continues without voice activity detection
- **STT failure** → Logs error, continues processing other speech
- **Translation failure** → Falls back to original language
- **TTS failure** → Logs error, doesn't break the session

### Logging & Monitoring

Comprehensive logging for debugging:
```python
logging.info(f"Processing speech from {participant_identity}")
logging.info(f"Translated: {translated_text[:100]}...")
logging.error(f"Error processing speech: {e}")
```

## Scalability Considerations

### Per-User Architecture Benefits

1. **Horizontal Scaling**: Each user gets independent processing
2. **Resource Isolation**: One user's failures don't affect others
3. **Custom Preferences**: Each user can have different settings
4. **Load Distribution**: Different users can use different AI providers

### Multi-Participant Room Handling

For rooms with many participants:
- Single AgentSession handles all participants efficiently
- Async processing prevents blocking
- Resource usage scales with active speakers, not total participants
- Memory usage remains constant regardless of room size

## Real-World Usage Example

### Scenario: 5-Person International Meeting

```
Room: "Global Team Standup"
Participants:
- Alice (English) - Host/User Agent
- Bob (Spanish) → English translation
- Carol (French) → English translation
- David (German) → English translation
- Eve (English) → No translation needed

Flow:
1. Alice speaks English → No translation
2. Bob speaks Spanish → Translated to English for Alice
3. Carol speaks French → Translated to English for Alice
4. David speaks German → Translated to English for Alice
5. Eve speaks English → No translation
```

**Concurrent Processing:**
- All translations happen simultaneously via async tasks
- Alice hears all translations mixed appropriately
- No blocking or queuing delays
- Real-time experience maintained

## Configuration & Customization

### Voice Avatar Selection

Each user can customize their translation voice:

```python
@dataclass
class VoiceAvatar:
    voice_id: str
    provider: str  # "elevenlabs", "openai", "google"
    name: str
    gender: str
    accent: str
    description: str
```

### Translation Preferences

```python
translation_preferences: Dict[str, bool] = {
    "formal_tone": False,
    "preserve_emotion": True
}
```

## Monitoring & Debugging

### Key Metrics to Monitor

1. **Translation Latency**: Time from speech to translated audio
2. **Concurrent Tasks**: Number of active translation tasks
3. **Error Rates**: Per component (STT, Translation, TTS)
4. **Resource Usage**: Memory and CPU per user agent
5. **Participant Count**: Active participants per room

### Logging Levels

```python
logging.info(f"AgentSession created for user {user_identity}")
logging.debug(f"Skipping translation (same language)")
logging.error(f"Translation service error: {e}")
```

## Conclusion

This architecture provides a robust, scalable solution for real-time voice translation that can handle multiple concurrent speakers efficiently. The key innovations are:

1. **Single AgentSession per user** for optimal resource usage
2. **Async task-based processing** for concurrent speech handling
3. **Event-driven architecture** for real-time responsiveness
4. **Graceful error handling** for production reliability
5. **Dynamic participant management** for changing room conditions

The system scales horizontally and can handle international meetings with participants speaking different languages simultaneously, providing each user with real-time translations in their preferred language.
