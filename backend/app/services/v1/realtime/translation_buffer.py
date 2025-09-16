"""
Real-time translation buffer for ultra-low latency simultaneous interpretation.
Optimized for 2-user translation with 500ms max delay.
"""
import asyncio
import time
from typing import Dict, Optional, Callable, List, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

from app.models.domain.profiles import SupportedLanguage


class AudioSegmentState(Enum):
    PENDING = "pending"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AudioSegment:
    """Audio segment for real-time processing."""
    segment_id: str
    participant_id: str
    text: str
    source_language: SupportedLanguage
    timestamp: float
    is_final: bool = False
    confidence: float = 0.0
    state: AudioSegmentState = AudioSegmentState.PENDING
    translation_start_time: Optional[float] = None
    translation_end_time: Optional[float] = None


@dataclass
class TranslationResult:
    """Translation result with timing info."""
    segment_id: str
    original_text: str
    translated_text: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    translation_time_ms: float
    total_latency_ms: float


class RealTimeTranslationBuffer:
    """
    Ultra-fast translation buffer optimized for real-time simultaneous interpretation.
    
    Features:
    - 500ms max delay target
    - Interim result processing
    - Smart buffering for coherent translations
    - Audio pollution prevention
    """
    
    def __init__(self, max_delay_ms: int = 500):
        self.max_delay_ms = max_delay_ms
        self.pending_segments: Dict[str, AudioSegment] = {}
        self.processing_queue = asyncio.Queue()
        self.translation_callbacks: Dict[str, Callable] = {}
        
        # Performance tracking
        self.stats = {
            "segments_processed": 0,
            "avg_latency_ms": 0.0,
            "translations_completed": 0,
            "translations_failed": 0,
            "max_latency_ms": 0.0,
        }
        
        # Background processing task
        self._processing_task = None
        self._running = False
        
        logging.info(f"RealTimeTranslationBuffer initialized with {max_delay_ms}ms max delay")
    
    async def start(self):
        """Start the background processing task."""
        if self._running:
            return
            
        self._running = True
        self._processing_task = asyncio.create_task(self._process_segments())
        logging.info("RealTimeTranslationBuffer started")
    
    async def stop(self):
        """Stop the background processing task."""
        if not self._running:
            return
            
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logging.info("RealTimeTranslationBuffer stopped")
    
    def register_translation_callback(self, target_user_id: str, callback: Callable):
        """Register callback for translation results."""
        self.translation_callbacks[target_user_id] = callback
        logging.debug(f"Translation callback registered for user: {target_user_id}")
    
    def unregister_translation_callback(self, target_user_id: str):
        """Unregister translation callback."""
        self.translation_callbacks.pop(target_user_id, None)
        logging.debug(f"Translation callback unregistered for user: {target_user_id}")
    
    async def add_audio_segment(self, 
                               segment_id: str,
                               participant_id: str, 
                               text: str,
                               source_language: SupportedLanguage,
                               is_final: bool = False,
                               confidence: float = 0.0) -> bool:
        """
        Add audio segment for processing.
        
        Args:
            segment_id: Unique identifier for the segment
            participant_id: ID of the speaking participant
            text: Transcribed text
            source_language: Language of the original text
            is_final: Whether this is a final transcription
            confidence: Confidence score from STT
            
        Returns:
            True if segment was added successfully
        """
        try:
            current_time = time.time()
            
            # Create audio segment
            segment = AudioSegment(
                segment_id=segment_id,
                participant_id=participant_id,
                text=text.strip(),
                source_language=source_language,
                timestamp=current_time,
                is_final=is_final,
                confidence=confidence
            )
            
            # Skip empty segments
            if not segment.text:
                return False
            
            # Update existing segment or create new one
            if segment_id in self.pending_segments:
                existing = self.pending_segments[segment_id]
                existing.text = segment.text
                existing.is_final = segment.is_final
                existing.confidence = segment.confidence
                logging.debug(f"Updated segment {segment_id}: {text[:50]}...")
            else:
                self.pending_segments[segment_id] = segment
                logging.debug(f"Added new segment {segment_id}: {text[:50]}...")
            
            # Queue for immediate processing if final or confidence is high
            if is_final or confidence > 0.8:
                await self.processing_queue.put(segment_id)
                logging.debug(f"Queued segment {segment_id} for immediate processing")
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding audio segment: {e}")
            return False
    
    async def _process_segments(self):
        """Background task to process translation segments."""
        logging.info("Starting segment processing loop")
        
        while self._running:
            try:
                # Wait for segment to process or timeout
                try:
                    segment_id = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=self.max_delay_ms / 1000.0
                    )
                except asyncio.TimeoutError:
                    # Process any pending segments that have exceeded max delay
                    await self._process_delayed_segments()
                    continue
                
                # Process the specific segment
                if segment_id in self.pending_segments:
                    await self._translate_segment(segment_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in segment processing loop: {e}")
                await asyncio.sleep(0.01)  # Brief pause to prevent tight error loop
    
    async def _process_delayed_segments(self):
        """Process segments that have exceeded max delay."""
        current_time = time.time()
        delayed_segments = []
        
        for segment_id, segment in self.pending_segments.items():
            if (segment.state == AudioSegmentState.PENDING and 
                (current_time - segment.timestamp) * 1000 > self.max_delay_ms):
                delayed_segments.append(segment_id)
        
        for segment_id in delayed_segments:
            await self._translate_segment(segment_id)
            logging.debug(f"Processed delayed segment: {segment_id}")
    
    async def _translate_segment(self, segment_id: str):
        """Translate a specific segment."""
        if segment_id not in self.pending_segments:
            return
        
        segment = self.pending_segments[segment_id]
        
        # Skip if already processing or completed
        if segment.state != AudioSegmentState.PENDING:
            return
        
        segment.state = AudioSegmentState.TRANSLATING
        segment.translation_start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from app.services.translation.service import TranslationService
            translation_service = TranslationService()
            
            # Get all registered callbacks (target users)
            for target_user_id, callback in self.translation_callbacks.items():
                try:
                    # Skip if this is the speaker's own callback
                    if target_user_id == segment.participant_id:
                        continue
                    
                    # For now, assume target language is English if source is Spanish, and vice versa
                    # In a real implementation, you'd get this from user profiles
                    if segment.source_language == SupportedLanguage.SPANISH:
                        target_language = SupportedLanguage.ENGLISH
                    else:
                        target_language = SupportedLanguage.SPANISH
                    
                    # Skip if same language
                    if segment.source_language == target_language:
                        continue
                    
                    # Perform translation
                    translated_text = await translation_service.translate_text(
                        segment.text,
                        segment.source_language,
                        target_language,
                        preferences={"formal_tone": False, "preserve_emotion": True}
                    )
                    
                    # Calculate timing
                    translation_end_time = time.time()
                    translation_time_ms = (translation_end_time - segment.translation_start_time) * 1000
                    total_latency_ms = (translation_end_time - segment.timestamp) * 1000
                    
                    # Create result
                    result = TranslationResult(
                        segment_id=segment_id,
                        original_text=segment.text,
                        translated_text=translated_text,
                        source_language=segment.source_language,
                        target_language=target_language,
                        translation_time_ms=translation_time_ms,
                        total_latency_ms=total_latency_ms
                    )
                    
                    # Update stats
                    self._update_stats(result)
                    
                    # Call the callback
                    await callback(result)
                    
                    logging.info(f"Translation completed in {translation_time_ms:.1f}ms "
                               f"(total: {total_latency_ms:.1f}ms): {segment.text[:30]}... -> "
                               f"{translated_text[:30]}...")
                    
                except Exception as e:
                    logging.error(f"Translation failed for user {target_user_id}: {e}")
                    self.stats["translations_failed"] += 1
            
            segment.state = AudioSegmentState.COMPLETED
            segment.translation_end_time = time.time()
            
        except Exception as e:
            logging.error(f"Error translating segment {segment_id}: {e}")
            segment.state = AudioSegmentState.FAILED
            self.stats["translations_failed"] += 1
        
        finally:
            # Clean up completed/failed segments after a brief delay
            asyncio.create_task(self._cleanup_segment(segment_id, delay=2.0))
    
    async def _cleanup_segment(self, segment_id: str, delay: float = 2.0):
        """Clean up a processed segment after delay."""
        await asyncio.sleep(delay)
        self.pending_segments.pop(segment_id, None)
        logging.debug(f"Cleaned up segment: {segment_id}")
    
    def _update_stats(self, result: TranslationResult):
        """Update performance statistics."""
        self.stats["segments_processed"] += 1
        self.stats["translations_completed"] += 1
        
        # Update average latency
        current_avg = self.stats["avg_latency_ms"]
        count = self.stats["translations_completed"]
        self.stats["avg_latency_ms"] = ((current_avg * (count - 1)) + result.total_latency_ms) / count
        
        # Update max latency
        if result.total_latency_ms > self.stats["max_latency_ms"]:
            self.stats["max_latency_ms"] = result.total_latency_ms
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        return {
            **self.stats,
            "pending_segments": len(self.pending_segments),
            "queue_size": self.processing_queue.qsize(),
            "target_delay_ms": self.max_delay_ms,
        }
    
    def get_segment_info(self, segment_id: str) -> Optional[Dict]:
        """Get information about a specific segment."""
        if segment_id not in self.pending_segments:
            return None
        
        segment = self.pending_segments[segment_id]
        return {
            "segment_id": segment.segment_id,
            "participant_id": segment.participant_id,
            "text": segment.text,
            "source_language": segment.source_language.value,
            "timestamp": segment.timestamp,
            "is_final": segment.is_final,
            "confidence": segment.confidence,
            "state": segment.state.value,
            "age_ms": (time.time() - segment.timestamp) * 1000,
        }
