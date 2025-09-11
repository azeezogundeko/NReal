"""
LiveKit agent service for user translation agents.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set

from livekit import api, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    tts,
    llm,
    AgentSession,
    Agent,
    function_tool,
)
from livekit.agents.vad import VAD
from livekit.plugins import openai, deepgram, elevenlabs, silero

from app.core.config import get_settings
from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage
from app.services.translation.service import TranslationService
from app.services.livekit.room_manager import PatternBRoomManager


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

    def __init__(self, user_profile: UserLanguageProfile):
        self.user_profile = user_profile
        self.translation_service = TranslationService()
        self.session: Optional[AgentSession] = None
        self.room: Optional[rtc.Room] = None
        self.local_participant: Optional[rtc.LocalParticipant] = None
        self.translation_agent: Optional[TranslationAgent] = None

        # Track participant languages for translation
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        self.active_participants: Set[str] = set()

        # Initialize TTS
        self._init_tts()

    def _init_tts(self):
        """Initialize TTS with user's preferred voice avatar"""
        settings = get_settings()
        avatar = self.user_profile.preferred_voice_avatar

        if avatar.provider == "elevenlabs":
            self.tts = elevenlabs.TTS(
                api_key=settings.elevenlabs_api_key,
                voice=avatar.voice_id,
                model="eleven_turbo_v2_5",
            )
        elif avatar.provider == "openai":
            self.tts = openai.TTS(
                api_key=settings.openai_api_key,
                voice=avatar.voice_id,
                model="tts-1",
            )
        else:
            # Default fallback
            self.tts = elevenlabs.TTS(
                api_key=settings.elevenlabs_api_key,
                voice=avatar.voice_id
            )

    async def start(self, ctx: JobContext):
        """Initialize the user translation agent with AgentSession"""
        self.room = ctx.room
        self.local_participant = ctx.room.local_participant

        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

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

    async def _on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Handle new participant joining"""
        if participant.identity == self.user_profile.user_identity:
            return  # Don't translate our own speech

        logging.info(f"New participant {participant.identity} connected")
        self._register_participant(participant)

    async def _on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Handle participant disconnecting"""
        if participant.identity in self.active_participants:
            self.active_participants.remove(participant.identity)
            self.participant_languages.pop(participant.identity, None)

            # Also unregister from the translation agent
            if self.translation_agent:
                self.translation_agent.unregister_participant(participant.identity)

            logging.info(f"Participant {participant.identity} disconnected")

    async def _on_track_published(self, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Subscribe to audio tracks from other participants"""
        if publication.kind == rtc.TrackKind.KIND_AUDIO and participant.identity != self.user_profile.user_identity:
            await publication.set_subscribed(True)
            logging.info(f"Subscribed to audio track from {participant.identity}")

    async def _create_agent_session(self, ctx: JobContext):
        """Create the main AgentSession for this user"""
        settings = get_settings()

        # Create STT for detecting speaker language (we'll use a generic model initially)
        stt_instance = deepgram.STT(
            api_key=settings.deepgram_api_key,
            model="nova-2-general",
            language="en",  # Default, will be overridden per participant
            interim_results=False,
            punctuate=True,
        )

        # Create translation LLM that can handle multiple languages
        translation_llm = self._create_multi_language_llm()

        # Try to use Silero VAD, fallback gracefully
        try:
            vad = silero.VAD.load()
        except Exception as e:
            logging.warning(f"VAD not available, proceeding without: {e}")
            vad = None

        # Create the custom translation agent
        self.translation_agent = TranslationAgent(self.user_profile, self.translation_service)

        # Sync participant information with the translation agent
        for identity, language in self.participant_languages.items():
            self.translation_agent.register_participant(identity, language)

        # Create the main AgentSession with the custom agent
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
            """Handle speech from any participant"""
            asyncio.create_task(self._handle_user_speech(ev))

        # Also set up additional event handlers for better integration
        @self.session.on("user_started_speaking")
        def on_user_started_speaking(ev):
            """Track when a user starts speaking"""
            participant_identity = self._extract_participant_identity(ev)
            if participant_identity and self.translation_agent:
                self.translation_agent.register_participant(
                    participant_identity,
                    self.participant_languages.get(participant_identity, SupportedLanguage.ENGLISH)
                )
                logging.debug(f"User started speaking: {participant_identity}")

        @self.session.on("user_stopped_speaking")
        def on_user_stopped_speaking(ev):
            """Track when a user stops speaking"""
            participant_identity = self._extract_participant_identity(ev)
            logging.debug(f"User stopped speaking: {participant_identity}")

        # Start the session with the custom agent
        await self.session.start(room=self.room, agent=self.translation_agent)
        logging.info("AgentSession started successfully with TranslationAgent")

    async def _handle_user_speech(self, ev):
        """Handle speech from a participant and translate if needed"""
        try:
            user_message = ev.user_transcript

            # Extract participant identity from the speech event
            # LiveKit speech events should contain participant information
            participant_identity = self._extract_participant_identity(ev)

            # Skip if this is our own speech or we can't identify the speaker
            if not participant_identity or participant_identity == self.user_profile.user_identity:
                logging.debug("Skipping speech processing (own speech or unknown participant)")
                return

            # Update speaker context in the translation LLM
            if hasattr(self, 'translation_llm'):
                self.translation_llm.update_last_speaker(participant_identity)
                self.translation_llm.register_pending_translation(user_message, participant_identity)

            # Get participant's language
            participant_lang = self.participant_languages.get(participant_identity, SupportedLanguage.ENGLISH)

            # Skip translation if same language
            if participant_lang == self.user_profile.native_language:
                logging.debug(f"Skipping translation for {participant_identity} (same language)")
                return

            logging.info(f"Processing speech from {participant_identity}: {user_message[:100]}...")

            # Try using the translation agent's function tool first (more integrated approach)
            if self.translation_agent:
                try:
                    translated_text = await self.translation_agent.translate_speech(
                        user_message,
                        participant_identity
                    )
                except Exception as e:
                    logging.warning(f"Agent translation failed, falling back to direct translation: {e}")
                    translated_text = None
            else:
                translated_text = None

            # Fallback to direct translation if agent approach didn't work
            if not translated_text or translated_text == user_message:
                translated_text = await self.translation_service.translate_text(
                    user_message,
                    participant_lang,
                    self.user_profile.native_language,
                    self.user_profile.translation_preferences
                )

            if translated_text and translated_text != user_message:
                # Send the translated message via TTS
                await self.session.say(translated_text)
                logging.info(f"Translated and sent: {translated_text[:100]}...")
            else:
                logging.debug("Translation resulted in no changes or failed")

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
                    if not chat_ctx.messages or chat_ctx.messages[-1].role != "user":
                        return llm.ChatResponse(content="")

                    user_message = chat_ctx.messages[-1].content

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
    """Service for LiveKit operations."""

    def __init__(self, room_manager: PatternBRoomManager):
        self.room_manager = room_manager
        self.active_agents: Dict[str, UserTranslationAgent] = {}

    async def create_user_agent(self, user_identity: str, ctx: JobContext) -> UserTranslationAgent:
        """Create and start a translation agent for a user"""
        profile = self.room_manager.get_user_profile(user_identity)
        if not profile:
            raise ValueError(f"No profile found for user {user_identity}")

        agent = UserTranslationAgent(profile)
        await agent.start(ctx)
        self.active_agents[user_identity] = agent

        return agent

    def remove_user_agent(self, user_identity: str):
        """Clean up user agent"""
        if user_identity in self.active_agents:
            del self.active_agents[user_identity]
            logging.info(f"Removed agent for user {user_identity}")

    def generate_room_token(self, user_identity: str, room_name: str, metadata: Optional[dict] = None) -> dict:
        """Generate LiveKit room token"""
        settings = get_settings()

        profile = self.room_manager.get_user_profile(user_identity)
        if not profile:
            raise ValueError(f"No profile found for user {user_identity}")

        token_metadata = {
            "language": profile.native_language.value,
            "voice_avatar": {
                "voice_id": profile.preferred_voice_avatar.voice_id,
                "provider": profile.preferred_voice_avatar.provider,
                "name": profile.preferred_voice_avatar.name,
            },
            **(metadata or {})
        }

        token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret) \
            .with_identity(user_identity) \
            .with_metadata(token_metadata) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))

        return {
            "token": token.to_jwt(),
            "ws_url": settings.livekit_ws_url,
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
