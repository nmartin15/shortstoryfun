"""
LLM Provider Factory.

This module provides factory functions for creating and managing LLM providers.
It handles provider selection based on environment configuration and provides
a default provider instance.
"""

import os
import logging
from typing import Optional

from .gemini import GeminiProvider, DEFAULT_GEMINI_MODEL
from ..utils.llm import BaseLLMClient

logger = logging.getLogger(__name__)

_default_provider: Optional[BaseLLMClient] = None


def create_provider(provider_name: Optional[str] = None, **kwargs) -> BaseLLMClient:
    """
    Create an LLM provider instance.
    
    Args:
        provider_name: Name of provider to create ('gemini' or None for auto-detect)
        **kwargs: Provider-specific configuration (api_key, model_name, temperature, etc.)
        
    Returns:
        BaseLLMClient instance
        
    Raises:
        ValueError: If provider_name is invalid or provider cannot be created
    """
    # Auto-detect provider if not specified
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_name == "gemini":
        model_name = kwargs.get("model_name", os.getenv("LLM_MODEL", DEFAULT_GEMINI_MODEL))
        temperature = kwargs.get("temperature", float(os.getenv("LLM_TEMPERATURE", "0.7")))
        api_key = kwargs.get("api_key")
        
        return GeminiProvider(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Supported providers: gemini"
        )


def get_default_provider() -> BaseLLMClient:
    """
    Get or create the default LLM provider.
    
    Uses environment variables for configuration:
    - LLM_PROVIDER: Provider name (default: 'gemini')
    - GOOGLE_API_KEY: Google API key (required for gemini)
    - LLM_MODEL: Model name (default: gemini-2.5-flash)
    - LLM_TEMPERATURE: Temperature (default: 0.7)
    
    Returns:
        BaseLLMClient instance
    """
    global _default_provider
    
    if _default_provider is None:
        _default_provider = create_provider()
        logger.info(f"Created default LLM provider: {type(_default_provider).__name__}")
    
    return _default_provider


def reset_default_provider() -> None:
    """
    Reset the default provider instance.
    
    This is useful for testing or when configuration changes.
    """
    global _default_provider
    _default_provider = None
    logger.info("Reset default LLM provider")

