# Deepgram Voice Configuration Helper
# This file provides easy access to voice configurations and utilities

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class VoiceInfo:
    """Voice information for easy access"""
    model: str
    name: str
    gender: str
    age: str
    language: str
    accent: str
    characteristics: str
    use_cases: str

# Featured English Voices (Recommended)
FEATURED_ENGLISH_VOICES = [
    VoiceInfo("aura-2-thalia-en", "thalia", "feminine", "Adult", "en-us", "American", 
              "Clear, Confident, Energetic, Enthusiastic", "Casual chat, customer service, IVR"),
    VoiceInfo("aura-2-andromeda-en", "andromeda", "feminine", "Adult", "en-us", "American", 
              "Casual, Expressive, Comfortable", "Customer service, IVR"),
    VoiceInfo("aura-2-helena-en", "helena", "feminine", "Adult", "en-us", "American", 
              "Caring, Natural, Positive, Friendly, Raspy", "IVR, casual chat"),
    VoiceInfo("aura-2-apollo-en", "apollo", "masculine", "Adult", "en-us", "American", 
              "Confident, Comfortable, Casual", "Casual chat"),
    VoiceInfo("aura-2-arcas-en", "arcas", "masculine", "Adult", "en-us", "American", 
              "Natural, Smooth, Clear, Comfortable", "Customer service, casual chat"),
    VoiceInfo("aura-2-aries-en", "aries", "masculine", "Adult", "en-us", "American", 
              "Warm, Energetic, Caring", "Casual chat"),
]

# Featured Spanish Voices (Recommended)
FEATURED_SPANISH_VOICES = [
    VoiceInfo("aura-2-celeste-es", "celeste", "feminine", "Young Adult", "es-co", "Colombian", 
              "Clear, Energetic, Positive, Friendly, Enthusiastic", "Casual Chat, Advertising, IVR"),
    VoiceInfo("aura-2-estrella-es", "estrella", "feminine", "Mature", "es-mx", "Mexican", 
              "Approachable, Natural, Calm, Comfortable, Expressive", "Casual Chat, Interview"),
    VoiceInfo("aura-2-nestor-es", "nestor", "masculine", "Adult", "es-es", "Peninsular", 
              "Calm, Professional, Approachable, Clear, Confident", "Casual Chat, Customer Service"),
]

# All Available English Voices
ALL_ENGLISH_VOICES = [
    VoiceInfo("aura-2-amalthea-en", "amalthea", "feminine", "Young Adult", "en-ph", "Filipino", 
              "Engaging, Natural, Cheerful", "Casual chat"),
    VoiceInfo("aura-2-andromeda-en", "andromeda", "feminine", "Adult", "en-us", "American", 
              "Casual, Expressive, Comfortable", "Customer service, IVR"),
    VoiceInfo("aura-2-apollo-en", "apollo", "masculine", "Adult", "en-us", "American", 
              "Confident, Comfortable, Casual", "Casual chat"),
    VoiceInfo("aura-2-arcas-en", "arcas", "masculine", "Adult", "en-us", "American", 
              "Natural, Smooth, Clear, Comfortable", "Customer service, casual chat"),
    VoiceInfo("aura-2-aries-en", "aries", "masculine", "Adult", "en-us", "American", 
              "Warm, Energetic, Caring", "Casual chat"),
    VoiceInfo("aura-2-asteria-en", "asteria", "feminine", "Adult", "en-us", "American", 
              "Clear, Confident, Knowledgeable, Energetic", "Advertising"),
    VoiceInfo("aura-2-athena-en", "athena", "feminine", "Mature", "en-us", "American", 
              "Calm, Smooth, Professional", "Storytelling"),
    VoiceInfo("aura-2-atlas-en", "atlas", "masculine", "Mature", "en-us", "American", 
              "Enthusiastic, Confident, Approachable, Friendly", "Advertising"),
    VoiceInfo("aura-2-aurora-en", "aurora", "feminine", "Adult", "en-us", "American", 
              "Cheerful, Expressive, Energetic", "Interview"),
    VoiceInfo("aura-2-callista-en", "callista", "feminine", "Adult", "en-us", "American", 
              "Clear, Energetic, Professional, Smooth", "IVR"),
    VoiceInfo("aura-2-cora-en", "cora", "feminine", "Adult", "en-us", "American", 
              "Smooth, Melodic, Caring", "Storytelling"),
    VoiceInfo("aura-2-cordelia-en", "cordelia", "feminine", "Young Adult", "en-us", "American", 
              "Approachable, Warm, Polite", "Storytelling"),
    VoiceInfo("aura-2-delia-en", "delia", "feminine", "Young Adult", "en-us", "American", 
              "Casual, Friendly, Cheerful, Breathy", "Interview"),
    VoiceInfo("aura-2-draco-en", "draco", "masculine", "Adult", "en-gb", "British", 
              "Warm, Approachable, Trustworthy, Baritone", "Storytelling"),
    VoiceInfo("aura-2-electra-en", "electra", "feminine", "Adult", "en-us", "American", 
              "Professional, Engaging, Knowledgeable", "IVR, advertising, customer service"),
    VoiceInfo("aura-2-harmonia-en", "harmonia", "feminine", "Adult", "en-us", "American", 
              "Empathetic, Clear, Calm, Confident", "Customer service"),
    VoiceInfo("aura-2-helena-en", "helena", "feminine", "Adult", "en-us", "American", 
              "Caring, Natural, Positive, Friendly, Raspy", "IVR, casual chat"),
    VoiceInfo("aura-2-hera-en", "hera", "feminine", "Adult", "en-us", "American", 
              "Smooth, Warm, Professional", "Informative"),
    VoiceInfo("aura-2-hermes-en", "hermes", "masculine", "Adult", "en-us", "American", 
              "Expressive, Engaging, Professional", "Informative"),
    VoiceInfo("aura-2-hyperion-en", "hyperion", "masculine", "Adult", "en-au", "Australian", 
              "Caring, Warm, Empathetic", "Interview"),
    VoiceInfo("aura-2-iris-en", "iris", "feminine", "Young Adult", "en-us", "American", 
              "Cheerful, Positive, Approachable", "IVR, advertising, customer service"),
    VoiceInfo("aura-2-janus-en", "janus", "feminine", "Adult", "en-us", "American", 
              "Southern, Smooth, Trustworthy", "Storytelling"),
    VoiceInfo("aura-2-juno-en", "juno", "feminine", "Adult", "en-us", "American", 
              "Natural, Engaging, Melodic, Breathy", "Interview"),
    VoiceInfo("aura-2-jupiter-en", "jupiter", "masculine", "Adult", "en-us", "American", 
              "Expressive, Knowledgeable, Baritone", "Informative"),
    VoiceInfo("aura-2-luna-en", "luna", "feminine", "Young Adult", "en-us", "American", 
              "Friendly, Natural, Engaging", "IVR"),
    VoiceInfo("aura-2-mars-en", "mars", "masculine", "Adult", "en-us", "American", 
              "Smooth, Patient, Trustworthy, Baritone", "Customer service"),
    VoiceInfo("aura-2-minerva-en", "minerva", "feminine", "Adult", "en-us", "American", 
              "Positive, Friendly, Natural", "Storytelling"),
    VoiceInfo("aura-2-neptune-en", "neptune", "masculine", "Adult", "en-us", "American", 
              "Professional, Patient, Polite", "Customer service"),
    VoiceInfo("aura-2-odysseus-en", "odysseus", "masculine", "Adult", "en-us", "American", 
              "Calm, Smooth, Comfortable, Professional", "Advertising"),
    VoiceInfo("aura-2-ophelia-en", "ophelia", "feminine", "Adult", "en-us", "American", 
              "Expressive, Enthusiastic, Cheerful", "Interview"),
    VoiceInfo("aura-2-orion-en", "orion", "masculine", "Adult", "en-us", "American", 
              "Approachable, Comfortable, Calm, Polite", "Informative"),
    VoiceInfo("aura-2-orpheus-en", "orpheus", "masculine", "Adult", "en-us", "American", 
              "Professional, Clear, Confident, Trustworthy", "Customer service, storytelling"),
    VoiceInfo("aura-2-pandora-en", "pandora", "feminine", "Adult", "en-gb", "British", 
              "Smooth, Calm, Melodic, Breathy", "IVR, informative"),
    VoiceInfo("aura-2-phoebe-en", "phoebe", "feminine", "Adult", "en-us", "American", 
              "Energetic, Warm, Casual", "Customer service"),
    VoiceInfo("aura-2-pluto-en", "pluto", "masculine", "Adult", "en-us", "American", 
              "Smooth, Calm, Empathetic, Baritone", "Interview, storytelling"),
    VoiceInfo("aura-2-saturn-en", "saturn", "masculine", "Adult", "en-us", "American", 
              "Knowledgeable, Confident, Baritone", "Customer service"),
    VoiceInfo("aura-2-selene-en", "selene", "feminine", "Adult", "en-us", "American", 
              "Expressive, Engaging, Energetic", "Informative"),
    VoiceInfo("aura-2-thalia-en", "thalia", "feminine", "Adult", "en-us", "American", 
              "Clear, Confident, Energetic, Enthusiastic", "Casual chat, customer service, IVR"),
    VoiceInfo("aura-2-theia-en", "theia", "feminine", "Adult", "en-au", "American", 
              "Expressive, Polite, Sincere", "Informative"),
    VoiceInfo("aura-2-vesta-en", "vesta", "feminine", "Adult", "en-us", "American", 
              "Natural, Expressive, Patient, Empathetic", "Customer service, interview, storytelling"),
    VoiceInfo("aura-2-zeus-en", "zeus", "masculine", "Adult", "en-us", "American", 
              "Deep, Trustworthy, Smooth", "IVR"),
]

# All Available Spanish Voices
ALL_SPANISH_VOICES = [
    VoiceInfo("aura-2-sirio-es", "sirio", "masculine", "Adult", "es-mx", "Mexican", 
              "Calm, Professional, Comfortable, Empathetic, Baritone", "Casual Chat, Interview"),
    VoiceInfo("aura-2-nestor-es", "nestor", "masculine", "Adult", "es-es", "Peninsular", 
              "Calm, Professional, Approachable, Clear, Confident", "Casual Chat, Customer Service"),
    VoiceInfo("aura-2-carina-es", "carina", "feminine", "Adult", "es-es", "Peninsular", 
              "Professional, Raspy, Energetic, Breathy, Confident", "Interview, Customer Service, IVR"),
    VoiceInfo("aura-2-celeste-es", "celeste", "feminine", "Young Adult", "es-co", "Colombian", 
              "Clear, Energetic, Positive, Friendly, Enthusiastic", "Casual Chat, Advertising, IVR"),
    VoiceInfo("aura-2-alvaro-es", "alvaro", "masculine", "Adult", "es-es", "Peninsular", 
              "Calm, Professional, Clear, Knowledgeable, Approachable", "Interview, Customer Service"),
    VoiceInfo("aura-2-diana-es", "diana", "feminine", "Adult", "es-es", "Peninsular", 
              "Professional, Confident, Expressive, Polite, Knowledgeable", "Storytelling, Advertising"),
    VoiceInfo("aura-2-aquila-es", "aquila", "masculine", "Adult", "es-419", "Latin American", 
              "Expressive, Enthusiastic, Confident, Casual, Comfortable", "Casual Chat, Informative"),
    VoiceInfo("aura-2-selena-es", "selena", "feminine", "Young Adult", "es-419", "Latin American", 
              "Approachable, Casual, Friendly, Calm, Positive", "Customer Service, Informative"),
    VoiceInfo("aura-2-estrella-es", "estrella", "feminine", "Mature", "es-mx", "Mexican", 
              "Approachable, Natural, Calm, Comfortable, Expressive", "Casual Chat, Interview"),
    VoiceInfo("aura-2-javier-es", "javier", "masculine", "Adult", "es-mx", "Latin American", 
              "Approachable, Professional, Friendly, Comfortable, Calm", "Casual Chat, IVR, Storytelling"),
]

# Codeswitching Voices (can switch between English and Spanish)
CODESWITCHING_VOICES = [
    "aquila", "carina", "diana", "javier", "selena"
]

def get_voice_by_name(name: str, language: str = "english") -> Optional[VoiceInfo]:
    """Get voice information by name and language."""
    voices = ALL_ENGLISH_VOICES if language.lower() == "english" else ALL_SPANISH_VOICES
    
    for voice in voices:
        if voice.name.lower() == name.lower():
            return voice
    return None

def get_voices_by_gender(gender: str, language: str = "english") -> List[VoiceInfo]:
    """Get all voices of a specific gender for a language."""
    voices = ALL_ENGLISH_VOICES if language.lower() == "english" else ALL_SPANISH_VOICES
    
    return [voice for voice in voices if voice.gender.lower() == gender.lower()]

def get_voices_by_accent(accent: str, language: str = "english") -> List[VoiceInfo]:
    """Get all voices with a specific accent for a language."""
    voices = ALL_ENGLISH_VOICES if language.lower() == "english" else ALL_SPANISH_VOICES
    
    return [voice for voice in voices if accent.lower() in voice.accent.lower()]

def get_voices_by_characteristic(characteristic: str, language: str = "english") -> List[VoiceInfo]:
    """Get all voices with a specific characteristic for a language."""
    voices = ALL_ENGLISH_VOICES if language.lower() == "english" else ALL_SPANISH_VOICES
    
    return [voice for voice in voices if characteristic.lower() in voice.characteristics.lower()]

def get_featured_voices(language: str = "english") -> List[VoiceInfo]:
    """Get featured voices for a language."""
    return FEATURED_ENGLISH_VOICES if language.lower() == "english" else FEATURED_SPANISH_VOICES

def is_codeswitching_voice(voice_name: str) -> bool:
    """Check if a voice supports codeswitching between English and Spanish."""
    return voice_name.lower() in CODESWITCHING_VOICES

def get_voice_summary(language: str = "english") -> str:
    """Get a summary of available voices for a language."""
    featured = get_featured_voices(language)
    all_voices = ALL_ENGLISH_VOICES if language.lower() == "english" else ALL_SPANISH_VOICES
    
    summary = f"Featured {language.title()} Voices:\n"
    for voice in featured:
        summary += f"- {voice.name.title()} ({voice.gender}, {voice.accent}): {voice.characteristics}\n"
    
    summary += f"\nTotal {language.title()} voices available: {len(all_voices)}\n"
    summary += f"Codeswitching voices: {', '.join(CODESWITCHING_VOICES)}"
    
    return summary
