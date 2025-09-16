"""
LiveKit agent service for user translation agents.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from livekit import api, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    # WorkerOptions,
    # cli,
    stt,
    tts,
    llm,
    AgentSession,
    Agent,
    function_tool,
)
from livekit.agents.vad import VAD
from livekit.plugins import openai, deepgram, silero
from livekit.plugins import spitch

from app.core.config import get_settings
from app.models.v1.domain.profiles import UserLanguageProfile, SupportedLanguage
from app.services.v1.translation.service import TranslationService
from app.services.v1.livekit.room_manager import PatternBRoomManager, RoomType
from app.services.v1.realtime.realtime_translation_agent import RealtimeTranslationService, RealtimeTranslationConfig


class TranslationAgent(Agent):
    """Custom LiveKit Agent for real-time translation"""

    def __init__(self, user_profile: UserLanguageProfile, translation_service: TranslationService):
        super().__init__(
            instructions=f"You are a real-time translation assistant for {user_profile.user_identity}. "
                        f"Translate speech from other participants into {user_profile.native_language.value}."
        )

        self.user_profile = user_profile
        self.translation_service = translation_service
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        self.active_participants: Set[str] = set()

    def register_participant(self, identity: str, language: SupportedLanguage):
        """Register a participant with their language"""
        self.participant_languages[identity] = language
        self.active_participants.add(identity)
        logging.info(f"Registered participant: {identity} ({language.value})")

    def unregister_participant(self, identity: str):
        """Unregister a participant"""
        self.participant_languages.pop(identity, None)
        self.active_participants.discard(identity)
        logging.info(f"Unregistered participant: {identity}")

    @function_tool()
    async def translate_speech(self, speech_text: str, speaker_identity: str) -> str:
        """Translate speech from a specific participant"""
        try:
            # Skip if it's the user's own speech
            if speaker_identity == self.user_profile.user_identity:
                return speech_text

            # Get speaker's language
            speaker_lang = self.participant_languages.get(speaker_identity, SupportedLanguage.ENGLISH)

            # Skip translation if same language
            if speaker_lang == self.user_profile.native_language:
                logging.debug(f"Skipping translation for {speaker_identity} (same language)")
                return speech_text

            # Perform translation
            translated_text = await self.translation_service.translate_text(
                speech_text,
                speaker_lang,
                self.user_profile.native_language,
                self.user_profile.translation_preferences
            )

            if translated_text and translated_text != speech_text:
                logging.info(f"Agent translated: {speaker_identity} ({speaker_lang} -> {self.user_profile.native_language})")
                return translated_text
            else:
                return speech_text

        except Exception as e:
            logging.error(f"Error in translate_speech: {e}")
            return speech_text


class UserTranslationAgent:
    """Per-user translation agent for LiveKit using AgentSession."""

    def __init__(self, user_profile: UserLanguageProfile, livekit_service: 'LiveKitService' = None):
        self.user_profile = user_profile
        self.livekit_service = livekit_service
        self.translation_service = TranslationService()
        self.session: Optional[AgentSession] = None
        self.room: Optional[rtc.Room] = None
        self.room_name: Optional[str] = None
        self.local_participant: Optional[rtc.LocalParticipant] = None
        self.translation_agent: Optional[TranslationAgent] = None

        # Track participant languages for translation
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        self.active_participants: Set[str] = set()
        
        # Agent coordination
        self.connected_agents: Dict[str, 'UserTranslationAgent'] = {}

        # Initialize TTS
        self._init_tts()
        self._init_stt()

    def _init_stt(self):
        """Initialize STT with user's preferred voice avatar"""
        settings = get_settings()
        avatar = self.user_profile.preferred_voice_avatar
        # if avatar.provider == "deepgram":
        self.stt = deepgram.STT(
            api_key=settings.deepgram_api_key,
                # voice=avatar.voice_id,
                model=avatar.model,
            )
        # elif avatar.provider == "spitch":
        #     self.stt = spitch.STT(
        #         api_key=settings.spitch_api_key,
        #         # model=avatar.model,
        #         # model="spitch-stt",
        #     )

    def _init_tts(self):
        """Initialize TTS with user's preferred voice avatar"""
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
        # if avatar.provider == "deepgram":
        #     self.tts = deepgram.TTS(
        #         api_key=settings.deepgram_api_key,
        #         # voice=avatar.voice_id,
        #         model=avatar.model,
        #         # model="eleven_turbo_v2_5",
        #     )

        # elif avatar.provider == "spitch":
        #     self.tts = spitch.TTS(
        #         api_key=settings.spitch_api_key,
        #         voice=avatar.voice_id,
        #         # model=avatar.model,
        #         # model="spitch-tts",
        #     )
        # elif avatar.provider == "openai":
        #     self.tts = openai.TTS(
        #         api_key=settings.openai_api_key,
        #         voice=avatar.voice_id,
        #         model=avatar.model,
        #         # model="tts-1",
        #     )
        # else:
        #     # Default fallback
        #     self.tts = deepgram.TTS(
        #         api_key=settings.deepgram_api_key,
        #         # voice=avatar.voice_id
        #     )

    async def start(self, ctx: JobContext):
        """Initialize the user translation agent with AgentSession"""
        self.room = ctx.room
        self.room_name = ctx.room.name

        # Connect to room first
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Now we can access the local participant after connecting
        self.local_participant = ctx.room.local_participant

        # Set up event handlers for participant management
        self.room.on("participant_connected", self._on_participant_connected)
        self.room.on("participant_disconnected", self._on_participant_disconnected)
        self.room.on("track_published", self._on_track_published)

        # Initialize participant tracking for existing participants
        for participant in self.room.remote_participants.values():
            if participant.identity != self.user_profile.user_identity:
                self._register_participant(participant)

        # Create the main AgentSession for this user
        await self._create_agent_session(ctx)

        logging.info(f"Translation agent started for user {self.user_profile.user_identity}")
        logging.info(f"Target language: {self.user_profile.native_language}")
        logging.info(f"Voice avatar: {self.user_profile.preferred_voice_avatar.name}")

    def _register_participant(self, participant: rtc.RemoteParticipant):
        """Register a participant and their language for translation"""
        if participant.identity == self.user_profile.user_identity:
            return

        participant_lang = self._get_participant_language(participant)
        self.participant_languages[participant.identity] = participant_lang
        self.active_participants.add(participant.identity)

        # Also register with the translation agent if it exists
        if self.translation_agent:
            self.translation_agent.register_participant(participant.identity, participant_lang)

        if participant_lang != self.user_profile.native_language:
            logging.info(f"Registered participant {participant.identity} for translation ({participant_lang} -> {self.user_profile.native_language})")
        else:
            logging.info(f"Registered participant {participant.identity} (same language, no translation needed)")

    def _on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Handle new participant joining"""
        if participant.identity == self.user_profile.user_identity:
            return  # Don't translate our own speech

        logging.info(f"New participant {participant.identity} connected")
        self._register_participant(participant)

    def _on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Handle participant disconnecting"""
        if participant.identity in self.active_participants:
            self.active_participants.remove(participant.identity)
            self.participant_languages.pop(participant.identity, None)

            # Also unregister from the translation agent
            if self.translation_agent:
                self.translation_agent.unregister_participant(participant.identity)

            logging.info(f"Participant {participant.identity} disconnected")

    def _on_track_published(self, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Subscribe to audio tracks from other participants"""
        try:
            # Validate parameters before creating task
            if publication is None:
                logging.warning("Track publication is None, cannot subscribe")
                return
                
            if participant is None:
                logging.warning("Participant is None, cannot subscribe to track")
                return
                
            if not hasattr(publication, 'kind'):
                logging.warning("Publication has no 'kind' attribute, cannot determine track type")
                return
            
            # Log audio tracks from other participants (auto-subscribed due to AutoSubscribe.AUDIO_ONLY)
            if (publication.kind == rtc.TrackKind.KIND_AUDIO and 
                participant.identity != self.user_profile.user_identity):
                logging.info(f"Audio track published by {participant.identity} (auto-subscribed)")
                # Note: Manual subscription not needed due to AutoSubscribe.AUDIO_ONLY
            else:
                logging.debug(f"Skipping track from {participant.identity}: "
                            f"kind={getattr(publication, 'kind', 'unknown')}, "
                            f"is_self={participant.identity == self.user_profile.user_identity}")
                
        except Exception as e:
            logging.error(f"Error in _on_track_published: {e}")

    async def on_agent_joined(self, other_agent: 'UserTranslationAgent'):
        """Handle when another agent joins the same room"""
        self.connected_agents[other_agent.user_profile.user_identity] = other_agent
        logging.info(f"Agent {self.user_profile.user_identity} connected to agent {other_agent.user_profile.user_identity}")

    async def translate_for_user(self, text: str, source_language: SupportedLanguage, 
                               speaker_identity: str) -> Optional[str]:
        """Translate text for this agent's user"""
        try:
            if source_language == self.user_profile.native_language:
                return None  # No translation needed
                
            translated_text = await self.translation_service.translate_text(
                text,
                source_language,
                self.user_profile.native_language,
                self.user_profile.translation_preferences
            )
            
            # Generate and play TTS for this user
            if translated_text and self.tts and self.session:
                await self.session.say(translated_text)
            
            return translated_text
            
        except Exception as e:
            logging.error(f"Translation failed for user {self.user_profile.user_identity}: {e}")
            return None

    async def _create_agent_session(self, ctx: JobContext):
        """Create the main AgentSession for this user"""
        settings = get_settings()

        # Create STT for detecting speaker language
        # Try Deepgram STT first (supports streaming natively)
        stt_instance = None
        try:
            stt_instance = deepgram.STT(
                api_key=settings.deepgram_api_key,
                model="nova-2-general",
                language="en",  # Default, will be overridden per participant
                interim_results=False,
                punctuate=True,
            )
            logging.info("Using Deepgram STT for speech recognition")
        except Exception as e:
            logging.warning(f"Deepgram STT failed to initialize: {e}")
            
            # Fallback to OpenAI STT if available
            try:
                stt_instance = openai.STT(
                    api_key=settings.openai_api_key,
                    model="whisper-1",
                    language="en",
                )
                logging.info("Using OpenAI STT as fallback for speech recognition")
            except Exception as e2:
                logging.error(f"All STT options failed: Deepgram={e}, OpenAI={e2}")
                raise RuntimeError("No working STT service available")

        # Alternative: If you want to use Spitch STT, uncomment below and ensure VAD is working
        # Note: Spitch STT requires VAD or StreamAdapter for streaming
        # try:
        #     vad_for_spitch = silero.VAD.load()
        #     stt_instance = stt.StreamAdapter(
        #         spitch.STT(
        #             api_key=settings.spitch_api_key,
        #             model="spitch-stt",
        #         ),
        #         vad=vad_for_spitch  # Required for non-streaming STT
        #     )
        #     logging.info("Using Spitch STT with StreamAdapter")
        # except Exception as e:
        #     logging.warning(f"Spitch STT with StreamAdapter failed: {e}")
        #     # Continue with Deepgram or OpenAI fallback above

        # Create translation LLM that can handle multiple languages
        translation_llm = self._create_multi_language_llm()

        # Try to use Silero VAD for better speech detection
        vad = None
        try:
            vad = silero.VAD.load()
            logging.info("Silero VAD loaded successfully for speech detection")
        except Exception as e:
            logging.warning(f"VAD not available, proceeding without: {e}")
            logging.info("Speech detection will rely on STT without VAD")

        # Create the custom translation agent
        self.translation_agent = TranslationAgent(self.user_profile, self.translation_service)

        # Sync participant information with the translation agent
        for identity, language in self.participant_languages.items():
            self.translation_agent.register_participant(identity, language)

        # Create the main AgentSession with the custom agent
        self.session = AgentSession(
            vad=vad,  # Enable VAD for better speech detection
            stt=stt_instance,
            llm=translation_llm,
            tts=self.tts,
            # chat_ctx=llm.ChatContext(),
        )

        # Set up speech event handler with CORRECT LiveKit event names
        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            """Handle transcribed speech from any participant - CORRECT EVENT NAME"""
            logging.info(f"🎤 User input transcribed: {event.transcript[:50]}... (speaker: {event.speaker_id})")
            asyncio.create_task(self._handle_user_speech(event))

        # Set up state change handlers
        @self.session.on("user_state_changed")
        def on_user_state_changed(event):
            """Track user state changes (speaking/listening/away)"""
            logging.debug(f"👤 User state changed: {event.old_state} → {event.new_state}")
            # Register participant when they start speaking
            if event.new_state == "speaking":
                participant_identity = getattr(event, 'participant_identity', None)
                if participant_identity and self.translation_agent:
                    self.translation_agent.register_participant(
                        participant_identity,
                        self.participant_languages.get(participant_identity, SupportedLanguage.ENGLISH)
                    )

        @self.session.on("conversation_item_added")
        def on_conversation_item_added(event):
            """Track conversation items being added"""
            logging.debug(f"💬 Conversation item added from {event.item.role}: {event.item.text_content[:50]}...")

        # Start the session with the custom agent
        await self.session.start(self.translation_agent, room=self.room)
        logging.info("AgentSession started successfully with TranslationAgent")

    async def _handle_user_speech(self, event):
        """Handle transcribed speech from a participant using coordinated translation"""
        try:
            # Extract data from the UserInputTranscribedEvent
            user_message = event.transcript
            participant_identity = event.speaker_id or self._extract_participant_identity(event)

            # Skip if this is our own speech or we can't identify the speaker
            if not participant_identity or participant_identity == self.user_profile.user_identity:
                logging.debug("Skipping speech processing (own speech or unknown participant)")
                return

            # Get participant's language
            participant_lang = self.participant_languages.get(participant_identity, SupportedLanguage.ENGLISH)
            
            logging.info(f"Speech detected from {participant_identity}: {user_message[:100]}...")

            # Use coordinated translation if LiveKit service is available
            if self.livekit_service and self.room_name:
                # Let the service coordinate translation among all agents
                translations = await self.livekit_service.coordinate_translation_task(
                    self.room_name, 
                    participant_identity, 
                    user_message, 
                    participant_lang
                )
                
                # Check if this agent received a translation
                if self.user_profile.user_identity in translations:
                    translated_text = translations[self.user_profile.user_identity]
                    logging.info(f"Received coordinated translation: {translated_text[:100]}...")
                else:
                    logging.debug("No translation needed for this user (same language or other reason)")
                    
            else:
                # Fallback to independent translation (original behavior)
                if participant_lang == self.user_profile.native_language:
                    logging.debug(f"Skipping translation for {participant_identity} (same language)")
                    return

                translated_text = await self.translation_service.translate_text(
                    user_message,
                    participant_lang,
                    self.user_profile.native_language,
                    self.user_profile.translation_preferences
                )

                if translated_text and translated_text != user_message:
                    await self.session.say(translated_text)
                    logging.info(f"Translated independently: {translated_text[:100]}...")

        except Exception as e:
            logging.error(f"Error handling user speech: {e}")

    def _extract_participant_identity(self, ev) -> Optional[str]:
        """Extract participant identity from speech event"""
        try:
            # Try different ways to get participant identity from the event

            # Method 1: Check if event has participant attribute
            if hasattr(ev, 'participant') and ev.participant:
                return ev.participant.identity

            # Method 2: Check if event has participant_identity attribute
            if hasattr(ev, 'participant_identity'):
                return ev.participant_identity

            # Method 3: Check if event has a participant_id attribute
            if hasattr(ev, 'participant_id'):
                return ev.participant_id

            # Method 4: Try to find participant by searching active participants
            # This is a fallback for cases where the event doesn't directly contain identity
            transcript = getattr(ev, 'user_transcript', '')

            # Look for the participant who most recently spoke
            # This is a heuristic - in production you'd want more robust participant tracking
            for identity in self.active_participants:
                # You could add more sophisticated logic here based on timing
                # or other event metadata to identify the speaker
                pass

            # Method 5: Check event metadata or source information
            if hasattr(ev, 'source') and ev.source:
                if hasattr(ev.source, 'participant_identity'):
                    return ev.source.participant_identity
                if hasattr(ev.source, 'identity'):
                    return ev.source.identity

            logging.warning(f"Could not extract participant identity from speech event: {type(ev)}")
            return None

        except Exception as e:
            logging.error(f"Error extracting participant identity: {e}")
            return None

    def _create_multi_language_llm(self):
        """Create an LLM wrapper that can handle translation for any participant"""

        class MultiLanguageTranslationLLM:
            def __init__(self, translation_service, agent):
                self.translation_service = translation_service
                self.agent = agent
                self.last_speaker_identity = None
                self.pending_translations = {}  # Track pending translations by message content

            async def chat(self, chat_ctx: llm.ChatContext):
                """Handle chat with translation logic"""
                try:
                    # Get the latest user message
                    if not chat_ctx.items or len(chat_ctx.items) == 0:
                        return llm.ChatResponse(content="")
                    
                    # Find the last message item with user role
                    last_user_message = None
                    for item in reversed(chat_ctx.items):
                        if item.type == "message" and item.role == "user":
                            last_user_message = item
                            break
                    
                    if not last_user_message:
                        return llm.ChatResponse(content="")

                    user_message = last_user_message.content[0] if isinstance(last_user_message.content, list) else last_user_message.content

                    # Try to identify which participant spoke this message
                    speaker_identity = self._identify_speaker_from_message(user_message)

                    if not speaker_identity:
                        # If we can't identify the speaker, check if this matches a pending translation
                        if user_message in self.pending_translations:
                            speaker_identity = self.pending_translations[user_message]
                            del self.pending_translations[user_message]
                        else:
                            logging.warning(f"Could not identify speaker for message: {user_message[:50]}...")
                            return llm.ChatResponse(content=user_message)

                    # Get the speaker's language
                    speaker_lang = self.agent.participant_languages.get(speaker_identity, SupportedLanguage.ENGLISH)

                    # Skip translation if same language as the user
                    if speaker_lang == self.agent.user_profile.native_language:
                        logging.debug(f"Skipping translation for {speaker_identity} (same language)")
                        return llm.ChatResponse(content=user_message)

                    # Perform translation
                    translated_text = await self.translation_service.translate_text(
                        user_message,
                        speaker_lang,
                        self.agent.user_profile.native_language,
                        self.agent.user_profile.translation_preferences
                    )

                    if translated_text and translated_text != user_message:
                        logging.info(f"LLM translated: {speaker_identity} ({speaker_lang} -> {self.agent.user_profile.native_language})")
                        return llm.ChatResponse(content=translated_text)
                    else:
                        logging.debug("Translation resulted in no changes")
                        return llm.ChatResponse(content=user_message)

                except Exception as e:
                    logging.error(f"Error in translation LLM: {e}")
                    return llm.ChatResponse(content=user_message)

            def _identify_speaker_from_message(self, message: str) -> Optional[str]:
                """Identify which participant spoke this message"""
                try:
                    # Method 1: Check if we have a last known speaker
                    if self.last_speaker_identity and self.last_speaker_identity in self.agent.active_participants:
                        return self.last_speaker_identity

                    # Method 2: Try to match message content with recent speech
                    # This is a heuristic approach - in a more sophisticated implementation,
                    # you might use timing information or other metadata

                    # For now, we'll use a simple approach: assume the most recently active participant
                    # In practice, you'd want to enhance this with better speaker identification
                    if self.agent.active_participants:
                        # Return the first active participant (this could be enhanced)
                        return next(iter(self.agent.active_participants))

                    logging.debug("No active participants found for speaker identification")
                    return None

                except Exception as e:
                    logging.error(f"Error identifying speaker: {e}")
                    return None

            def update_last_speaker(self, identity: str):
                """Update the last known speaker identity"""
                self.last_speaker_identity = identity

            def register_pending_translation(self, message: str, speaker_identity: str):
                """Register a pending translation for message identification"""
                self.pending_translations[message] = speaker_identity

        translation_llm = MultiLanguageTranslationLLM(self.translation_service, self)

        # Store reference for updating speaker context
        self.translation_llm = translation_llm

        return translation_llm

    def _get_participant_language(self, participant: rtc.RemoteParticipant) -> SupportedLanguage:
        """Extract participant's language from metadata"""
        try:
            import json
            metadata = json.loads(participant.metadata or "{}")
            lang = metadata.get("language", "en")
            return SupportedLanguage(lang)
        except:
            return SupportedLanguage.ENGLISH



class LiveKitService:
    """Service for LiveKit operations with real-time translation support."""

    def __init__(self, room_manager: PatternBRoomManager):
        self.room_manager = room_manager
        self.active_agents: Dict[str, UserTranslationAgent] = {}
        # Room-level agent registry: room_name -> {user_identity -> agent}
        self.room_agents: Dict[str, Dict[str, UserTranslationAgent]] = {}
        self._livekit_api = None
        
        # Real-time translation service for ultra-fast translation
        self.realtime_translation_service = RealtimeTranslationService()

    async def create_user_agent(self, user_identity: str, ctx: JobContext, use_realtime: bool = True) -> UserTranslationAgent:
        """Create and start a translation agent for a user"""
        profile = await self.room_manager.get_user_profile(user_identity)
        if not profile:
            # Try to create profile from job metadata
            profile = await self._create_profile_from_metadata(user_identity, ctx)
            if not profile:
                raise ValueError(f"No profile found for user {user_identity} and cannot create from metadata")

        room_name = ctx.room.name
        
        # Check if this is a translation room (2 users max)
        is_translation_room = self._is_translation_room(room_name, ctx.room)
        
        if use_realtime and is_translation_room:
            # Use the new real-time translation agent for optimal performance
            return await self._create_realtime_agent(user_identity, profile, ctx)
        else:
            # Use the legacy agent for non-translation rooms or when realtime is disabled
            return await self._create_legacy_agent(user_identity, profile, ctx)

    async def _create_realtime_agent(self, user_identity: str, profile: UserLanguageProfile, ctx: JobContext):
        """Create and start a real-time translation agent."""
        try:
            # Configure for ultra-fast translation
            config = RealtimeTranslationConfig(
                max_delay_ms=500,           # 500ms max delay as requested
                interim_results=True,       # Process interim results
                utterance_end_ms=500,      # Fast utterance detection  
                enable_vad=True,           # Use VAD for better detection
                audio_routing=True,        # Enable clean audio routing
                confidence_threshold=0.7   # Lower threshold for speed
            )
            
            # Create the real-time agent (fast operation)
            realtime_agent = await asyncio.wait_for(
                self.realtime_translation_service.create_agent(profile, config),
                timeout=5.0
            )
            
            # Start the agent (this might take longer, so separate timeout)
            await asyncio.wait_for(
                self.realtime_translation_service.start_agent(user_identity, ctx),
                timeout=8.0
            )
            
            logging.info(f"Created real-time translation agent for {user_identity}")
            return realtime_agent
            
        except asyncio.TimeoutError:
            logging.error(f"Real-time agent creation/start timed out for {user_identity}")
            # Fallback to legacy agent
            logging.info(f"Falling back to legacy agent for {user_identity}")
            return await self._create_legacy_agent(user_identity, profile, ctx)
        except Exception as e:
            logging.error(f"Error creating real-time agent for {user_identity}: {e}")
            # Fallback to legacy agent
            logging.info(f"Falling back to legacy agent for {user_identity}")
            return await self._create_legacy_agent(user_identity, profile, ctx)

    async def _create_legacy_agent(self, user_identity: str, profile: UserLanguageProfile, ctx: JobContext):
        """Create and start a legacy translation agent."""
        # Pass the service reference to enable agent coordination
        agent = UserTranslationAgent(profile, livekit_service=self)
        await agent.start(ctx)
        
        # Register agent globally and by room
        self.active_agents[user_identity] = agent
        room_name = ctx.room.name
        if room_name not in self.room_agents:
            self.room_agents[room_name] = {}
        self.room_agents[room_name][user_identity] = agent

        # Notify existing agents in the room about the new agent
        await self._notify_agents_of_new_agent(room_name, agent)

        logging.info(f"Created legacy translation agent for {user_identity}")
        return agent

    async def _create_profile_from_metadata(self, user_identity: str, ctx: JobContext) -> Optional[UserLanguageProfile]:
        """Create a user profile from job metadata if available."""
        try:
            if not ctx.job.metadata:
                return None
                
            metadata = json.loads(ctx.job.metadata)
            
            # Extract language from metadata
            native_language_code = metadata.get("native_language", "en")
            try:
                native_language = SupportedLanguage(native_language_code)
            except ValueError:
                logging.warning(f"Unsupported language code: {native_language_code}, defaulting to English")
                native_language = SupportedLanguage.ENGLISH
            
            # Get default voice avatar for the language
            from app.models.domain.profiles import VOICE_AVATARS
            avatars = VOICE_AVATARS.get(native_language.value, VOICE_AVATARS["en"])
            default_avatar = avatars[0] if avatars else None
            
            if not default_avatar:
                logging.error(f"No voice avatar available for language: {native_language.value}")
                return None
            
            # Create the profile
            profile = UserLanguageProfile(
                user_identity=user_identity,
                native_language=native_language,
                preferred_voice_avatar=default_avatar,
                translation_preferences=metadata.get("translation_preferences", {"formal_tone": False, "preserve_emotion": True})
            )
            
            # Save to database
            await self.room_manager.create_user_profile(profile)
            logging.info(f"Created user profile for {user_identity} with language {native_language.value}")
            
            return profile
            
        except Exception as e:
            logging.error(f"Error creating profile from metadata for {user_identity}: {e}")
            return None

    def _is_translation_room(self, room_name: str, room: rtc.Room) -> bool:
        """Check if this is a translation room (2-user simultaneous interpretation)."""
        # Check room name pattern
        if "translation" in room_name.lower():
            return True
        
        # Check participant count (translation rooms are limited to 2)
        total_participants = len(room.remote_participants) + (1 if room.local_participant else 0)
        if total_participants <= 2:
            return True
        
        return False

    def remove_user_agent(self, user_identity: str):
        """Clean up user agent"""
        if user_identity in self.active_agents:
            agent = self.active_agents[user_identity]
            del self.active_agents[user_identity]
            
            # Remove from room registry
            room_name = getattr(agent, 'room_name', None)
            if room_name and room_name in self.room_agents:
                self.room_agents[room_name].pop(user_identity, None)
                # Clean up empty room entries
                if not self.room_agents[room_name]:
                    del self.room_agents[room_name]
            
            logging.info(f"Removed agent for user {user_identity}")

    async def _notify_agents_of_new_agent(self, room_name: str, new_agent: 'UserTranslationAgent'):
        """Notify existing agents in the room about a new agent joining"""
        if room_name not in self.room_agents:
            return
            
        for user_identity, existing_agent in self.room_agents[room_name].items():
            if existing_agent != new_agent:
                await existing_agent.on_agent_joined(new_agent)
                await new_agent.on_agent_joined(existing_agent)

    def get_room_agents(self, room_name: str) -> Dict[str, 'UserTranslationAgent']:
        """Get all agents in a specific room"""
        return self.room_agents.get(room_name, {})

    async def coordinate_translation_task(self, room_name: str, participant_identity: str, 
                                        speech_text: str, source_language: SupportedLanguage) -> Dict[str, str]:
        """Coordinate translation task among agents in the room"""
        if room_name not in self.room_agents:
            return {}
            
        translations = {}
        translation_tasks = []
        
        # Create translation tasks for each agent that needs this translation
        for user_identity, agent in self.room_agents[room_name].items():
            if (user_identity != participant_identity and 
                agent.user_profile.native_language != source_language):
                
                task = agent.translate_for_user(
                    speech_text, source_language, participant_identity
                )
                translation_tasks.append((user_identity, task))
        
        # Execute all translations concurrently
        if translation_tasks:
            results = await asyncio.gather(
                *[task for _, task in translation_tasks], 
                return_exceptions=True
            )
            
            for (user_identity, _), result in zip(translation_tasks, results):
                if not isinstance(result, Exception):
                    translations[user_identity] = result
                else:
                    logging.error(f"Translation failed for {user_identity}: {result}")
        
        return translations

    def _get_livekit_api(self) -> api.LiveKitAPI:
        """Get or create LiveKit API client"""
        if self._livekit_api is None:
            settings = get_settings()
            self._livekit_api = api.LiveKitAPI(
                url=settings.livekit_url,
                api_key=settings.livekit_api_key,
                api_secret=settings.livekit_api_secret
            )
        return self._livekit_api

    async def dispatch_agent_to_room(self, room_name: str, user_identity: str = None, agent_name: str = None) -> dict:
        """Manually dispatch a translation agent to an existing room"""
        try:
            lkapi = self._get_livekit_api()
            
            # Prepare metadata for the agent
            agent_metadata = {"dispatched_manually": True}
            
            if user_identity:
                # Get user profile if specific user is provided
                profile = await self.room_manager.get_user_profile(user_identity)
                if profile:
                    agent_metadata.update({
                        "user_identity": user_identity,
                        "native_language": profile.native_language.value,
                        "translation_preferences": profile.translation_preferences,
                    })
                else:
                    # Create default metadata
                    agent_metadata.update({
                        "user_identity": user_identity,
                        "native_language": "en",
                        "translation_preferences": {"formal_tone": False, "preserve_emotion": True}
                    })
            
            # Create the dispatch request
            dispatch_request = api.CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=json.dumps(agent_metadata)
            )
            
            # Dispatch the agent
            dispatch = await lkapi.agent_dispatch.create_dispatch(dispatch_request)
            
            logging.info(f"Agent dispatched to room {room_name}: {dispatch}")
            
            return {
                "success": True,
                "dispatch_id": dispatch.id,
                "room_name": room_name,
                "agent_name": "translation-agent",
                "metadata": agent_metadata
            }
            
        except Exception as e:
            logging.error(f"Failed to dispatch agent to room {room_name}: {e}")
            raise Exception(f"Agent dispatch failed: {str(e)}")

    async def list_agent_dispatches(self, room_name: str) -> List[dict]:
        """List all agent dispatches for a room"""
        try:
            lkapi = self._get_livekit_api()
            dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
            
            return [
                {
                    "id": dispatch.id,
                    "agent_name": dispatch.agent_name,
                    "room": dispatch.room,
                    "metadata": dispatch.metadata
                }
                for dispatch in dispatches
            ]
        except Exception as e:
            logging.error(f"Failed to list dispatches for room {room_name}: {e}")
            return []

    async def generate_room_token(self, user_identity: str, room_name: str, metadata: Optional[dict] = None) -> dict:
        """Generate LiveKit room token with agent dispatch"""
        settings = get_settings()

        profile = await self.room_manager.get_user_profile(user_identity)
        if not profile:
            raise ValueError(f"No profile found for user {user_identity}")

        # Prepare agent metadata with user profile information
        agent_metadata = {
            "user_identity": user_identity,
            "native_language": profile.native_language.value,
            "translation_preferences": profile.translation_preferences,
        }
        if metadata:
            agent_metadata.update(metadata)

        # Create room configuration with agent dispatch
        room_config = api.RoomConfiguration(
            agents=[
                api.RoomAgentDispatch(
                    # agent_name="translation-agent",
                    metadata=json.dumps(agent_metadata)
                )
            ]
        )

        # Create the token with basic grants and room configuration
        token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret) \
            .with_identity(user_identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_update_own_metadata=True,
            )) \
            .with_room_config(room_config)
        
        # Add user metadata as well
        if metadata:
            token = token.with_metadata(json.dumps(metadata))
        # print(token.value)
        return {
            "token": token.to_jwt(),
            "ws_url": settings.livekit_url,
            "room_name": room_name,
            "user_profile": {
                "user_identity": profile.user_identity,
                "native_language": profile.native_language.value,
                "voice_avatar": {
                    "voice_id": profile.preferred_voice_avatar.voice_id,
                    "provider": profile.preferred_voice_avatar.provider,
                    "name": profile.preferred_voice_avatar.name,
                },
                "translation_preferences": profile.translation_preferences,
            }
        }
