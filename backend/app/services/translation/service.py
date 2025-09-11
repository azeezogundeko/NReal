"""
Translation service for handling text translation with AI providers.
"""
from typing import Dict, Optional

from livekit.agents import llm

from app.core.config import get_settings
from app.models.domain.profiles import SupportedLanguage


class TranslationService:
    """Service for translating text between languages."""

    def __init__(self):
        settings = get_settings()
        self.llm = llm.openai.LLM(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3,
        )

    async def translate_text(
        self,
        text: str,
        source_lang: SupportedLanguage,
        target_lang: SupportedLanguage,
        preferences: Optional[Dict[str, bool]] = None
    ) -> str:
        """Translate text with context preservation and tone matching"""

        if source_lang == target_lang:
            return text

        preferences = preferences or {}

        # Build translation prompt based on preferences
        tone_instruction = "formal and professional" if preferences.get("formal_tone") else "natural and conversational"
        emotion_instruction = "preserve the emotional tone and intensity" if preferences.get("preserve_emotion") else "maintain clarity"

        system_prompt = f"""
        You are an expert real-time translator. Translate the following text from {source_lang.value} to {target_lang.value}.

        Guidelines:
        - Keep the translation {tone_instruction}
        - {emotion_instruction}
        - Maintain cultural context appropriateness
        - Preserve speaker intent and meaning
        - Keep response length similar to original
        - For informal speech, use appropriate colloquialisms in target language

        Respond ONLY with the translated text, no explanations.
        """

        chat_ctx = llm.ChatContext()
        chat_ctx.messages.append(llm.ChatMessage(role="system", content=system_prompt))
        chat_ctx.messages.append(llm.ChatMessage(role="user", content=text))

        response = await self.llm.chat(chat_ctx=chat_ctx)
        return response.content.strip()
