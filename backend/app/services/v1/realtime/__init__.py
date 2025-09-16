"""
Real-time translation services for ultra-fast simultaneous interpretation.

This package provides optimized components for 2-user translation with 500ms max delay:
- RealTimeTranslationBuffer: Smart buffering with 500ms max delay
- FastSTTService: Optimized STT with interim results and minimal processing
- CleanAudioRouter: Audio routing to prevent pollution
- RealtimeTranslationAgent: Integrated agent for ultra-fast translation
"""

from .translation_buffer import RealTimeTranslationBuffer, TranslationResult
from .fast_stt import FastSTTService, FastSTTConfig, create_fast_stt_service
from .audio_router import CleanAudioRouter
from .realtime_translation_agent import (
    RealtimeTranslationAgent, 
    RealtimeTranslationService, 
    RealtimeTranslationConfig
)

__all__ = [
    "RealTimeTranslationBuffer",
    "TranslationResult", 
    "FastSTTService",
    "FastSTTConfig",
    "create_fast_stt_service",
    "CleanAudioRouter",
    "RealtimeTranslationAgent",
    "RealtimeTranslationService", 
    "RealtimeTranslationConfig",
]



