# Modern Multilingual Agent using LiveKit Agents SDK
# Based on the multi-agent pattern from the LiveKit blog

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.job import get_current_job_context
from livekit.agents.llm import function_tool
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import google
# from app.core.livekit_import import deepgram, openai, silero, spitch
# Import plugins with fallbacks for problematic dependencies
try:
    from livekit.plugins import openai, silero
    from livekit.plugins import spitch
    PLUGINS_AVAILABLE = True
except ImportError as e:
    PLUGINS_AVAILABLE = False
    print(f"Warning: Could not import all plugins. Some providers may not be available. Error: {e}")

# Con
# Logger & Environment Setup
logger = logging.getLogger("multilingual-agent")
load_dotenv()

# Common instructions for all agents
common_instructions = (
    "You are a helpful multilingual AI assistant that can communicate in English, Yoruba, Hausa, and Igbo. "
    "You provide cultural context, translations, and authentic communication in each language. "
    "Be friendly, respectful, and culturally sensitive in all interactions."
)

# Voice configuration dataclass
@dataclass
class VoiceConfig:
    language: str
    voice_name: str
    gender: str
    description: str

# Available voices by language
AVAILABLE_VOICES = {
    "yoruba": [
        VoiceConfig("yoruba", "sade", "feminine", "Energetic, but breezy"),
        VoiceConfig("yoruba", "funmi", "feminine", "Calm, can sometimes be fun"),
        VoiceConfig("yoruba", "segun", "masculine", "Vibrant, yet cool"),
        VoiceConfig("yoruba", "femi", "masculine", "Really fun guy to interact with"),
    ],
    "hausa": [
        VoiceConfig("hausa", "hasan", "masculine", "Loud and clear voice"),
        VoiceConfig("hausa", "amina", "feminine", "A bit quiet and soft"),
        VoiceConfig("hausa", "zainab", "feminine", "Clear, loud voice"),
        VoiceConfig("hausa", "aliyu", "masculine", "Soft voice, cool tone"),
    ],
    "igbo": [
        VoiceConfig("igbo", "obinna", "masculine", "Loud and clear voice"),
        VoiceConfig("igbo", "ngozi", "feminine", "A bit quiet and soft"),
        VoiceConfig("igbo", "amara", "feminine", "Clear, loud voice"),
        VoiceConfig("igbo", "ebuka", "masculine", "Soft voice, cool tone"),
    ],
    "english": [
        VoiceConfig("english", "john", "masculine", "Loud and clear voice"),
        VoiceConfig("english", "lucy", "feminine", "Very clear voice"),
        VoiceConfig("english", "lina", "feminine", "Clear, loud voice"),
        VoiceConfig("english", "jude", "masculine", "Deep voice, smooth"),
        VoiceConfig("english", "henry", "masculine", "Soft voice, cool tone"),
        VoiceConfig("english", "kani", "feminine", "Soft voice, cool tone"),
    ]
}

# Shared state dataclass
@dataclass
class MultilingualData:
    current_language: Optional[str] = None
    user_name: Optional[str] = None
    user_location: Optional[str] = None
    conversation_topic: Optional[str] = None
    cultural_context: Optional[str] = None
    preferred_voice_gender: Optional[str] = None  # "masculine" or "feminine"
    preferred_voice_characteristic: Optional[str] = None  # "breezy", "calm", "loud", "soft", etc.
    selected_voice: Optional[str] = None  # Specific voice name

def get_voice_for_language(language: str, userdata: MultilingualData) -> str:
    """Get the appropriate voice for a language based on user preferences."""
    language_key = language.lower()
    
    if language_key not in AVAILABLE_VOICES:
        return "kani"  # Default fallback
    
    available_voices = AVAILABLE_VOICES[language_key]
    
    # If user has a specific voice selected, use it
    if userdata.selected_voice:
        for voice in available_voices:
            if voice.voice_name.lower() == userdata.selected_voice.lower():
                return voice.voice_name
    
    # Filter by gender preference
    if userdata.preferred_voice_gender:
        gender_voices = [v for v in available_voices if v.gender == userdata.preferred_voice_gender]
        if gender_voices:
            available_voices = gender_voices
    
    # Filter by characteristic preference
    if userdata.preferred_voice_characteristic:
        char_voices = []
        for voice in available_voices:
            if userdata.preferred_voice_characteristic.lower() in voice.description.lower():
                char_voices.append(voice)
        if char_voices:
            available_voices = char_voices
    
    # Return the first available voice (or default)
    return available_voices[0].voice_name if available_voices else "kani"

def get_voice_options_text(language: str) -> str:
    """Get a formatted text of available voices for a language."""
    language_key = language.lower()
    if language_key not in AVAILABLE_VOICES:
        return "Default voice available"
    
    voices = AVAILABLE_VOICES[language_key]
    voice_list = []
    
    for voice in voices:
        voice_list.append(f"- {voice.voice_name.title()} ({voice.gender}): {voice.description}")
    
    return "\n".join(voice_list)

# Welcome Agent - Initial language selection
class WelcomeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=f"{common_instructions} "
            "Your goal is to welcome users and help them choose their preferred language and voice. "
            "Ask them to choose their preferred language or start speaking in their language. "
            "Also ask about their voice preference (masculine/feminine and characteristics like 'breezy', 'calm', 'loud', 'soft'). "
            "Be warm and inviting. Start with a multilingual greeting."
        )

    async def on_enter(self):
        # Generate initial greeting when agent becomes active
        self.session.generate_reply()

    @function_tool
    async def language_selected(
        self,
        context: RunContext[MultilingualData],
        language: str,
        user_name: Optional[str] = None,
        user_location: Optional[str] = None,
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Called when the user has selected their preferred language and voice.
        
        Args:
            language: The selected language (English, Yoruba, Hausa, or Igbo)
            user_name: Optional user name if provided
            user_location: Optional user location if provided
            voice_gender: Preferred voice gender (masculine/feminine)
            voice_characteristic: Preferred voice characteristic (breezy, calm, loud, soft, etc.)
            specific_voice: Specific voice name if mentioned
        """
        context.userdata.current_language = language
        if user_name:
            context.userdata.user_name = user_name
        if user_location:
            context.userdata.user_location = user_location
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if specific_voice:
            context.userdata.selected_voice = specific_voice

        # Create appropriate language-specific agent
        if language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        elif language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        elif language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        elif language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        else:
            # Default to English if language not recognized
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)

        # Get the selected voice for the language
        selected_voice = get_voice_for_language(language, context.userdata)
        voice_info = f" with {selected_voice.title()} voice"
        
        return agent, f"Switching to {language} mode{voice_info}. How can I help you today?"

# English Language Agent
class EnglishAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[MultilingualData] = None) -> None:
        name_context = f" The user's name is {user_name}." if user_name else ""
        location_context = f" They are from {user_location}." if user_location else ""
        
        # Get the appropriate voice for English
        selected_voice = "kani"  # Default
        if userdata:
            selected_voice = get_voice_for_language("english", userdata)
        
        super().__init__(
            instructions=f"{common_instructions} "
            "You are now in English mode. Provide helpful assistance in clear, professional English. "
            "Handle general questions, provide information, help with tasks, offer translations to other languages, "
            "and engage in natural conversation. Use American English conventions and be friendly yet professional."
            f"{name_context}{location_context}",
            # Use Spitch STT and TTS for English
            stt=spitch.STT(language="en"),
            tts=spitch.TTS(language="en", voice=selected_voice),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[MultilingualData],
        new_language: str,
    ):
        """Switch to a different language.
        
        Args:
            new_language: The language to switch to (Yoruba, Hausa, Igbo, or English)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Switching to {new_language} mode."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[MultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Configure voice preferences for the current language.
        
        Args:
            voice_gender: Preferred voice gender (masculine/feminine)
            voice_characteristic: Preferred voice characteristic (breezy, calm, loud, soft, etc.)
            specific_voice: Specific voice name if mentioned
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "english", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Voice updated to {new_voice.title()}!"

    @function_tool
    async def end_conversation(self, context: RunContext[MultilingualData]):
        """End the conversation and say goodbye."""
        self.session.interrupt()
        
        goodbye_msg = f"Thank you for using our multilingual assistant! Have a wonderful day!"
        if context.userdata.user_name:
            goodbye_msg = f"Thank you {context.userdata.user_name}! Have a wonderful day!"
        
        await self.session.generate_reply(
            instructions=f"Say goodbye: {goodbye_msg}", 
            allow_interruptions=False
        )
        
        # End the session
        job_ctx = get_current_job_context()
        lkapi = job_ctx.api
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

# Yoruba Language Agent
class YorubaAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[MultilingualData] = None) -> None:
        name_context = f" Orukọ eniyan ni {user_name}." if user_name else ""
        location_context = f" Wọn wa lati {user_location}." if user_location else ""
        
        # Get the appropriate voice for Yoruba
        selected_voice = "sade"  # Default
        if userdata:
            selected_voice = get_voice_for_language("yoruba", userdata)
        
        super().__init__(
            instructions=f"{common_instructions} "
            "O ti wa ni ipo Yoruba bayi. Pese iranwo ni ede Yoruba ti o ye kooro. "
            "Lo awon oro ti o tọ bi 'ẹ jọwọ' (please), 'ẹ ṣe' (thank you), 'bawo ni' (how are you). "
            "Ran awon eniyan lowo pelu awon ibeere, fun ni alaye, ṣe atumọ si awon ede miiran, "
            "ati ṢIS oro tabi gbogbo iru iṣe ti won ba beere. Jẹ ki ibaraenisepo rẹ jẹ atunṣe ati ki o ni itọju."
            f"{name_context}{location_context}",
            # Use Spitch STT and TTS for Yoruba
            stt=spitch.STT(language="yo"),
            tts=spitch.TTS(language="yo", voice=selected_voice),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[MultilingualData],
        new_language: str,
    ):
        """Yi ede pada si ede miiran.
        
        Args:
            new_language: Ede ti a fe yi pada si (English, Hausa, Igbo, tabi Yoruba)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Mo ti yi pada si ipo {new_language}."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[MultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Ṣeto awọn ifẹ ohun ọrọ fun ede lọwọlọwọ.
        
        Args:
            voice_gender: Ifẹ ohun ọrọ ti a fẹ (masculine/feminine)
            voice_characteristic: Ifẹ ohun ọrọ ti a fẹ (breezy, calm, loud, soft, etc.)
            specific_voice: Orukọ ohun ọrọ pataki ti a sọ
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "yoruba", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Ohun ọrọ ti yipada si {new_voice.title()}!"

    @function_tool
    async def end_conversation(self, context: RunContext[MultilingualData]):
        """Pari ibaraenisepo ati so odabo."""
        self.session.interrupt()
        
        goodbye_msg = "E ṣe fun lilo iranwo wa ti o ni ede pupọ! E ni ọjọ ti o dara!"
        if context.userdata.user_name:
            goodbye_msg = f"E ṣe {context.userdata.user_name}! E ni ọjọ ti o dara!"
        
        await self.session.generate_reply(
            instructions=f"Ṣe odabo: {goodbye_msg}", 
            allow_interruptions=False
        )
        
        job_ctx = get_current_job_context()
        lkapi = job_ctx.api
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

# Hausa Language Agent
class HausaAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[MultilingualData] = None) -> None:
        name_context = f" Sunan mai amfani shine {user_name}." if user_name else ""
        location_context = f" Suna daga {user_location}." if user_location else ""
        
        # Get the appropriate voice for Hausa
        selected_voice = "hasan"  # Default
        if userdata:
            selected_voice = get_voice_for_language("hausa", userdata)
        
        super().__init__(
            instructions=f"{common_instructions} "
            "Yanzu kuna cikin yanayin Hausa. Bayar da taimako a cikin Hausa mai kyau. "
            "Yi amfani da kalmomi masu dacewa kamar 'don Allah' (please), 'na gode' (thank you), 'sannu da zuwa' (welcome). "
            "Taimaka wa mutane da tambayoyi, bayar da bayanai, yi fassara zuwa wasu harsuna, "
            "da yin hira akan duk wani batu da suke so. Kasance mai son zuciya kuma mai kulawa."
            f"{name_context}{location_context}",
            # Use Spitch STT and TTS for Hausa
            stt=spitch.STT(language="ha"),
            tts=spitch.TTS(language="ha", voice=selected_voice),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[MultilingualData],
        new_language: str,
    ):
        """Canja zuwa wani harshe.
        
        Args:
            new_language: Harshen da za a canja zuwa (English, Yoruba, Igbo, ko Hausa)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Na canja zuwa yanayin {new_language}."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[MultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Saita abubuwan murya don harshen yanzu.
        
        Args:
            voice_gender: Muryar da ake so (masculine/feminine)
            voice_characteristic: Halin muryar da ake so (breezy, calm, loud, soft, etc.)
            specific_voice: Sunan murya na musamman idan aka ambata
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "hausa", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Murya ta canza zuwa {new_voice.title()}!"

    @function_tool
    async def end_conversation(self, context: RunContext[MultilingualData]):
        """Ƙare tattaunawa da yin sallama."""
        self.session.interrupt()
        
        goodbye_msg = "Na gode da yin amfani da mataimakin mu mai harsuna da yawa! Ku yi kyakkyawan rana!"
        if context.userdata.user_name:
            goodbye_msg = f"Na gode {context.userdata.user_name}! Ku yi kyakkyawan rana!"
        
        await self.session.generate_reply(
            instructions=f"Yi sallama: {goodbye_msg}", 
            allow_interruptions=False
        )
        
        job_ctx = get_current_job_context()
        lkapi = job_ctx.api
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

# Igbo Language Agent
class IgboAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[MultilingualData] = None) -> None:
        name_context = f" Aha onye ọrụ bụ {user_name}." if user_name else ""
        location_context = f" Ha si {user_location}." if user_location else ""
        
        # Get the appropriate voice for Igbo
        selected_voice = "obinna"  # Default
        if userdata:
            selected_voice = get_voice_for_language("igbo", userdata)
        
        super().__init__(
            instructions=f"{common_instructions} "
            "Ị nọ ugbu a n'ọnọdụ Igbo. Nye enyemaka n'asụsụ Igbo dị mma. "
            "Jiri okwu kwesịrị ekwesị dị ka 'biko' (please), 'daalụ' (thank you), 'ndewo' (hello). "
            "Nyere ndị mmadụ aka na ajụjụ ha, nye ozi, tụgharịa asụsụ n'asụsụ ndị ọzọ, "
            "ma kwurịta okwu gbasara ihe ọ bụla ha chọrọ. Bụrụ onye obiọma ma na-elekọta."
            f"{name_context}{location_context}",
            # Use Spitch STT and TTS for Igbo
            stt=spitch.STT(language="ig"),
            tts=spitch.TTS(language="ig", voice=selected_voice),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[MultilingualData],
        new_language: str,
    ):
        """Gbanwee gaa n'asụsụ ọzọ.
        
        Args:
            new_language: Asụsụ a ga-agbanwe gaa (English, Yoruba, Hausa, ma ọ bụ Igbo)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif new_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Agbanwere m gaa ọnọdụ {new_language}."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[MultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Hazie nhọrọ olu maka asụsụ ugbu a.
        
        Args:
            voice_gender: Olu a chọrọ (masculine/feminine)
            voice_characteristic: Àgwà olu a chọrọ (breezy, calm, loud, soft, etc.)
            specific_voice: Aha olu kpọmkwem ma ọ bụrụ na ekwuru ya
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "igbo", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en"]:
            agent = EnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["yoruba", "yo"]:
            agent = YorubaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["hausa", "ha"]:
            agent = HausaAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        elif context.userdata.current_language and context.userdata.current_language.lower() in ["igbo", "ig"]:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = IgboAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Olu gbanwere gaa {new_voice.title()}!"

    @function_tool
    async def end_conversation(self, context: RunContext[MultilingualData]):
        """Kwụsị mkparịta ụka ma sị nke ọma."""
        self.session.interrupt()
        
        goodbye_msg = "Daalụ maka iji onyeinyeaka anyị nwere asụsụ dị iche iche! Nwee ọmarịcha ụbọchị!"
        if context.userdata.user_name:
            goodbye_msg = f"Daalụ {context.userdata.user_name}! Nwee ọmarịcha ụbọchị!"
        
        await self.session.generate_reply(
            instructions=f"Sị nke ọma: {goodbye_msg}", 
            allow_interruptions=False
        )
        
        job_ctx = get_current_job_context()
        lkapi = job_ctx.api
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

# Prewarm function - loads VAD model once
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

# Main entrypoint
async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession[MultilingualData](
        vad=ctx.proc.userdata["vad"],
        # Configure default models - agents can override these
        llm=google.LLM(model="gemini-2.0-flash-001", api_key=os.getenv("GEMINI_API_KEY")),
        stt=spitch.STT(language="en"),  # Default to English STT
        tts=spitch.TTS(language="en", voice="kani"),
        userdata=MultilingualData(),
    )

    # Set up metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session with the WelcomeAgent
    await session.start(
        agent=WelcomeAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # Enable noise cancellation if needed
            # noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
