"""
BizForge AI Service
Centralized Groq Cloud integration for all AI-powered features.
"""

import time
import logging
from groq import Groq
from app.config import get_settings
from app.prompts.templates import (
    SYSTEM_PROMPT,
    BRAND_NAME_PROMPT,
    MARKETING_CONTENT_PROMPT,
    CHAT_SYSTEM_PROMPT,
    SENTIMENT_ANALYSIS_PROMPT,
    DESIGN_PALETTE_PROMPT,
    LOGO_PROMPT_GENERATION
)

logger = logging.getLogger("bizforge.ai")


class GroqAIService:
    """
    Centralized AI service for BizForge using Groq Cloud.
    All AI interactions are handled through this service.
    """
    
    def __init__(self):
        """Initialize the Groq AI client."""
        self.settings = get_settings()
        
        if not self.settings.groq_api_key or self.settings.groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Please set it in your .env file. "
                "Get a key from: https://console.groq.com/keys"
            )
        
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.model = self.settings.model_name

    def _generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_retries: int = 2) -> str:
        """
        Core generation method using Groq with retry logic.
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=2048,
                    timeout=30.0
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                logger.warning(f"Groq API attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
        raise last_error
    
    def _chat_generate(self, messages: list, temperature: float = 0.7, max_retries: int = 2) -> str:
        """
        Chat generation with conversation history and retry logic.
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=2048,
                    timeout=30.0
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                logger.warning(f"Groq chat API attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
        raise last_error
    
    def generate_brand_names(
        self,
        industry: str,
        keywords: list,
        style: str = "modern",
        target_audience: str = "general",
        context: str = ""
    ) -> str:
        """Generate creative brand name suggestions."""
        user_prompt = BRAND_NAME_PROMPT.format(
            industry=industry,
            keywords=", ".join(keywords),
            style=style,
            target_audience=target_audience,
            context=context if context else "None specified"
        )
        return self._generate(SYSTEM_PROMPT, user_prompt, temperature=0.8)
    
    def generate_marketing_content(
        self,
        brand_name: str,
        brand_description: str,
        content_type: str,
        target_audience: str,
        tone: str = "professional",
        key_message: str = "",
        cta: str = ""
    ) -> str:
        """Generate marketing content for various channels."""
        user_prompt = MARKETING_CONTENT_PROMPT.format(
            brand_name=brand_name,
            brand_description=brand_description,
            content_type=content_type,
            target_audience=target_audience,
            tone=tone,
            key_message=key_message if key_message else "Not specified",
            cta=cta if cta else "Not specified"
        )
        return self._generate(SYSTEM_PROMPT, user_prompt, temperature=0.7)
    
    def chat(
        self,
        message: str,
        conversation_history: list = None,
        business_context: str = ""
    ) -> str:
        """Branding consultant chatbot interaction."""
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        
        # Add business context if provided
        if business_context:
            messages.append({
                "role": "system",
                "content": f"Business Context: {business_context}"
            })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return self._chat_generate(messages, temperature=0.7)
    
    def analyze_sentiment(self, text: str, context: str = "general brand feedback") -> str:
        """Analyze sentiment of text for brand insights."""
        user_prompt = SENTIMENT_ANALYSIS_PROMPT.format(
            text=text,
            context=context
        )
        return self._generate(SYSTEM_PROMPT, user_prompt, temperature=0.3)
    
    def generate_color_palette(
        self,
        brand_name: str,
        industry: str,
        brand_personality: str,
        target_audience: str,
        mood: str = "professional",
        existing_colors: str = ""
    ) -> str:
        """Generate color palette and design system recommendations."""
        user_prompt = DESIGN_PALETTE_PROMPT.format(
            brand_name=brand_name,
            industry=industry,
            brand_personality=brand_personality,
            target_audience=target_audience,
            mood=mood,
            existing_colors=existing_colors if existing_colors else "None specified"
        )
        return self._generate(SYSTEM_PROMPT, user_prompt, temperature=0.6)
    
    def generate_logo_prompt(
        self,
        brand_name: str,
        industry: str,
        brand_values: str,
        style: str = "modern minimalist",
        icon_preferences: str = "",
        colors: str = ""
    ) -> str:
        """Generate text-to-image prompts for logo design."""
        user_prompt = LOGO_PROMPT_GENERATION.format(
            brand_name=brand_name,
            industry=industry,
            brand_values=brand_values,
            style=style,
            icon_preferences=icon_preferences if icon_preferences else "Open to suggestions",
            colors=colors if colors else "Open to suggestions"
        )
        return self._generate(SYSTEM_PROMPT, user_prompt, temperature=0.8)


# Singleton instance
_ai_service = None
_ai_service_error = None


def get_ai_service() -> GroqAIService:
    """Get or create the AI service singleton. Raises ValueError if not configured."""
    global _ai_service, _ai_service_error
    if _ai_service is not None:
        return _ai_service
    if _ai_service_error is not None:
        raise _ai_service_error
    try:
        _ai_service = GroqAIService()
        return _ai_service
    except ValueError as e:
        _ai_service_error = e
        logger.error(f"Failed to initialize AI service: {e}")
        raise
