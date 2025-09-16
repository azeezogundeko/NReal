# Deepgram Multilingual Agent for Spanish and English
# Using Deepgram Aura-2 voices for high-quality speech synthesis

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

# Import Deepgram plugin
try:
    from livekit.plugins import deepgram
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    DEEPGRAM_AVAILABLE = False
    print(f"Warning: Deepgram plugin not available. Error: {e}")

# Logger & Environment Setup
logger = logging.getLogger("deepgram-multilingual-agent")
load_dotenv()

# Common instructions for all agents
common_instructions = (
    "You are a helpful multilingual AI assistant that can communicate in English and Spanish. "
    "You provide cultural context, translations, and authentic communication in each language. "
    "Be friendly, respectful, and culturally sensitive in all interactions. "
    "You can seamlessly switch between languages and provide accurate translations when needed."
)

# Voice configuration dataclass
@dataclass
class DeepgramVoiceConfig:
    model: str
    name: str
    gender: str
    age: str
    language: str
    accent: str
    characteristics: str
    use_cases: str

# Available Deepgram Aura-2 voices by language
DEEPGRAM_VOICES = {
    "english": [
        # Featured English Voices
        DeepgramVoiceConfig("aura-2-thalia-en", "thalia", "feminine", "Adult", "en-us", "American", 
                           "Clear, Confident, Energetic, Enthusiastic", "Casual chat, customer service, IVR"),
        DeepgramVoiceConfig("aura-2-andromeda-en", "andromeda", "feminine", "Adult", "en-us", "American", 
                           "Casual, Expressive, Comfortable", "Customer service, IVR"),
        DeepgramVoiceConfig("aura-2-helena-en", "helena", "feminine", "Adult", "en-us", "American", 
                           "Caring, Natural, Positive, Friendly, Raspy", "IVR, casual chat"),
        DeepgramVoiceConfig("aura-2-apollo-en", "apollo", "masculine", "Adult", "en-us", "American", 
                           "Confident, Comfortable, Casual", "Casual chat"),
        DeepgramVoiceConfig("aura-2-arcas-en", "arcas", "masculine", "Adult", "en-us", "American", 
                           "Natural, Smooth, Clear, Comfortable", "Customer service, casual chat"),
        DeepgramVoiceConfig("aura-2-aries-en", "aries", "masculine", "Adult", "en-us", "American", 
                           "Warm, Energetic, Caring", "Casual chat"),
        
        # Additional English Voices
        DeepgramVoiceConfig("aura-2-asteria-en", "asteria", "feminine", "Adult", "en-us", "American", 
                           "Clear, Confident, Knowledgeable, Energetic", "Advertising"),
        DeepgramVoiceConfig("aura-2-athena-en", "athena", "feminine", "Mature", "en-us", "American", 
                           "Calm, Smooth, Professional", "Storytelling"),
        DeepgramVoiceConfig("aura-2-atlas-en", "atlas", "masculine", "Mature", "en-us", "American", 
                           "Enthusiastic, Confident, Approachable, Friendly", "Advertising"),
        DeepgramVoiceConfig("aura-2-aurora-en", "aurora", "feminine", "Adult", "en-us", "American", 
                           "Cheerful, Expressive, Energetic", "Interview"),
        DeepgramVoiceConfig("aura-2-callista-en", "callista", "feminine", "Adult", "en-us", "American", 
                           "Clear, Energetic, Professional, Smooth", "IVR"),
        DeepgramVoiceConfig("aura-2-cora-en", "cora", "feminine", "Adult", "en-us", "American", 
                           "Smooth, Melodic, Caring", "Storytelling"),
        DeepgramVoiceConfig("aura-2-delia-en", "delia", "feminine", "Young Adult", "en-us", "American", 
                           "Casual, Friendly, Cheerful, Breathy", "Interview"),
        DeepgramVoiceConfig("aura-2-draco-en", "draco", "masculine", "Adult", "en-gb", "British", 
                           "Warm, Approachable, Trustworthy, Baritone", "Storytelling"),
        DeepgramVoiceConfig("aura-2-electra-en", "electra", "feminine", "Adult", "en-us", "American", 
                           "Professional, Engaging, Knowledgeable", "IVR, advertising, customer service"),
        DeepgramVoiceConfig("aura-2-harmonia-en", "harmonia", "feminine", "Adult", "en-us", "American", 
                           "Empathetic, Clear, Calm, Confident", "Customer service"),
        DeepgramVoiceConfig("aura-2-hera-en", "hera", "feminine", "Adult", "en-us", "American", 
                           "Smooth, Warm, Professional", "Informative"),
        DeepgramVoiceConfig("aura-2-hermes-en", "hermes", "masculine", "Adult", "en-us", "American", 
                           "Expressive, Engaging, Professional", "Informative"),
        DeepgramVoiceConfig("aura-2-hyperion-en", "hyperion", "masculine", "Adult", "en-au", "Australian", 
                           "Caring, Warm, Empathetic", "Interview"),
        DeepgramVoiceConfig("aura-2-iris-en", "iris", "feminine", "Young Adult", "en-us", "American", 
                           "Cheerful, Positive, Approachable", "IVR, advertising, customer service"),
        DeepgramVoiceConfig("aura-2-janus-en", "janus", "feminine", "Adult", "en-us", "American", 
                           "Southern, Smooth, Trustworthy", "Storytelling"),
        DeepgramVoiceConfig("aura-2-juno-en", "juno", "feminine", "Adult", "en-us", "American", 
                           "Natural, Engaging, Melodic, Breathy", "Interview"),
        DeepgramVoiceConfig("aura-2-jupiter-en", "jupiter", "masculine", "Adult", "en-us", "American", 
                           "Expressive, Knowledgeable, Baritone", "Informative"),
        DeepgramVoiceConfig("aura-2-luna-en", "luna", "feminine", "Young Adult", "en-us", "American", 
                           "Friendly, Natural, Engaging", "IVR"),
        DeepgramVoiceConfig("aura-2-mars-en", "mars", "masculine", "Adult", "en-us", "American", 
                           "Smooth, Patient, Trustworthy, Baritone", "Customer service"),
        DeepgramVoiceConfig("aura-2-minerva-en", "minerva", "feminine", "Adult", "en-us", "American", 
                           "Positive, Friendly, Natural", "Storytelling"),
        DeepgramVoiceConfig("aura-2-neptune-en", "neptune", "masculine", "Adult", "en-us", "American", 
                           "Professional, Patient, Polite", "Customer service"),
        DeepgramVoiceConfig("aura-2-odysseus-en", "odysseus", "masculine", "Adult", "en-us", "American", 
                           "Calm, Smooth, Comfortable, Professional", "Advertising"),
        DeepgramVoiceConfig("aura-2-ophelia-en", "ophelia", "feminine", "Adult", "en-us", "American", 
                           "Expressive, Enthusiastic, Cheerful", "Interview"),
        DeepgramVoiceConfig("aura-2-orion-en", "orion", "masculine", "Adult", "en-us", "American", 
                           "Approachable, Comfortable, Calm, Polite", "Informative"),
        DeepgramVoiceConfig("aura-2-orpheus-en", "orpheus", "masculine", "Adult", "en-us", "American", 
                           "Professional, Clear, Confident, Trustworthy", "Customer service, storytelling"),
        DeepgramVoiceConfig("aura-2-pandora-en", "pandora", "feminine", "Adult", "en-gb", "British", 
                           "Smooth, Calm, Melodic, Breathy", "IVR, informative"),
        DeepgramVoiceConfig("aura-2-phoebe-en", "phoebe", "feminine", "Adult", "en-us", "American", 
                           "Energetic, Warm, Casual", "Customer service"),
        DeepgramVoiceConfig("aura-2-pluto-en", "pluto", "masculine", "Adult", "en-us", "American", 
                           "Smooth, Calm, Empathetic, Baritone", "Interview, storytelling"),
        DeepgramVoiceConfig("aura-2-saturn-en", "saturn", "masculine", "Adult", "en-us", "American", 
                           "Knowledgeable, Confident, Baritone", "Customer service"),
        DeepgramVoiceConfig("aura-2-selene-en", "selene", "feminine", "Adult", "en-us", "American", 
                           "Expressive, Engaging, Energetic", "Informative"),
        DeepgramVoiceConfig("aura-2-theia-en", "theia", "feminine", "Adult", "en-au", "American", 
                           "Expressive, Polite, Sincere", "Informative"),
        DeepgramVoiceConfig("aura-2-vesta-en", "vesta", "feminine", "Adult", "en-us", "American", 
                           "Natural, Expressive, Patient, Empathetic", "Customer service, interview, storytelling"),
        DeepgramVoiceConfig("aura-2-zeus-en", "zeus", "masculine", "Adult", "en-us", "American", 
                           "Deep, Trustworthy, Smooth", "IVR"),
    ],
    "spanish": [
        # Featured Spanish Voices
        DeepgramVoiceConfig("aura-2-celeste-es", "celeste", "feminine", "Young Adult", "es-co", "Colombian", 
                           "Clear, Energetic, Positive, Friendly, Enthusiastic", "Casual Chat, Advertising, IVR"),
        DeepgramVoiceConfig("aura-2-estrella-es", "estrella", "feminine", "Mature", "es-mx", "Mexican", 
                           "Approachable, Natural, Calm, Comfortable, Expressive", "Casual Chat, Interview"),
        DeepgramVoiceConfig("aura-2-nestor-es", "nestor", "masculine", "Adult", "es-es", "Peninsular", 
                           "Calm, Professional, Approachable, Clear, Confident", "Casual Chat, Customer Service"),
        
        # Additional Spanish Voices
        DeepgramVoiceConfig("aura-2-sirio-es", "sirio", "masculine", "Adult", "es-mx", "Mexican", 
                           "Calm, Professional, Comfortable, Empathetic, Baritone", "Casual Chat, Interview"),
        DeepgramVoiceConfig("aura-2-carina-es", "carina", "feminine", "Adult", "es-es", "Peninsular", 
                           "Professional, Raspy, Energetic, Breathy, Confident", "Interview, Customer Service, IVR"),
        DeepgramVoiceConfig("aura-2-alvaro-es", "alvaro", "masculine", "Adult", "es-es", "Peninsular", 
                           "Calm, Professional, Clear, Knowledgeable, Approachable", "Interview, Customer Service"),
        DeepgramVoiceConfig("aura-2-diana-es", "diana", "feminine", "Adult", "es-es", "Peninsular", 
                           "Professional, Confident, Expressive, Polite, Knowledgeable", "Storytelling, Advertising"),
        DeepgramVoiceConfig("aura-2-aquila-es", "aquila", "masculine", "Adult", "es-419", "Latin American", 
                           "Expressive, Enthusiastic, Confident, Casual, Comfortable", "Casual Chat, Informative"),
        DeepgramVoiceConfig("aura-2-selena-es", "selena", "feminine", "Young Adult", "es-419", "Latin American", 
                           "Approachable, Casual, Friendly, Calm, Positive", "Customer Service, Informative"),
        DeepgramVoiceConfig("aura-2-javier-es", "javier", "masculine", "Adult", "es-mx", "Latin American", 
                           "Approachable, Professional, Friendly, Comfortable, Calm", "Casual Chat, IVR, Storytelling"),
    ]
}

# Shared state dataclass
@dataclass
class DeepgramMultilingualData:
    current_language: Optional[str] = None
    user_name: Optional[str] = None
    user_location: Optional[str] = None
    conversation_topic: Optional[str] = None
    cultural_context: Optional[str] = None
    preferred_voice_gender: Optional[str] = None  # "masculine" or "feminine"
    preferred_voice_characteristic: Optional[str] = None  # "energetic", "calm", "professional", etc.
    selected_voice: Optional[str] = None  # Specific voice name
    preferred_accent: Optional[str] = None  # "American", "British", "Mexican", "Colombian", etc.

def get_voice_for_language(language: str, userdata: DeepgramMultilingualData) -> DeepgramVoiceConfig:
    """Get the appropriate voice for a language based on user preferences."""
    language_key = language.lower()
    
    if language_key not in DEEPGRAM_VOICES:
        # Default fallback
        if language_key == "english":
            return DEEPGRAM_VOICES["english"][0]  # thalia
        else:
            return DEEPGRAM_VOICES["spanish"][0]  # celeste
    
    available_voices = DEEPGRAM_VOICES[language_key]
    
    # If user has a specific voice selected, use it
    if userdata.selected_voice:
        for voice in available_voices:
            if voice.name.lower() == userdata.selected_voice.lower():
                return voice
    
    # Filter by gender preference
    if userdata.preferred_voice_gender:
        gender_voices = [v for v in available_voices if v.gender == userdata.preferred_voice_gender]
        if gender_voices:
            available_voices = gender_voices
    
    # Filter by accent preference
    if userdata.preferred_accent:
        accent_voices = [v for v in available_voices if userdata.preferred_accent.lower() in v.accent.lower()]
        if accent_voices:
            available_voices = accent_voices
    
    # Filter by characteristic preference
    if userdata.preferred_voice_characteristic:
        char_voices = []
        for voice in available_voices:
            if userdata.preferred_voice_characteristic.lower() in voice.characteristics.lower():
                char_voices.append(voice)
        if char_voices:
            available_voices = char_voices
    
    # Return the first available voice (or default)
    return available_voices[0] if available_voices else DEEPGRAM_VOICES["english"][0]

def get_voice_options_text(language: str) -> str:
    """Get a formatted text of available voices for a language."""
    language_key = language.lower()
    if language_key not in DEEPGRAM_VOICES:
        return "Default voice available"
    
    voices = DEEPGRAM_VOICES[language_key]
    voice_list = []
    
    for voice in voices:
        voice_list.append(f"- {voice.name.title()} ({voice.gender}, {voice.accent}): {voice.characteristics}")
    
    return "\n".join(voice_list)

# Welcome Agent - Initial language selection
class DeepgramWelcomeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=f"{common_instructions} "
            "Your goal is to welcome users and help them choose their preferred language (English or Spanish) and voice. "
            "Ask them to choose their preferred language or start speaking in their language. "
            "Also ask about their voice preference (masculine/feminine, accent, and characteristics). "
            "Be warm and inviting. Start with a bilingual greeting in both English and Spanish."
        )

    async def on_enter(self):
        # Generate initial greeting when agent becomes active
        self.session.generate_reply()

    @function_tool
    async def language_selected(
        self,
        context: RunContext[DeepgramMultilingualData],
        language: str,
        user_name: Optional[str] = None,
        user_location: Optional[str] = None,
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        voice_accent: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Called when the user has selected their preferred language and voice.
        
        Args:
            language: The selected language (English or Spanish)
            user_name: Optional user name if provided
            user_location: Optional user location if provided
            voice_gender: Preferred voice gender (masculine/feminine)
            voice_characteristic: Preferred voice characteristic (energetic, calm, professional, etc.)
            voice_accent: Preferred accent (American, British, Mexican, Colombian, etc.)
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
        if voice_accent:
            context.userdata.preferred_accent = voice_accent
        if specific_voice:
            context.userdata.selected_voice = specific_voice

        # Create appropriate language-specific agent
        if language.lower() in ["english", "en"]:
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        elif language.lower() in ["spanish", "es", "español"]:
            agent = DeepgramSpanishAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)
        else:
            # Default to English if language not recognized
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, userdata=context.userdata)

        # Get the selected voice for the language
        selected_voice = get_voice_for_language(language, context.userdata)
        voice_info = f" with {selected_voice.name.title()} voice ({selected_voice.accent} accent)"
        
        return agent, f"Switching to {language} mode{voice_info}. How can I help you today?"

# English Language Agent with Deepgram
class DeepgramEnglishAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[DeepgramMultilingualData] = None) -> None:
        name_context = f" The user's name is {user_name}." if user_name else ""
        location_context = f" They are from {user_location}." if user_location else ""
        
        # Get the appropriate voice for English
        selected_voice = get_voice_for_language("english", userdata) if userdata else DEEPGRAM_VOICES["english"][0]
        
        super().__init__(
            instructions=f"{common_instructions} "
            "You are now in English mode. Provide helpful assistance in clear, professional English. "
            "Handle general questions, provide information, help with tasks, offer translations to Spanish, "
            "and engage in natural conversation. Use American English conventions and be friendly yet professional. "
            "You can seamlessly switch to Spanish when needed."
            f"{name_context}{location_context}",
            # Use Deepgram STT and TTS for English
            stt=deepgram.STT(model="nova-3", language="en") if DEEPGRAM_AVAILABLE else None,
            tts=deepgram.TTS(model=selected_voice.model) if DEEPGRAM_AVAILABLE else None,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[DeepgramMultilingualData],
        new_language: str,
    ):
        """Switch to a different language.
        
        Args:
            new_language: The language to switch to (Spanish or English)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["spanish", "es", "español"]:
            agent = DeepgramSpanishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Switching to {new_language} mode."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[DeepgramMultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        voice_accent: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Configure voice preferences for the current language.
        
        Args:
            voice_gender: Preferred voice gender (masculine/feminine)
            voice_characteristic: Preferred voice characteristic (energetic, calm, professional, etc.)
            voice_accent: Preferred accent (American, British, etc.)
            specific_voice: Specific voice name if mentioned
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if voice_accent:
            context.userdata.preferred_accent = voice_accent
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "english", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en"]:
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = DeepgramSpanishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Voice updated to {new_voice.name.title()} ({new_voice.accent} accent)!"

    @function_tool
    async def translate_to_spanish(
        self,
        context: RunContext[DeepgramMultilingualData],
        text: str,
    ):
        """Translate English text to Spanish.
        
        Args:
            text: The English text to translate
        """
        # This would typically use a translation service
        # For now, we'll provide a simple response
        return f"I can help translate '{text}' to Spanish. Would you like me to switch to Spanish mode to provide the translation?"

    @function_tool
    async def end_conversation(self, context: RunContext[DeepgramMultilingualData]):
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

# Spanish Language Agent with Deepgram
class DeepgramSpanishAgent(Agent):
    def __init__(self, user_name: Optional[str] = None, user_location: Optional[str] = None, *, chat_ctx: Optional[ChatContext] = None, userdata: Optional[DeepgramMultilingualData] = None) -> None:
        name_context = f" El nombre del usuario es {user_name}." if user_name else ""
        location_context = f" Son de {user_location}." if user_location else ""
        
        # Get the appropriate voice for Spanish
        selected_voice = get_voice_for_language("spanish", userdata) if userdata else DEEPGRAM_VOICES["spanish"][0]
        
        super().__init__(
            instructions=f"{common_instructions} "
            "Ahora estás en modo español. Proporciona asistencia útil en español claro y profesional. "
            "Maneja preguntas generales, proporciona información, ayuda con tareas, ofrece traducciones al inglés, "
            "y participa en conversaciones naturales. Usa convenciones del español y sé amigable pero profesional. "
            "Puedes cambiar sin problemas al inglés cuando sea necesario."
            f"{name_context}{location_context}",
            # Use Deepgram STT and TTS for Spanish
            stt=deepgram.STT(model="nova-3", language="es") if DEEPGRAM_AVAILABLE else None,
            tts=deepgram.TTS(model=selected_voice.model) if DEEPGRAM_AVAILABLE else None,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):
        self.session.generate_reply()

    @function_tool
    async def switch_language(
        self,
        context: RunContext[DeepgramMultilingualData],
        new_language: str,
    ):
        """Cambiar a un idioma diferente.
        
        Args:
            new_language: El idioma al que cambiar (English o Spanish)
        """
        context.userdata.current_language = new_language
        
        if new_language.lower() in ["english", "en", "inglés"]:
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = DeepgramSpanishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"Cambiando al modo {new_language}."

    @function_tool
    async def configure_voice(
        self,
        context: RunContext[DeepgramMultilingualData],
        voice_gender: Optional[str] = None,
        voice_characteristic: Optional[str] = None,
        voice_accent: Optional[str] = None,
        specific_voice: Optional[str] = None,
    ):
        """Configurar preferencias de voz para el idioma actual.
        
        Args:
            voice_gender: Género de voz preferido (masculine/feminine)
            voice_characteristic: Característica de voz preferida (energetic, calm, professional, etc.)
            voice_accent: Acento preferido (Mexican, Colombian, Peninsular, etc.)
            specific_voice: Nombre específico de voz si se menciona
        """
        if voice_gender:
            context.userdata.preferred_voice_gender = voice_gender
        if voice_characteristic:
            context.userdata.preferred_voice_characteristic = voice_characteristic
        if voice_accent:
            context.userdata.preferred_accent = voice_accent
        if specific_voice:
            context.userdata.selected_voice = specific_voice
        
        # Get the new voice for current language
        new_voice = get_voice_for_language(context.userdata.current_language or "spanish", context.userdata)
        
        # Create new agent with updated voice
        if context.userdata.current_language and context.userdata.current_language.lower() in ["english", "en", "inglés"]:
            agent = DeepgramEnglishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        else:
            agent = DeepgramSpanishAgent(context.userdata.user_name, context.userdata.user_location, chat_ctx=context.chat_ctx, userdata=context.userdata)
        
        return agent, f"¡Voz actualizada a {new_voice.name.title()} (acento {new_voice.accent})!"

    @function_tool
    async def translate_to_english(
        self,
        context: RunContext[DeepgramMultilingualData],
        text: str,
    ):
        """Traducir texto español al inglés.
        
        Args:
            text: El texto en español a traducir
        """
        # This would typically use a translation service
        # For now, we'll provide a simple response
        return f"Puedo ayudar a traducir '{text}' al inglés. ¿Te gustaría que cambie al modo inglés para proporcionar la traducción?"

    @function_tool
    async def end_conversation(self, context: RunContext[DeepgramMultilingualData]):
        """Terminar la conversación y despedirse."""
        self.session.interrupt()
        
        goodbye_msg = "¡Gracias por usar nuestro asistente multilingüe! ¡Que tengas un día maravilloso!"
        if context.userdata.user_name:
            goodbye_msg = f"¡Gracias {context.userdata.user_name}! ¡Que tengas un día maravilloso!"
        
        await self.session.generate_reply(
            instructions=f"Despedirse: {goodbye_msg}", 
            allow_interruptions=False
        )
        
        job_ctx = get_current_job_context()
        lkapi = job_ctx.api
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

# Main entrypoint
async def entrypoint(ctx: JobContext):
    if not DEEPGRAM_AVAILABLE:
        logger.error("Deepgram plugin not available. Please install it to use this agent.")
        return
    
    await ctx.connect()

    # Parse metadata from token to get user configuration
    metadata = {}
    if ctx.job.metadata:
        try:
            import json
            metadata = json.loads(ctx.job.metadata)
            logger.info(f"Received metadata: {metadata}")
        except Exception as e:
            logger.warning(f"Failed to parse metadata: {e}")

    # Extract configuration from metadata
    user_preferences = metadata.get("user_preferences", {})
    language = user_preferences.get("language", "en")
    voice = user_preferences.get("voice", "alloy")
    voice_gender = user_preferences.get("voice_gender", "neutral")
    voice_characteristic = user_preferences.get("voice_characteristic", "neutral")

    # Create userdata with configuration
    userdata = DeepgramMultilingualData(
        current_language=language,
        preferred_voice_gender=voice_gender,
        preferred_voice_characteristic=voice_characteristic,
        selected_voice=voice
    )

    # Get the appropriate voice configuration
    selected_voice_config = get_voice_for_language(language, userdata)
    logger.info(f"Selected voice: {selected_voice_config.name} ({selected_voice_config.model}) for language: {language}")

    session = AgentSession[DeepgramMultilingualData](
        # Configure default models - agents can override these
        llm=google.LLM(model="gemini-2.0-flash-001", api_key=os.getenv("GEMINI_API_KEY")),
        stt=deepgram.STT(model="nova-3", language=language),  # Use configured language
        tts=deepgram.TTS(model=selected_voice_config.model),  # Use configured voice
        userdata=userdata,
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

    # Start with appropriate agent based on configuration
    if metadata.get("user_preferences") and language:
        # If we have configuration, start directly with the language-specific agent
        if language.lower() in ["english", "en"]:
            initial_agent = DeepgramEnglishAgent(userdata=userdata)
        elif language.lower() in ["spanish", "es", "español"]:
            initial_agent = DeepgramSpanishAgent(userdata=userdata)
        else:
            # Default to English if language not recognized
            initial_agent = DeepgramEnglishAgent(userdata=userdata)
        
        logger.info(f"Starting with pre-configured {language} agent")
    else:
        # No configuration provided, start with welcome agent
        initial_agent = DeepgramWelcomeAgent()
        logger.info("Starting with welcome agent for language selection")

    await session.start(
        agent=initial_agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
