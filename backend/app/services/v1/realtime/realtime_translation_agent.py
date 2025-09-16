"""
Specialized real-time translation agent optimized for 2-user simultaneous interpretation.
Integrates FastSTT, RealTimeTranslationBuffer, and CleanAudioRouter for ultra-low latency.
"""
import asyncio
import logging
import time
import uuid
from typing import Dict, Optional, Set, Callable, Any
from dataclasses import dataclass

from livekit import rtc
from livekit.agents import (
    JobContext,
    AutoSubscribe,
    AgentSession,
    Agent,
    stt,
    tts,
    llm
)
from livekit.plugins import deepgram, silero

from app.core.config import get_settings
from app.models.v1.domain.profiles import UserLanguageProfile, SupportedLanguage
from app.services.v1.realtime.translation_buffer import RealTimeTranslationBuffer, TranslationResult
from app.services.v1.realtime.fast_stt import FastSTTService, create_fast_stt_service
from app.services.v1.realtime.audio_router import CleanAudioRouter
from app.services.v1.translation.service import TranslationService


@dataclass
class RealtimeTranslationConfig:
    """Configuration for real-time translation agent."""
    max_delay_ms: int = 500
    interim_results: bool = True
    utterance_end_ms: int = 500
    enable_vad: bool = True
    audio_routing: bool = True
    translation_buffer_size: int = 10
    confidence_threshold: float = 0.7


class RealtimeTranslationAgent:
    """
    Ultra-fast real-time translation agent for 2-user simultaneous interpretation.
    
    Features:
    - 500ms max translation delay
    - Clean audio routing (no pollution)
    - Interim result processing
    - Optimized STT settings
    - Smart buffering
    - Language-aware audio management
    """
    
    def __init__(self, 
                 user_profile: UserLanguageProfile,
                 config: Optional[RealtimeTranslationConfig] = None):
        self.user_profile = user_profile
        self.config = config or RealtimeTranslationConfig()
        
        # Core components
        self.translation_buffer = RealTimeTranslationBuffer(
            max_delay_ms=self.config.max_delay_ms
        )
        self.fast_stt_service = create_fast_stt_service()
        self.audio_router = CleanAudioRouter()
        self.translation_service = TranslationService()
        
        # LiveKit components
        self.session: Optional[AgentSession] = None
        self.room: Optional[rtc.Room] = None
        self.local_participant: Optional[rtc.LocalParticipant] = None
        
        # Participant tracking
        self.participants: Dict[str, rtc.RemoteParticipant] = {}
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        self.stt_wrappers: Dict[str, Any] = {}
        
        # TTS for translated speech
        self.tts = None
        
        # State tracking
        self.is_running = False
        self.current_speaker: Optional[str] = None
        
        logging.info(f"RealtimeTranslationAgent initialized for {user_profile.user_identity}")
    
    async def start(self, ctx: JobContext):
        """Start the real-time translation agent."""
        try:
            self.room = ctx.room
            
            # Connect to room with timeout
            await asyncio.wait_for(
                ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY),
                timeout=5.0
            )
            self.local_participant = ctx.room.local_participant
            
            # Initialize TTS (fast operation)
            await self._init_tts()
            
            # Start core components (fast operation)  
            await self.translation_buffer.start()
            
            # Register translation callback (fast operation)
            self.translation_buffer.register_translation_callback(
                self.user_profile.user_identity,
                self._handle_translation_result
            )
            
            # Register audio router for this participant (fast operation)
            self.audio_router.register_participant(
                self.user_profile.user_identity,
                self.user_profile.native_language,
                local_participant=self.local_participant
            )
            
            # Set up event handlers (fast operation)
            self.room.on("participant_connected", self._sync_on_participant_connected)
            self.room.on("participant_disconnected", self._sync_on_participant_disconnected)
            self.room.on("track_published", self._sync_on_track_published)
            self.room.on("track_subscribed", self._sync_on_track_subscribed)
            
            # Process existing participants (fast operation)
            for participant in self.room.remote_participants.values():
                if participant.identity != self.user_profile.user_identity:
                    await self._register_participant(participant)
            
            # Start the main agent session with optimized configuration (potentially slow)
            try:
                await asyncio.wait_for(
                    self._create_optimized_session(ctx),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logging.warning(f"AgentSession creation timed out for {self.user_profile.user_identity}, continuing without session")
                # Continue without session - basic functionality will still work
            
            self.is_running = True
            logging.info(f"RealtimeTranslationAgent started for {self.user_profile.user_identity}")
            
        except Exception as e:
            logging.error(f"Error starting RealtimeTranslationAgent: {e}")
            await self.stop()
            raise
    
    def _sync_on_participant_connected(self, participant):
        """Synchronous wrapper for participant connected event."""
        asyncio.create_task(self._on_participant_connected(participant))

    def _sync_on_participant_disconnected(self, participant):
        """Synchronous wrapper for participant disconnected event."""
        asyncio.create_task(self._on_participant_disconnected(participant))

    def _sync_on_track_published(self, publication, participant):
        """Synchronous wrapper for track published event."""
        asyncio.create_task(self._on_track_published(publication, participant))

    def _sync_on_track_subscribed(self, track, publication, participant):
        """Synchronous wrapper for track subscribed event."""
        asyncio.create_task(self._on_track_subscribed(track, publication, participant))

    async def stop(self):
        """Stop the real-time translation agent."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        try:
            # Stop components
            await self.translation_buffer.stop()
            
            # Clean up STT wrappers
            self.stt_wrappers.clear()
            
            # Unregister from audio router
            self.audio_router.unregister_participant(self.user_profile.user_identity)
            
            logging.info(f"RealtimeTranslationAgent stopped for {self.user_profile.user_identity}")
            
        except Exception as e:
            logging.error(f"Error stopping RealtimeTranslationAgent: {e}")
    
    async def _init_tts(self):
        """Initialize TTS for translated speech output."""
        settings = get_settings()
        avatar = self.user_profile.preferred_voice_avatar
        
        if avatar.provider == "deepgram":
            self.tts = deepgram.TTS(
                api_key=settings.deepgram_api_key,
                model=avatar.model,
            )
        elif avatar.provider == "elevenlabs":
            # Check if ElevenLabs is configured
            if hasattr(settings, 'elevenlabs_api_key'):
                from livekit.plugins import elevenlabs
                self.tts = elevenlabs.TTS(
                    api_key=settings.elevenlabs_api_key,
                    voice=avatar.voice_id,
                    model=avatar.model,
                )
            else:
                # Fallback to Deepgram if ElevenLabs is not configured
                self.tts = deepgram.TTS(
                    api_key=settings.deepgram_api_key,
                    model="aura-2-thalia-en",
                )
        elif avatar.provider == "openai":
            from livekit.plugins import openai
            self.tts = openai.TTS(
                api_key=settings.openai_api_key,
                voice=avatar.voice_id,
                model=avatar.model,
            )
        else:
            # Fallback to Deepgram with a default model for unsupported providers
            self.tts = deepgram.TTS(
                api_key=settings.deepgram_api_key,
                model="aura-2-thalia-en",  # Use a known working Deepgram model
            )
        
        logging.debug(f"TTS initialized with provider: {avatar.provider}, model: {avatar.model}")
    
    async def _create_optimized_session(self, ctx: JobContext):
        """Create optimized AgentSession for real-time translation."""
        # Create optimized STT for the user's language
        user_stt = self.fast_stt_service.get_stt_instance(
            self.user_profile.native_language,
            self.user_profile.user_identity
        )
        
        # Create VAD if enabled
        vad = None
        if self.config.enable_vad:
            try:
                vad = silero.VAD.load()
                logging.info("VAD loaded successfully")
            except Exception as e:
                logging.warning(f"VAD not available: {e}")
        
        # Create minimal LLM (not used for translation, just for session)
        minimal_llm = self._create_minimal_llm()
        
        # Create a minimal agent for the session
        from livekit.agents import Agent
        
        class MinimalAgent(Agent):
            def __init__(self, user_identity: str):
                super().__init__(
                    instructions=f"Minimal agent for real-time translation user {user_identity}"
                )
        
        minimal_agent = MinimalAgent(self.user_profile.user_identity)
        
        # Create the session
        self.session = AgentSession(
            vad=vad,
            stt=user_stt,
            llm=minimal_llm,
            tts=self.tts,
        )
        
        # Set up optimized event handlers with CORRECT LiveKit event names
        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            logging.info(f"🎤 User input transcribed: {event.transcript[:50]}... (speaker: {event.speaker_id})")
            asyncio.create_task(self._handle_speech_event(event))
        
        @self.session.on("user_state_changed")
        def on_user_state_changed(event):
            logging.debug(f"👤 User state changed: {event.old_state} → {event.new_state}")
            if event.new_state == "speaking":
                asyncio.create_task(self._handle_speaking_started(event))
            elif event.old_state == "speaking":
                asyncio.create_task(self._handle_speaking_stopped(event))
        
        # Start the session with the minimal agent
        await self.session.start(agent=minimal_agent)
        
        logging.info("Optimized AgentSession created and started")
    
    def _create_minimal_llm(self):
        """Create minimal LLM for session (not used for translation)."""
        class MinimalLLM:
            async def chat(self, chat_ctx: llm.ChatContext):
                # Return empty response - we handle translation separately
                return llm.ChatResponse(content="")
        
        return MinimalLLM()
    
    async def _on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Handle new participant joining."""
        if participant.identity == self.user_profile.user_identity:
            return
        
        await self._register_participant(participant)
        logging.info(f"Participant connected: {participant.identity}")
    
    async def _on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Handle participant leaving."""
        participant_id = participant.identity
        
        # Clean up participant data
        self.participants.pop(participant_id, None)
        self.participant_languages.pop(participant_id, None)
        self.stt_wrappers.pop(participant_id, None)
        
        # Unregister from audio router
        self.audio_router.unregister_participant(participant_id)
        
        # Unregister translation callback
        self.translation_buffer.unregister_translation_callback(participant_id)
        
        logging.info(f"Participant disconnected: {participant_id}")
    
    async def _register_participant(self, participant: rtc.RemoteParticipant):
        """Register a new participant for translation."""
        participant_id = participant.identity
        
        # Store participant
        self.participants[participant_id] = participant
        
        # Extract language from metadata
        participant_language = self._extract_participant_language(participant)
        self.participant_languages[participant_id] = participant_language
        
        # Register with audio router
        self.audio_router.register_participant(
            participant_id,
            participant_language,
            participant=participant
        )
        
        # Create STT wrapper for this participant
        stt_wrapper = self.fast_stt_service.create_streaming_stt(
            participant_language,
            participant_id,
            on_interim_transcript=self._handle_interim_transcript,
            on_final_transcript=self._handle_final_transcript
        )
        self.stt_wrappers[participant_id] = stt_wrapper
        
        logging.info(f"Registered participant {participant_id} with language {participant_language.value}")
    
    def _extract_participant_language(self, participant: rtc.RemoteParticipant) -> SupportedLanguage:
        """Extract participant language from metadata."""
        try:
            import json
            metadata = json.loads(participant.metadata or "{}")
            lang_code = metadata.get("language", "en")
            return SupportedLanguage(lang_code)
        except Exception as e:
            logging.warning(f"Could not extract language for {participant.identity}: {e}")
            # Default to opposite language for 2-user setup
            if self.user_profile.native_language == SupportedLanguage.ENGLISH:
                return SupportedLanguage.SPANISH
            else:
                return SupportedLanguage.ENGLISH
    
    async def _on_track_published(self, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Handle audio track published by participant."""
        if publication.kind == rtc.TrackKind.KIND_AUDIO:
            logging.debug(f"Audio track published by {participant.identity}")
    
    async def _on_track_subscribed(self, track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Handle audio track subscription."""
        if isinstance(track, rtc.RemoteAudioTrack):
            logging.debug(f"Subscribed to audio track from {participant.identity}")
            # In a real implementation, you would set up audio processing here
    
    async def _handle_speech_event(self, event):
        """Handle transcribed speech event from AgentSession."""
        try:
            # Extract data from the UserInputTranscribedEvent
            participant_identity = event.speaker_id or self._extract_participant_identity(event)
            if not participant_identity or participant_identity == self.user_profile.user_identity:
                return
            
            transcript = event.transcript
            if not transcript.strip():
                return
            
            # Add to translation buffer
            segment_id = str(uuid.uuid4())
            participant_language = self.participant_languages.get(
                participant_identity, 
                SupportedLanguage.ENGLISH
            )
            
            await self.translation_buffer.add_audio_segment(
                segment_id=segment_id,
                participant_id=participant_identity,
                text=transcript,
                source_language=participant_language,
                is_final=True,
                confidence=0.9  # From AgentSession, assume high confidence
            )
            
            logging.debug(f"Added speech to buffer: {participant_identity}: {transcript[:50]}...")
            
        except Exception as e:
            logging.error(f"Error handling speech event: {e}")
    
    async def _handle_speaking_started(self, ev):
        """Handle when a participant starts speaking."""
        participant_identity = self._extract_participant_identity(ev)
        if participant_identity and participant_identity != self.user_profile.user_identity:
            self.current_speaker = participant_identity
            self.audio_router.set_current_speaker(participant_identity)
            logging.debug(f"Speaking started: {participant_identity}")
    
    async def _handle_speaking_stopped(self, ev):
        """Handle when a participant stops speaking."""
        participant_identity = self._extract_participant_identity(ev)
        if participant_identity and participant_identity == self.current_speaker:
            self.audio_router.clear_current_speaker(participant_identity)
            self.current_speaker = None
            logging.debug(f"Speaking stopped: {participant_identity}")
    
    def _extract_participant_identity(self, ev) -> Optional[str]:
        """Extract participant identity from event."""
        try:
            if hasattr(ev, 'participant') and ev.participant:
                return ev.participant.identity
            if hasattr(ev, 'participant_identity'):
                return ev.participant_identity
            if hasattr(ev, 'participant_id'):
                return ev.participant_id
            return None
        except Exception as e:
            logging.error(f"Error extracting participant identity: {e}")
            return None
    
    async def _handle_interim_transcript(self, 
                                       segment_id: str,
                                       participant_id: str,
                                       text: str,
                                       language: SupportedLanguage,
                                       confidence: float,
                                       is_final: bool):
        """Handle interim transcript from STT."""
        if confidence > self.config.confidence_threshold:
            await self.translation_buffer.add_audio_segment(
                segment_id=segment_id,
                participant_id=participant_id,
                text=text,
                source_language=language,
                is_final=is_final,
                confidence=confidence
            )
    
    async def _handle_final_transcript(self,
                                     segment_id: str,
                                     participant_id: str,
                                     text: str,
                                     language: SupportedLanguage,
                                     confidence: float,
                                     is_final: bool):
        """Handle final transcript from STT."""
        await self.translation_buffer.add_audio_segment(
            segment_id=segment_id,
            participant_id=participant_id,
            text=text,
            source_language=language,
            is_final=True,
            confidence=confidence
        )
    
    async def _handle_translation_result(self, result: TranslationResult):
        """Handle completed translation result."""
        try:
            # Play translated audio using TTS
            if self.session and result.translated_text:
                await self.session.say(result.translated_text)
                
                # Notify audio router about translated audio
                await self.audio_router.handle_translated_audio(
                    result.segment_id,  # Using segment_id as source participant
                    self.user_profile.user_identity,
                    b""  # Audio data would be generated by TTS
                )
                
                logging.info(f"Played translation: {result.original_text[:30]}... -> "
                           f"{result.translated_text[:30]}... "
                           f"({result.total_latency_ms:.1f}ms)")
        
        except Exception as e:
            logging.error(f"Error handling translation result: {e}")
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        buffer_stats = self.translation_buffer.get_stats()
        routing_info = self.audio_router.get_routing_info()
        
        return {
            "agent_info": {
                "user_identity": self.user_profile.user_identity,
                "native_language": self.user_profile.native_language.value,
                "is_running": self.is_running,
                "current_speaker": self.current_speaker,
                "participants_count": len(self.participants)
            },
            "translation_buffer": buffer_stats,
            "audio_routing": routing_info,
            "participants": {
                pid: lang.value 
                for pid, lang in self.participant_languages.items()
            }
        }
    
    def get_participant_info(self) -> Dict:
        """Get information about all participants."""
        return {
            pid: {
                "language": lang.value,
                "is_current_speaker": pid == self.current_speaker,
                "audio_config": self.audio_router.get_participant_audio_config(pid)
            }
            for pid, lang in self.participant_languages.items()
        }


class RealtimeTranslationService:
    """Service for managing real-time translation agents."""
    
    def __init__(self):
        self.active_agents: Dict[str, RealtimeTranslationAgent] = {}
        logging.info("RealtimeTranslationService initialized")
    
    async def create_agent(self, 
                          user_profile: UserLanguageProfile,
                          config: Optional[RealtimeTranslationConfig] = None) -> RealtimeTranslationAgent:
        """Create a new real-time translation agent."""
        agent = RealtimeTranslationAgent(user_profile, config)
        self.active_agents[user_profile.user_identity] = agent
        
        logging.info(f"Created RealtimeTranslationAgent for {user_profile.user_identity}")
        return agent
    
    async def start_agent(self, user_identity: str, ctx: JobContext) -> bool:
        """Start a real-time translation agent."""
        if user_identity not in self.active_agents:
            return False
        
        agent = self.active_agents[user_identity]
        await agent.start(ctx)
        return True
    
    async def stop_agent(self, user_identity: str) -> bool:
        """Stop a real-time translation agent."""
        if user_identity not in self.active_agents:
            return False
        
        agent = self.active_agents[user_identity]
        await agent.stop()
        del self.active_agents[user_identity]
        return True
    
    def get_agent(self, user_identity: str) -> Optional[RealtimeTranslationAgent]:
        """Get an active agent."""
        return self.active_agents.get(user_identity)
    
    def get_active_agents(self) -> Dict[str, RealtimeTranslationAgent]:
        """Get all active agents."""
        return self.active_agents.copy()
    
    def get_service_stats(self) -> Dict:
        """Get service-level statistics."""
        return {
            "active_agents_count": len(self.active_agents),
            "active_agents": list(self.active_agents.keys()),
            "agents_stats": {
                user_id: agent.get_stats()
                for user_id, agent in self.active_agents.items()
            }
        }
