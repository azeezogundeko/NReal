# Spitch STT/TTS Integration

## Overview

The multilingual agent has been updated to use **Spitch STT and TTS** for each language-specific agent, providing native language recognition and authentic pronunciation.

## Changes Made

### 1. STT Configuration

**Before:**
```python
# All agents used Deepgram STT
stt=deepgram.STT(model="nova-2")
```

**After:**
```python
# Each agent uses Spitch STT optimized for its language
stt=spitch.STT(language="en")  # English
stt=spitch.STT(language="yo")  # Yoruba  
stt=spitch.STT(language="ha")  # Hausa
stt=spitch.STT(language="ig")  # Igbo
```

### 2. TTS Configuration

**Before:**
```python
# Mixed TTS providers
tts=openai.TTS(voice="alloy", model="tts-1")
tts=openai.TTS(voice="shimmer", model="tts-1")
```

**After:**
```python
# All agents use Spitch TTS with language-specific voices
tts=spitch.TTS(language="en", voice=selected_voice)  # English
tts=spitch.TTS(language="yo", voice=selected_voice)  # Yoruba
tts=spitch.TTS(language="ha", voice=selected_voice)  # Hausa
tts=spitch.TTS(language="ig", voice=selected_voice)  # Igbo
```

### 3. LLM Configuration

**Updated to use Google Gemini:**
```python
llm=google.LLM(model="gemini-2.0-flash-001")
```

## Benefits

### 🎯 **Native Language Recognition**
- **English**: Optimized for American English pronunciation and accents
- **Yoruba**: Native Yoruba language recognition with proper tone handling
- **Hausa**: Authentic Hausa speech recognition with cultural context
- **Igbo**: Native Igbo language processing with tonal accuracy

### 🎤 **Authentic Voice Generation**
- **Language-Specific Voices**: Each language has multiple authentic voices
- **Cultural Pronunciation**: Proper pronunciation of names, places, and cultural terms
- **Tonal Accuracy**: Correct handling of tonal languages (Yoruba, Igbo)

### ⚡ **Performance Improvements**
- **Faster Recognition**: Spitch STT is optimized for each specific language
- **Better Accuracy**: Native language models provide higher accuracy
- **Reduced Latency**: Language-specific models process faster

## Environment Variables

```env
# Required for Spitch integration
SPITCH_API_KEY=your_spitch_api_key

# Required for Google Gemini LLM
GOOGLE_API_KEY=your_google_api_key
```

## Agent Configuration Summary

| Agent | STT | TTS | LLM |
|-------|-----|-----|-----|
| **WelcomeAgent** | `spitch.STT(language="en")` | `spitch.TTS(language="en", voice="kani")` | `google.LLM()` |
| **EnglishAgent** | `spitch.STT(language="en")` | `spitch.TTS(language="en", voice=selected)` | `google.LLM()` |
| **YorubaAgent** | `spitch.STT(language="yo")` | `spitch.TTS(language="yo", voice=selected)` | `google.LLM()` |
| **HausaAgent** | `spitch.STT(language="ha")` | `spitch.TTS(language="ha", voice=selected)` | `google.LLM()` |
| **IgboAgent** | `spitch.STT(language="ig")` | `spitch.TTS(language="ig", voice=selected)` | `google.LLM()` |

## Important Configuration Note

**Agent-Level STT/TTS Override**: Each agent now configures its own STT and TTS settings. The `AgentSession` no longer sets default STT/TTS to ensure that each language-specific agent uses the correct Spitch configuration for its language.

**Session Configuration:**
```python
session = AgentSession[MultilingualData](
    vad=ctx.proc.userdata["vad"],
    llm=google.LLM(model="gemini-2.0-flash-001", api_key=os.getenv("GEMINI_API_KEY")),
    # No STT/TTS set here - each agent handles its own
    userdata=MultilingualData(),
)
```

## Voice Selection Examples

### English
```python
# User selects "I want a female voice"
selected_voice = "lucy"  # or "lina", "kani"
tts=spitch.TTS(language="en", voice="lucy")
```

### Yoruba
```python
# User selects "I want a breezy voice"
selected_voice = "sade"  # Only breezy voice available
tts=spitch.TTS(language="yo", voice="sade")
```

### Hausa
```python
# User selects "I want Hasan's voice"
selected_voice = "hasan"
tts=spitch.TTS(language="ha", voice="hasan")
```

### Igbo
```python
# User selects "I want a soft male voice"
selected_voice = "ebuka"  # Soft male voice
tts=spitch.TTS(language="ig", voice="ebuka")
```

## Migration Notes

- **No breaking changes** to the user interface
- **Voice selection system** remains the same
- **Language switching** works identically
- **Function tools** unchanged
- **User preferences** persist across sessions

The integration is **seamless** and provides **significantly better** language recognition and voice quality for each supported language.
