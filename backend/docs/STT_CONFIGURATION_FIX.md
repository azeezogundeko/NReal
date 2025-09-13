# STT Configuration Fix

## Issue Fixed

**Error:** `RuntimeError: The STT (livekit.plugins.spitch.stt.STT) does not support streaming, add a VAD to the AgentTask/VoiceAgent to enable streaming Or manually wrap your STT in a stt.StreamAdapter`

## Root Cause

The Spitch STT service doesn't support streaming mode natively and requires either:
1. A VAD (Voice Activity Detection) system
2. Wrapping in a `stt.StreamAdapter`

## Solution Applied

### 1. **Primary Fix: Switch to Deepgram STT**
```python
# Deepgram STT supports streaming natively
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-general",
    language="en",
    interim_results=False,
    punctuate=True,
)
```

### 2. **Fallback: OpenAI STT**
```python
# If Deepgram fails, fallback to OpenAI Whisper
stt_instance = openai.STT(
    api_key=settings.openai_api_key,
    model="whisper-1",
    language="en",
)
```

### 3. **Alternative: Spitch STT with StreamAdapter**
```python
# If you want to use Spitch STT, wrap it in StreamAdapter
vad_for_spitch = silero.VAD.load()
stt_instance = stt.StreamAdapter(
    spitch.STT(
        api_key=settings.spitch_api_key,
        model="spitch-stt",
    ),
    vad=vad_for_spitch  # Required for non-streaming STT
)
```

## Configuration Options

### Environment Variables Required

```env
# Primary STT (Deepgram)
DEEPGRAM_API_KEY=your_deepgram_key

# Fallback STT (OpenAI)
OPENAI_API_KEY=your_openai_key

# Alternative STT (Spitch) - if using StreamAdapter
SPITCH_API_KEY=your_spitch_key
```

### STT Service Comparison

| Service | Streaming Support | Setup Complexity | Performance |
|---------|------------------|------------------|-------------|
| **Deepgram** | ✅ Native | 🟢 Simple | 🟢 Fast |
| **OpenAI Whisper** | ✅ Native | 🟢 Simple | 🟡 Medium |
| **Spitch** | ❌ Requires Adapter | 🔴 Complex | 🟡 Medium |

## Benefits of the Fix

### ✅ **Immediate Benefits**
- **No more STT streaming errors**
- **Better speech recognition accuracy** (Deepgram nova-2-general)
- **Robust fallback system** (Deepgram → OpenAI → Error)
- **Improved VAD integration**

### 🚀 **Performance Improvements**
- **Lower latency** with native streaming support
- **Better real-time processing** for voice translation
- **Reduced error rates** in speech detection

### 🛡️ **Reliability**
- **Multiple STT providers** for redundancy
- **Graceful error handling** with informative logging
- **Automatic fallback** if primary service fails

## Monitoring & Debugging

### Log Messages to Watch For

```
✅ SUCCESS:
"Using Deepgram STT for speech recognition"
"Silero VAD loaded successfully for speech detection"

⚠️ WARNINGS:
"Deepgram STT failed to initialize: [error]"
"Using OpenAI STT as fallback for speech recognition"
"VAD not available, proceeding without: [error]"

❌ ERRORS:
"All STT options failed: Deepgram=[error], OpenAI=[error]"
"No working STT service available"
```

### Testing STT Configuration

```bash
# Test the agent with new STT configuration
cd backend
python -m agents.worker_entrypoint

# Check logs for STT initialization
tail -f logs/agent.log | grep -i "stt\|speech"
```

## Advanced Configuration

### Custom STT Settings

```python
# Fine-tune Deepgram STT for your use case
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-general",          # Best general model
    language="en",                   # Primary language
    interim_results=False,           # Only final results
    punctuate=True,                  # Add punctuation
    diarize=False,                   # Speaker identification
    smart_format=True,               # Format numbers/dates
    utterance_end_ms=1000,          # End of speech detection
)
```

### Multi-Language Support

```python
# Configure STT for multiple languages
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-general",
    language="auto",                 # Auto-detect language
    detect_language=True,            # Enable language detection
)
```

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Check `DEEPGRAM_API_KEY` in environment variables
   - Verify API key is valid and has credits

2. **"Model not available"**
   - Use `nova-2-general` for best compatibility
   - Check Deepgram documentation for available models

3. **"VAD loading failed"**
   - This is non-critical, STT will work without VAD
   - Ensure sufficient memory for VAD model loading

### Performance Tuning

```python
# For faster response (lower accuracy)
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-phonecall",        # Optimized for phone calls
    interim_results=True,            # Get partial results
)

# For higher accuracy (slower response)
stt_instance = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2-meeting",          # Optimized for meetings
    interim_results=False,           # Only final results
    smart_format=True,               # Enhanced formatting
)
```

The STT configuration is now robust and should handle all speech recognition needs for the translation service! 🎉
