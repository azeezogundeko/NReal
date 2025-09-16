"""
Optimized STT configuration for ultra-fast real-time translation.
Configured for maximum speed with minimal processing overhead.
"""
import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import uuid

from livekit.agents import stt
from livekit.plugins import deepgram, openai
from app.core.config import get_settings
from app.models.v1.domain.profiles import SupportedLanguage


class STTProvider(Enum):
    DEEPGRAM = "deepgram"
    OPENAI = "openai"


@dataclass
class FastSTTConfig:
    """Configuration for ultra-fast STT."""
    provider: STTProvider = STTProvider.DEEPGRAM
    model: str = "nova-2-general"
    language: str = "en-US"
    interim_results: bool = True
    utterance_end_ms: int = 500  # Very fast utterance detection
    punctuate: bool = False  # Skip punctuation for speed
    smart_format: bool = False  # Skip formatting for speed
    profanity_filter: bool = False  # Skip filtering for speed
    redact: bool = False  # Skip redaction for speed
    diarize: bool = False  # Skip diarization for speed
    multichannel: bool = False  # Single channel for speed
    alternatives: int = 0  # No alternatives for speed
    tier: str = "enhanced"  # Use enhanced tier for speed
    detect_language: bool = False  # Disable auto-detection for speed


class FastSTTService:
    """
    Ultra-fast STT service optimized for real-time simultaneous interpretation.
    
    Features:
    - Optimized for speed over accuracy
    - Interim results processing
    - Language-specific optimization
    - Minimal processing overhead
    """
    
    def __init__(self, config: Optional[FastSTTConfig] = None):
        self.config = config or FastSTTConfig()
        self.settings = get_settings()
        self._stt_instances: Dict[str, stt.STT] = {}
        self._language_configs: Dict[SupportedLanguage, FastSTTConfig] = {}
        
        # Initialize language-specific configs
        self._setup_language_configs()
        
        logging.info(f"FastSTTService initialized with {self.config.provider.value} provider")
    
    def _setup_language_configs(self):
        """Setup optimized configs for different languages."""
        # English - fastest configuration
        self._language_configs[SupportedLanguage.ENGLISH] = FastSTTConfig(
            provider=STTProvider.DEEPGRAM,
            model="nova-2-general",
            language="en-US",
            interim_results=True,
            utterance_end_ms=500,
            punctuate=False,
            smart_format=False,
            profanity_filter=False,
            redact=False,
            diarize=False,
            tier="enhanced"
        )
        
        # Spanish - optimized for Spanish
        self._language_configs[SupportedLanguage.SPANISH] = FastSTTConfig(
            provider=STTProvider.DEEPGRAM,
            model="nova-2-general",
            language="es-US",  # Updated to use proper locale format
            interim_results=True,
            utterance_end_ms=500,
            punctuate=False,
            smart_format=False,
            profanity_filter=False,
            redact=False,
            diarize=False,
            tier="enhanced"
        )
        
        # French - optimized for French
        self._language_configs[SupportedLanguage.FRENCH] = FastSTTConfig(
            provider=STTProvider.DEEPGRAM,
            model="nova-2-general",
            language="fr-FR",  # Updated to use proper locale format
            interim_results=True,
            utterance_end_ms=500,
            punctuate=False,
            smart_format=False,
            profanity_filter=False,
            redact=False,
            diarize=False,
            tier="enhanced"
        )
        
        # Note: German removed as it's not in SupportedLanguage enum
        # If German support is needed, add SupportedLanguage.GERMAN = "de" to profiles.py first
    
    def get_stt_instance(self, language: SupportedLanguage, participant_id: Optional[str] = None) -> stt.STT:
        """
        Get optimized STT instance for a specific language.
        
        Args:
            language: Target language for STT
            participant_id: Optional participant ID for caching
            
        Returns:
            Configured STT instance
        """
        cache_key = f"{language.value}_{participant_id or 'default'}"
        
        if cache_key in self._stt_instances:
            return self._stt_instances[cache_key]
        
        config = self._language_configs.get(language, self.config)
        stt_instance = self._create_stt_instance(config)
        
        # Cache the instance
        self._stt_instances[cache_key] = stt_instance
        
        logging.debug(f"Created STT instance for {language.value} (participant: {participant_id})")
        return stt_instance
    
    def _create_stt_instance(self, config: FastSTTConfig) -> stt.STT:
        """Create STT instance with optimized configuration."""
        if config.provider == STTProvider.DEEPGRAM:
            return self._create_deepgram_stt(config)
        elif config.provider == STTProvider.OPENAI:
            return self._create_openai_stt(config)
        else:
            raise ValueError(f"Unsupported STT provider: {config.provider}")
    
    def _create_deepgram_stt(self, config: FastSTTConfig) -> deepgram.STT:
        """Create optimized Deepgram STT instance."""
        # Use only supported parameters for LiveKit's deepgram.STT wrapper
        stt_params = {
            "api_key": self.settings.deepgram_api_key,
            "model": config.model,
            "language": config.language,
            "interim_results": config.interim_results,
        }
        
        # Add optional parameters that are commonly supported
        if hasattr(config, 'punctuate'):
            stt_params["punctuate"] = config.punctuate
        if hasattr(config, 'smart_format'):
            stt_params["smart_format"] = config.smart_format
            
        return deepgram.STT(**stt_params)
    
    def _create_openai_stt(self, config: FastSTTConfig) -> openai.STT:
        """Create OpenAI STT instance (fallback)."""
        return openai.STT(
            api_key=self.settings.openai_api_key,
            model="whisper-1",  # Fastest Whisper model
            language=config.language,
        )
    
    def get_optimized_config_for_pair(self, 
                                     language_a: SupportedLanguage, 
                                     language_b: SupportedLanguage) -> Dict[str, FastSTTConfig]:
        """
        Get optimized STT configs for a 2-user translation pair.
        
        Args:
            language_a: First user's language
            language_b: Second user's language
            
        Returns:
            Dictionary mapping language to optimized config
        """
        configs = {}
        
        # Get configs for both languages
        config_a = self._language_configs.get(language_a, self.config)
        config_b = self._language_configs.get(language_b, self.config)
        
        # For 2-user translation, we can make additional optimizations
        if language_a == SupportedLanguage.ENGLISH and language_b == SupportedLanguage.SPANISH:
            # English-Spanish pair - most common, highly optimized
            config_a.utterance_end_ms = 400  # Even faster for English
            config_b.utterance_end_ms = 450  # Slightly faster for Spanish
        elif language_a == SupportedLanguage.SPANISH and language_b == SupportedLanguage.ENGLISH:
            # Spanish-English pair
            config_a.utterance_end_ms = 450
            config_b.utterance_end_ms = 400
        
        configs[language_a.value] = config_a
        configs[language_b.value] = config_b
        
        return configs
    
    def create_streaming_stt(self, 
                           language: SupportedLanguage,
                           participant_id: str,
                           on_interim_transcript: Optional[Callable] = None,
                           on_final_transcript: Optional[Callable] = None) -> 'StreamingSTTWrapper':
        """
        Create a streaming STT wrapper with callbacks.
        
        Args:
            language: Language for STT
            participant_id: Participant identifier
            on_interim_transcript: Callback for interim results
            on_final_transcript: Callback for final results
            
        Returns:
            Streaming STT wrapper
        """
        stt_instance = self.get_stt_instance(language, participant_id)
        
        return StreamingSTTWrapper(
            stt_instance=stt_instance,
            participant_id=participant_id,
            language=language,
            on_interim_transcript=on_interim_transcript,
            on_final_transcript=on_final_transcript
        )


class StreamingSTTWrapper:
    """
    Wrapper for STT instances to handle streaming with callbacks.
    """
    
    def __init__(self,
                 stt_instance: stt.STT,
                 participant_id: str,
                 language: SupportedLanguage,
                 on_interim_transcript: Optional[Callable] = None,
                 on_final_transcript: Optional[Callable] = None):
        self.stt = stt_instance
        self.participant_id = participant_id
        self.language = language
        self.on_interim_transcript = on_interim_transcript
        self.on_final_transcript = on_final_transcript
        
        # Track current segment
        self.current_segment_id: Optional[str] = None
        self.current_text = ""
        
        logging.debug(f"StreamingSTTWrapper created for {participant_id} ({language.value})")
    
    async def process_audio_event(self, event: Any):
        """
        Process audio event and handle transcription results.
        
        Args:
            event: Audio event from LiveKit
        """
        try:
            # Extract transcription data from event
            if hasattr(event, 'alternatives') and event.alternatives:
                alternative = event.alternatives[0]
                transcript = alternative.text
                confidence = getattr(alternative, 'confidence', 0.0)
                is_final = getattr(event, 'is_final', False)
                
                # Generate segment ID if needed
                if not self.current_segment_id or is_final:
                    self.current_segment_id = str(uuid.uuid4())
                
                # Update current text
                self.current_text = transcript
                
                # Call appropriate callback
                if is_final and self.on_final_transcript:
                    await self.on_final_transcript(
                        segment_id=self.current_segment_id,
                        participant_id=self.participant_id,
                        text=transcript,
                        language=self.language,
                        confidence=confidence,
                        is_final=True
                    )
                    # Reset for next segment
                    self.current_segment_id = None
                    self.current_text = ""
                    
                elif not is_final and self.on_interim_transcript:
                    await self.on_interim_transcript(
                        segment_id=self.current_segment_id,
                        participant_id=self.participant_id,
                        text=transcript,
                        language=self.language,
                        confidence=confidence,
                        is_final=False
                    )
                
                logging.debug(f"Processed {'final' if is_final else 'interim'} transcript "
                            f"for {self.participant_id}: {transcript[:30]}...")
                
        except Exception as e:
            logging.error(f"Error processing audio event for {self.participant_id}: {e}")
    
    def get_current_segment_info(self) -> Dict:
        """Get information about the current segment."""
        return {
            "segment_id": self.current_segment_id,
            "participant_id": self.participant_id,
            "language": self.language.value,
            "current_text": self.current_text,
            "has_content": bool(self.current_text.strip())
        }


# Factory function for easy creation
def create_fast_stt_service(config: Optional[FastSTTConfig] = None) -> FastSTTService:
    """
    Factory function to create FastSTTService with optimal defaults.
    
    Args:
        config: Optional custom configuration
        
    Returns:
        Configured FastSTTService instance
    """
    if config is None:
        # Use ultra-fast defaults
        config = FastSTTConfig(
            provider=STTProvider.DEEPGRAM,
            model="nova-2-general",
            interim_results=True,
            utterance_end_ms=500,
            punctuate=False,
            smart_format=False,
            profanity_filter=False,
            redact=False,
            diarize=False,
            multichannel=False,
            alternatives=0,
            tier="enhanced",
            detect_language=False
        )
    
    return FastSTTService(config)
