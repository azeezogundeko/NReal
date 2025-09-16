"""
Proper LiveKit-based real-time translation agent.
Uses LiveKit's AgentSession for seamless audio processing.
"""
import asyncio
import logging
from typing import Dict, Optional, List
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


class TranslationAgent(Agent):
    """
    LiveKit Agent that handles real-time translation.
    
    This agent:
    1. Listens to other participants' speech
    2. Transcribes it using STT
    3. Translates the text using function tools
    4. Speaks the translation using TTS
    """
    
    def __init__(self, user_profile: UserLanguageProfile):
        self.user_profile = user_profile
        self.translation_service = TranslationService()
        self.settings = get_settings()
        
        # Track participants and their languages
        self.participant_languages: Dict[str, SupportedLanguage] = {}
        
        # Initialize with translation instructions
        super().__init__(
            instructions=f"""You are a real-time translation assistant for {user_profile.user_identity}.
            
                        Your role:
                        1. Listen to speech from other participants
                        2. Translate their speech into {user_profile.native_language.value}
                        3. Speak the translation naturally

                        Language preferences:
                        - Target language: {user_profile.native_language.value}
                        - Formal tone: {user_profile.translation_preferences.get('formal_tone', False)}
                        - Preserve emotion: {user_profile.translation_preferences.get('preserve_emotion', True)}

                        Always use the translate_speech function when you hear speech from other participants."""
                                )
        
        logging.info(f"TranslationAgent initialized for {user_profile.user_identity}")
    
    @function_tool()
    async def translate_speech(self, speech_text: str, speaker_identity: str = "unknown") -> str:
        """
        Translate speech from a participant into the user's native language.
        
        Args:
            speech_text: The original speech text to translate
            speaker_identity: Identity of the speaker (optional)
            
        Returns:
            Translated text in the user's native language
        """
        try:
            if not speech_text.strip():
                return ""
            
            # Skip if it's the user's own speech
            if speaker_identity == self.user_profile.user_identity:
                return ""
            
            # Determine source language
            # For now, assume opposite language for 2-user setup
            source_language = SupportedLanguage.SPANISH if self.user_profile.native_language == SupportedLanguage.ENGLISH else SupportedLanguage.ENGLISH
            
            # Get speaker's language if available
            if speaker_identity in self.participant_languages:
                source_language = self.participant_languages[speaker_identity]
            
            # Skip translation if same language
            if source_language == self.user_profile.native_language:
                return ""
            
            # Perform translation
            translated_text = await self.translation_service.translate_text(
                speech_text,
                source_language,
                self.user_profile.native_language,
                self.user_profile.translation_preferences
            )
            
            if translated_text and translated_text != speech_text:
                logging.info(f"Translated: '{speech_text}' -> '{translated_text}' ({source_language.value} -> {self.user_profile.native_language.value})")
                return translated_text
            
            return ""
            
        except Exception as e:
            logging.error(f"Translation error: {e}")
            return ""
    
    def register_participant(self, identity: str, language: SupportedLanguage):
        """Register a participant with their language."""
        self.participant_languages[identity] = language
        logging.info(f"Registered participant: {identity} ({language.value})")
    
    def unregister_participant(self, identity: str):
        """Unregister a participant."""
        self.participant_languages.pop(identity, None)
        logging.info(f"Unregistered participant: {identity}")
    


class LiveKitTranslationService:
    """Service for managing LiveKit-based translation agents with AgentSession."""
    
    def __init__(self):
        self.active_sessions: Dict[str, AgentSession] = {}
        self.active_agents: Dict[str, TranslationAgent] = {}
        self.settings = get_settings()
        logging.info("LiveKitTranslationService initialized")
    
    def _create_stt(self, user_profile: UserLanguageProfile) -> stt.STT:
        """Create optimized STT for the user's language."""
        user_lang = user_profile.native_language
        
        # Map to proper language codes
        # TODO
        # use proper language code for each provider
        # use provider already set by the UI
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
        # TODO
        # Use google gemini instead
        # return openai.LLM(
        #     api_key=self.settings.openai_api_key,
        #     model="gpt-4o-mini",
        # )

        return google.LLM(
            api_key=self.settings.gemini_api_key,
            # model="gemini-2.0-flash",
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
            # Check if ElevenLabs is configured
            if hasattr(self.settings, 'elevenlabs_api_key'):
                from livekit.plugins import elevenlabs
                return elevenlabs.TTS(
                    api_key=self.settings.elevenlabs_api_key,
                    voice=avatar.voice_id,
                    model=avatar.model,
                )
            else:
                # Fallback to Deepgram if ElevenLabs is not configured
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
            # Fallback to Deepgram with a default model for unsupported providers
            return deepgram.TTS(
                api_key=self.settings.deepgram_api_key,
                model="aura-2-thalia-en",  # Use a known working Deepgram model
            )
    
    def _create_vad(self):
        """Create Voice Activity Detection."""
        return silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.5,
        )
    
    async def create_agent(self, user_profile: UserLanguageProfile) -> TranslationAgent:
        """Create a new translation agent."""
        agent = TranslationAgent(user_profile)
        self.active_agents[user_profile.user_identity] = agent
        
        logging.info(f"Created TranslationAgent for {user_profile.user_identity}")
        return agent
    
    async def start_agent(self, user_identity: str, ctx: JobContext) -> bool:
        """Start a translation agent with AgentSession."""
        if user_identity not in self.active_agents:
            return False
        
        agent = self.active_agents[user_identity]
        user_profile = agent.user_profile
        
        # Connect to the room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Create AgentSession with components
        session = AgentSession(
            stt=self._create_stt(user_profile),
            llm=self._create_llm(),
            tts=self._create_tts(user_profile),
            vad=self._create_vad(),
        )
        
        # Register participant event handlers
        @ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_participant_connected(participant, agent))
        
        @ctx.room.on("participant_disconnected") 
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            asyncio.create_task(self._handle_participant_disconnected(participant, agent))
        
        # Start the session
        await session.start(agent, room=ctx.room)
        
        # Store the session
        self.active_sessions[user_identity] = session
        
        logging.info(f"Started AgentSession for {user_identity}")
        return True
    
    async def _handle_participant_connected(self, participant: rtc.RemoteParticipant, agent: TranslationAgent):
        """Handle new participant joining."""
        try:
            # Extract language from participant metadata
            metadata = json.loads(participant.metadata or "{}")
            language = SupportedLanguage(metadata.get("language", "en"))
            
            agent.register_participant(participant.identity, language)
            
        except Exception as e:
            logging.error(f"Error processing participant connection: {e}")
            # Default to English if metadata parsing fails
            agent.register_participant(participant.identity, SupportedLanguage.ENGLISH)
    
    async def _handle_participant_disconnected(self, participant: rtc.RemoteParticipant, agent: TranslationAgent):
        """Handle participant leaving."""
        agent.unregister_participant(participant.identity)
    
    async def stop_agent(self, user_identity: str) -> bool:
        """Stop a translation agent."""
        if user_identity not in self.active_agents:
            return False
        
        # Stop the session if it exists
        if user_identity in self.active_sessions:
            session = self.active_sessions[user_identity]
            # Session cleanup is handled automatically by LiveKit
            del self.active_sessions[user_identity]
        
        # Remove the agent
        del self.active_agents[user_identity]
        
        logging.info(f"Stopped TranslationAgent for {user_identity}")
        return True
    
    def get_agent(self, user_identity: str) -> Optional[TranslationAgent]:
        """Get an active agent."""
        return self.active_agents.get(user_identity)
    
    def get_active_agents(self) -> Dict[str, TranslationAgent]:
        """Get all active agents."""
        return self.active_agents.copy()
