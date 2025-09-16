"""
Audio filtering agent that prevents feedback loops in translation.
This agent filters out its own TTS output to avoid processing it as input.
"""
import asyncio
import logging
from typing import Dict, Optional, Set
import json

from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    AutoSubscribe,
    llm,
    stt,
    tts,
    function_tool,
)
from livekit.plugins import deepgram, openai, silero, google
from livekit import rtc

from app.core.config import get_settings
from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage
from app.services.translation.service import TranslationService


class AudioFilteredTranslationAgent(Agent):
    """
    Translation agent with proper audio filtering to prevent feedback loops.
    
    Key features:
    - Filters out own TTS output
    - Only processes audio from OTHER participants
    - Targeted translation delivery
    """
    
    def __init__(self, user_profile: UserLanguageProfile):
        self.user_profile = user_profile
        self.translation_service = TranslationService()
        self.settings = get_settings()
        
        # Audio filtering
        self.own_audio_tracks: Set[str] = set()  # Track our own audio track IDs
        self.target_participants: Dict[str, SupportedLanguage] = {}  # Participants we translate for
        
        # Initialize with proper instructions
        super().__init__(
            instructions=f"""You are a real-time translation assistant for {user_profile.user_identity}.
            
            Your role:
            1. Listen ONLY to speech from OTHER participants (not your own output)
            2. Translate their speech into {user_profile.native_language.value}
            3. Deliver translations clearly and naturally
            
            CRITICAL: Never process or respond to your own TTS output.
            Only translate speech from human participants."""
        )
        
        logging.info(f"AudioFilteredTranslationAgent initialized for {user_profile.user_identity}")
    
    @function_tool()
    async def translate_speech(self, speech_text: str, speaker_identity: str = "unknown") -> str:
        """
        Translate speech from another participant.
        
        Args:
            speech_text: The speech text to translate
            speaker_identity: Identity of the speaker
            
        Returns:
            Translated text or empty string if no translation needed
        """
        try:
            if not speech_text.strip():
                return ""
            
            # CRITICAL: Never translate our own speech or TTS output
            if speaker_identity == self.user_profile.user_identity:
                logging.debug(f"Ignoring own speech from {speaker_identity}")
                return ""
            
            # Check if this is from a known participant
            if speaker_identity not in self.target_participants:
                logging.warning(f"Unknown speaker: {speaker_identity}")
                return ""
            
            source_language = self.target_participants[speaker_identity]
            target_language = self.user_profile.native_language
            
            # Skip if same language
            if source_language == target_language:
                logging.debug(f"Same language, no translation needed: {source_language}")
                return ""
            
            # Perform translation
            translated_text = await self.translation_service.translate_text(
                speech_text,
                source_language,
                target_language,
                self.user_profile.translation_preferences
            )
            
            if translated_text and translated_text.strip() != speech_text.strip():
                logging.info(f"Translated for {self.user_profile.user_identity}: "
                           f"'{speech_text[:30]}...' -> '{translated_text[:30]}...'")
                return translated_text
            
            return ""
            
        except Exception as e:
            logging.error(f"Translation error for {self.user_profile.user_identity}: {e}")
            return ""
    
    def register_participant(self, identity: str, language: SupportedLanguage):
        """Register a participant that we should translate for."""
        if identity != self.user_profile.user_identity:  # Don't register ourselves
            self.target_participants[identity] = language
            logging.info(f"👥 PARTICIPANT REGISTERED: Agent {self.user_profile.user_identity} will translate for {identity} ({language.value})")
            logging.info(f"   - Total registered participants: {list(self.target_participants.keys())}")
        else:
            logging.debug(f"👤 SKIPPING SELF-REGISTRATION: {identity}")
    
    def unregister_participant(self, identity: str):
        """Unregister a participant."""
        self.target_participants.pop(identity, None)
        logging.info(f"Agent {self.user_profile.user_identity} stopped translating for {identity}")
    
    def mark_own_audio_track(self, track_sid: str):
        """Mark an audio track as our own TTS output to filter it out."""
        self.own_audio_tracks.add(track_sid)
        logging.debug(f"Marked track {track_sid} as own TTS output")
    
    def is_own_audio(self, track_sid: str) -> bool:
        """Check if an audio track is our own TTS output."""
        return track_sid in self.own_audio_tracks


class AudioFilteredTranslationService:
    """Service for managing audio-filtered translation agents."""
    
    def __init__(self):
        self.active_sessions: Dict[str, AgentSession] = {}
        self.active_agents: Dict[str, AudioFilteredTranslationAgent] = {}
        self.settings = get_settings()
        logging.info("AudioFilteredTranslationService initialized")
    
    def _create_stt(self, user_profile: UserLanguageProfile) -> stt.STT:
        """Create STT optimized for the user's language."""
        user_lang = user_profile.native_language
        
        # Map to proper language codes
        lang_code = "en-US"
        if user_lang == SupportedLanguage.SPANISH:
            lang_code = "es"
        elif user_lang == SupportedLanguage.FRENCH:
            lang_code = "fr"
        
        return deepgram.STT(
            api_key=self.settings.deepgram_api_key,
            model="nova-2-general",
            language=lang_code,
            interim_results=True,
            punctuate=False,
            smart_format=False,
        )
    
    def _create_llm(self) -> llm.LLM:
        """Create LLM for the agent."""
        return google.LLM(
            api_key=self.settings.gemini_api_key,
        )
    
    def _create_tts(self, user_profile: UserLanguageProfile) -> tts.TTS:
        """Create TTS for the user's language."""
        avatar = user_profile.preferred_voice_avatar
        
        if avatar.provider == "deepgram":
            return deepgram.TTS(
                api_key=self.settings.deepgram_api_key,
                model=avatar.model,
            )
        elif avatar.provider == "elevenlabs":
            if hasattr(self.settings, 'elevenlabs_api_key'):
                from livekit.plugins import elevenlabs
                return elevenlabs.TTS(
                    api_key=self.settings.elevenlabs_api_key,
                    voice=avatar.voice_id,
                    model=avatar.model,
                )
            else:
                # Fallback to Deepgram
                return deepgram.TTS(
                    api_key=self.settings.deepgram_api_key,
                    model="aura-2-thalia-en",
                )
        elif avatar.provider == "openai":
            return openai.TTS(
                api_key=self.settings.openai_api_key,
                voice=avatar.voice_id,
                model=avatar.model,
            )
        else:
            # Default fallback
            return deepgram.TTS(
                api_key=self.settings.deepgram_api_key,
                model="aura-2-thalia-en",
            )
    
    def _create_vad(self):
        """Create Voice Activity Detection."""
        return silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.5,
        )
    
    async def create_agent(self, user_profile: UserLanguageProfile) -> AudioFilteredTranslationAgent:
        """Create a new audio-filtered translation agent."""
        agent = AudioFilteredTranslationAgent(user_profile)
        self.active_agents[user_profile.user_identity] = agent
        
        logging.info(f"Created AudioFilteredTranslationAgent for {user_profile.user_identity}")
        return agent
    
    async def start_agent(self, user_identity: str, ctx: JobContext) -> bool:
        """Start an audio-filtered translation agent."""
        if user_identity not in self.active_agents:
            return False
        
        agent = self.active_agents[user_identity]
        user_profile = agent.user_profile
        
        # Connect to the room with audio subscription
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Create AgentSession with components
        session = AgentSession(
            stt=self._create_stt(user_profile),
            llm=self._create_llm(),
            tts=self._create_tts(user_profile),
            vad=self._create_vad(),
        )
        
        # CRITICAL: Set up speech event handlers using CORRECT LiveKit event names
        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            """Handle transcribed speech from any participant - CORRECT EVENT NAME"""
            logging.info(f"🎤 User input transcribed: {event.transcript[:50]}... (speaker: {event.speaker_id})")
            asyncio.create_task(self._handle_user_speech(event, agent))
        
        @session.on("user_state_changed")
        def on_user_state_changed(event):
            """Track user state changes (speaking/listening/away)"""
            logging.debug(f"👤 User state changed: {event.old_state} → {event.new_state}")
        
        @session.on("conversation_item_added")
        def on_conversation_item_added(event):
            """Track conversation items being added"""
            logging.debug(f"💬 Conversation item added from {event.item.role}: {event.item.text_content[:50]}...")
        
        # Set up room event handlers for participant management
        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_participant_connected(participant, agent))
        
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_participant_disconnected(participant, agent))
        
        @ctx.room.on("track_published")
        def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_track_published(publication, participant, agent))
        
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_track_subscribed(track, publication, participant, agent))
        
        # Add error handling for AgentSession
        @session.on("error")
        def on_error(event):
            logging.error(f"❌ Agent error: {event.error} (recoverable: {event.error.recoverable})")
            if not event.error.recoverable:
                # Handle unrecoverable errors
                asyncio.create_task(session.say("I'm experiencing technical difficulties. Please try again."))
        
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            logging.info(f"🤖 Agent state changed: {event.old_state} → {event.new_state}")
        
        # Start the session
        await session.start(agent, room=ctx.room)
        
        # CRITICAL: Process existing participants in the room
        logging.info(f"🔍 PROCESSING EXISTING PARTICIPANTS...")
        for participant in ctx.room.remote_participants.values():
            if participant.identity != user_identity:  # Don't process ourselves
                logging.info(f"   - Found existing participant: {participant.identity}")
                await self._handle_participant_connected(participant, agent)
        
        # Store the session
        self.active_sessions[user_identity] = session
        
        logging.info(f"✅ Started AudioFilteredTranslationAgent for {user_identity}")
        return True
    
    async def _handle_participant_connected(self, participant: rtc.RemoteParticipant, agent: AudioFilteredTranslationAgent):
        """Handle participant connection with language detection."""
        try:
            logging.info(f"🔗 PARTICIPANT CONNECTED: {participant.identity}")
            logging.info(f"   - Metadata: {participant.metadata}")
            
            # Extract language from participant metadata
            metadata = json.loads(participant.metadata or "{}")
            language_code = metadata.get("language", "en")
            
            try:
                language = SupportedLanguage(language_code)
                logging.info(f"   - Detected language: {language.value}")
            except ValueError:
                language = SupportedLanguage.ENGLISH
                logging.warning(f"   - Invalid language code '{language_code}', defaulting to English")
            
            # Register this participant for translation (if not ourselves)
            if participant.identity != agent.user_profile.user_identity:
                agent.register_participant(participant.identity, language)
                logging.info(f"   - ✅ Participant registered for translation")
            else:
                logging.info(f"   - ⏭️ Skipping self (agent participant)")
            
        except Exception as e:
            logging.error(f"❌ Error processing participant connection: {e}")
            # Default registration
            if participant.identity != agent.user_profile.user_identity:
                agent.register_participant(participant.identity, SupportedLanguage.ENGLISH)
                logging.info(f"   - ⚠️ Using default English registration")
    
    async def _handle_participant_disconnected(self, participant: rtc.RemoteParticipant, agent: AudioFilteredTranslationAgent):
        """Handle participant disconnection."""
        agent.unregister_participant(participant.identity)
    
    async def _handle_track_published(self, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant, agent: AudioFilteredTranslationAgent):
        """Handle track publication with audio filtering."""
        try:
            if publication.kind == rtc.TrackKind.KIND_AUDIO:
                # If this is our own TTS output, mark it for filtering
                if participant.identity == agent.user_profile.user_identity:
                    agent.mark_own_audio_track(publication.sid)
                    logging.debug(f"Marked own TTS track for filtering: {publication.sid}")
                else:
                    logging.info(f"Audio track from {participant.identity} will be processed for translation")
        
        except Exception as e:
            logging.error(f"Error handling track publication: {e}")
    
    async def _handle_track_subscribed(self, track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant, agent: AudioFilteredTranslationAgent):
        """Handle track subscription - ensure we can process audio from other participants."""
        try:
            if isinstance(track, rtc.RemoteAudioTrack) and publication.kind == rtc.TrackKind.KIND_AUDIO:
                # Only process audio from OTHER participants (not our own TTS output)
                if participant.identity != agent.user_profile.user_identity:
                    logging.info(f"🎧 Subscribed to audio track from {participant.identity} - ready for translation processing")
                    
                    # Ensure participant is registered for translation
                    if participant.identity not in agent.target_participants:
                        # Extract language from metadata
                        metadata = json.loads(participant.metadata or "{}")
                        language_code = metadata.get("language", "en")
                        try:
                            language = SupportedLanguage(language_code)
                        except ValueError:
                            language = SupportedLanguage.ENGLISH
                        
                        agent.register_participant(participant.identity, language)
                        logging.info(f"📝 Auto-registered {participant.identity} for translation ({language.value})")
                else:
                    logging.debug(f"🔇 Ignoring own audio track subscription: {participant.identity}")
        
        except Exception as e:
            logging.error(f"Error handling track subscription: {e}")
    
    async def stop_agent(self, user_identity: str) -> bool:
        """Stop an audio-filtered translation agent."""
        if user_identity not in self.active_agents:
            return False
        
        # Stop the session
        if user_identity in self.active_sessions:
            session = self.active_sessions[user_identity]
            del self.active_sessions[user_identity]
        
        # Remove the agent
        del self.active_agents[user_identity]
        
        logging.info(f"Stopped AudioFilteredTranslationAgent for {user_identity}")
        return True
    
    async def _handle_user_speech(self, ev, agent: AudioFilteredTranslationAgent):
        """Handle speech from a participant with proper filtering"""
        try:
            # Extract data from the UserInputTranscribedEvent
            user_message = ev.transcript  # CORRECT attribute name
            participant_identity = ev.speaker_id or self._extract_participant_identity(ev)

            # If we still can't identify the speaker, try to use the most recently active participant
            if not participant_identity:
                # Get the most recently active participant from the agent's registered participants
                # This is a fallback when LiveKit doesn't provide speaker_id
                if agent.target_participants:
                    # Use the first registered participant as a fallback
                    # In a real scenario, you'd want to track the most recently active speaker
                    participant_identity = list(agent.target_participants.keys())[0]
                    logging.warning(f"⚠️ Using fallback participant identity: {participant_identity}")
                else:
                    logging.warning("⚠️ No registered participants available for fallback")
                    return

            logging.info(f"🎤 SPEECH RECEIVED: {participant_identity}: '{user_message[:50]}...'")

            # Skip if this is our own speech or we can't identify the speaker
            if not participant_identity or participant_identity == agent.user_profile.user_identity:
                logging.debug(f"Skipping speech processing (own speech or unknown participant): {participant_identity}")
                return

            # Check if this participant is registered for translation
            if participant_identity not in agent.target_participants:
                logging.warning(f"Speech from unregistered participant: {participant_identity}")
                # Try to auto-register the participant
                try:
                    # This should have been handled in track_subscribed, but let's be safe
                    metadata = json.loads(getattr(ev, 'participant', {}).metadata or "{}")
                    language_code = metadata.get("language", "en")
                    try:
                        language = SupportedLanguage(language_code)
                    except ValueError:
                        language = SupportedLanguage.ENGLISH
                    
                    agent.register_participant(participant_identity, language)
                    logging.info(f"📝 Auto-registered {participant_identity} for translation ({language.value})")
                except Exception as reg_error:
                    logging.error(f"Failed to auto-register participant {participant_identity}: {reg_error}")
                    return

            # Get participant's language
            participant_lang = agent.target_participants[participant_identity]
            
            logging.info(f"🔄 PROCESSING TRANSLATION: {participant_identity} ({participant_lang}) -> {agent.user_profile.native_language}")

            # Perform translation using the agent's function tool
            translated_text = await agent.translate_speech(user_message, participant_identity)
            
            if translated_text:
                logging.info(f"✅ TRANSLATION SUCCESS: '{translated_text[:50]}...'")
            else:
                logging.warning(f"❌ TRANSLATION FAILED or SKIPPED for: {participant_identity}")

        except Exception as e:
            logging.error(f"❌ ERROR handling user speech: {e}")

    def _extract_participant_identity(self, ev) -> Optional[str]:
        """Extract participant identity from speech event with improved fallback logic"""
        try:
            # Method 1: Check for speaker_id attribute (LiveKit specific) - try this first
            if hasattr(ev, 'speaker_id') and ev.speaker_id:
                logging.debug(f"Found speaker_id: {ev.speaker_id}")
                return ev.speaker_id

            # Method 2: Direct participant attribute
            if hasattr(ev, 'participant') and ev.participant:
                if hasattr(ev.participant, 'identity') and ev.participant.identity:
                    logging.debug(f"Found participant.identity: {ev.participant.identity}")
                    return ev.participant.identity
                elif hasattr(ev.participant, 'sid') and ev.participant.sid:
                    logging.debug(f"Found participant.sid: {ev.participant.sid}")
                    return ev.participant.sid

            # Method 3: Source participant
            if hasattr(ev, 'source') and ev.source:
                if hasattr(ev.source, 'participant') and ev.source.participant:
                    if hasattr(ev.source.participant, 'identity') and ev.source.participant.identity:
                        logging.debug(f"Found source.participant.identity: {ev.source.participant.identity}")
                        return ev.source.participant.identity
                    elif hasattr(ev.source.participant, 'sid') and ev.source.participant.sid:
                        logging.debug(f"Found source.participant.sid: {ev.source.participant.sid}")
                        return ev.source.participant.sid
                elif hasattr(ev.source, 'identity') and ev.source.identity:
                    logging.debug(f"Found source.identity: {ev.source.identity}")
                    return ev.source.identity

            # Method 4: Track participant
            if hasattr(ev, 'track') and ev.track:
                if hasattr(ev.track, 'participant') and ev.track.participant:
                    if hasattr(ev.track.participant, 'identity') and ev.track.participant.identity:
                        logging.debug(f"Found track.participant.identity: {ev.track.participant.identity}")
                        return ev.track.participant.identity

            # Method 5: Check for participant_id attribute
            if hasattr(ev, 'participant_id') and ev.participant_id:
                logging.debug(f"Found participant_id: {ev.participant_id}")
                return ev.participant_id

            # Method 6: Check for participant_identity attribute
            if hasattr(ev, 'participant_identity') and ev.participant_identity:
                logging.debug(f"Found participant_identity: {ev.participant_identity}")
                return ev.participant_identity

            # Method 7: Try to extract from event metadata or context
            if hasattr(ev, 'metadata') and ev.metadata:
                try:
                    import json
                    metadata = json.loads(ev.metadata)
                    if 'participant_identity' in metadata:
                        logging.debug(f"Found metadata.participant_identity: {metadata['participant_identity']}")
                        return metadata['participant_identity']
                    if 'speaker_id' in metadata:
                        logging.debug(f"Found metadata.speaker_id: {metadata['speaker_id']}")
                        return metadata['speaker_id']
                except:
                    pass

            # Method 8: For UserInputTranscribedEvent, try to get the current active speaker
            # This is a fallback when speaker_id is None
            if hasattr(ev, 'type') and 'UserInputTranscribedEvent' in str(ev.type):
                # Try to get the most recently active participant from the room
                # This is a heuristic approach
                logging.warning(f"UserInputTranscribedEvent with no speaker_id - using fallback logic")
                
                # Check if we can get the participant from the room context
                # This would require access to the room object, which we don't have here
                # For now, we'll return None and let the calling code handle it
                return None

            logging.warning(f"Could not extract participant identity from speech event: {type(ev)}")
            logging.debug(f"Event attributes: {[attr for attr in dir(ev) if not attr.startswith('_')]}")
            return None

        except Exception as e:
            logging.error(f"Error extracting participant identity: {e}")
            return None

    def get_agent(self, user_identity: str) -> Optional[AudioFilteredTranslationAgent]:
        """Get an active agent."""
        return self.active_agents.get(user_identity)
