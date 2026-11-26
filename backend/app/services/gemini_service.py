import os
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


def generate_gemini_content(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """
    Calls Google Gemini API (gemini-1.5-flash / gemini-1.5-pro) to generate analytical content.
    Returns generated text or None if API key is not configured or an error occurs.
    """
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or ""
    if not api_key:
        logger.info("GEMINI_API_KEY is not set. Using structured analytical fallback.")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try gemini-1.5-flash first, fallback to gemini-pro
        for model_name in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction if system_instruction else None
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini model {model_name} invocation failed: {e}")
                continue

        return None
    except Exception as exc:
        logger.error(f"Error calling Google Gemini API: {exc}")
        return None
