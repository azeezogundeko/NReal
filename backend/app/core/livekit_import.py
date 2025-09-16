#!/usr/bin/env python3
"""
Common LiveKit plugin imports and configurations.
This file centralizes all LiveKit plugin imports to avoid duplication.
"""

import logging

logger = logging.getLogger(__name__)

# Import plugins with fallbacks for problematic dependencies
try:
    from livekit.plugins import openai, deepgram, cartesia, silero
    SILERO_AVAILABLE = True
    PLUGINS_AVAILABLE = True
    logger.info("All LiveKit plugins loaded successfully")
except ImportError as e:
    if "onnxruntime" in str(e):
        # Silero VAD requires onnxruntime which can have DLL issues on Windows
        try:
            from livekit.plugins import openai, deepgram, cartesia, elevenlabs, spitch
            SILERO_AVAILABLE = False
            PLUGINS_AVAILABLE = True
            logger.warning("Silero VAD not available due to onnxruntime DLL issues. Using fallback VAD.")
        except ImportError:
            PLUGINS_AVAILABLE = False
            SILERO_AVAILABLE = False
            logger.error("Basic LiveKit plugins not available")
    else:
        PLUGINS_AVAILABLE = False
        SILERO_AVAILABLE = False
        logger.error(f"LiveKit plugins not available: {e}")

# Import groq separately to avoid plugin registration issues
if PLUGINS_AVAILABLE:
    try:
        from livekit.plugins import groq, elevenlabs
        GROQ_AVAILABLE = True
        logger.info("Groq plugin loaded successfully")
    except Exception as e:
        GROQ_AVAILABLE = False
        logger.warning(f"Groq not available: {e}")
else:
    GROQ_AVAILABLE = False
    logger.warning("Groq not available due to missing base plugins")

# Define fallback classes if plugins not available
if not PLUGINS_AVAILABLE:
    logger.warning("Using fallback dummy implementations for LiveKit plugins")

    class DummyLLM:
        def __init__(self, **kwargs):
            pass
        async def achat(self, **kwargs):
            return type('Response', (), {'message': type('Message', (), {'content': 'Plugin not available'})()})()

    class DummyTTS:
        def __init__(self, **kwargs):
            pass

    class DummySTT:
        def __init__(self, **kwargs):
            pass

    # Create dummy modules
    openai = type('module', (), {'LLM': DummyLLM, 'TTS': DummyTTS, 'STT': DummySTT})()
    deepgram = type('module', (), {'TTS': DummyTTS, 'STT': DummySTT})()
    cartesia = type('module', (), {'TTS': DummyTTS})()
    groq = type('module', (), {'LLM': DummyLLM, 'STT': DummySTT})()

# Export all plugins and availability flags
__all__ = [
    'openai',
    'deepgram',
    'cartesia',
    'groq',
    'SILERO_AVAILABLE',
    'PLUGINS_AVAILABLE',
    'GROQ_AVAILABLE'
]
