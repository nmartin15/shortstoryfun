"""
Google Gemini LLM Provider implementation.

This module provides the GeminiProvider class for interacting with
Google's Generative AI models. All Gemini-specific code is isolated here.
"""

import os
import logging
import time
from typing import Optional, List, TYPE_CHECKING

from ..utils.llm import BaseLLMClient
from ..utils.llm_constants import (
    GEMINI_MAX_OUTPUT_TOKENS,
    DEFAULT_MIN_TOKENS,
    TOKENS_PER_WORD_ESTIMATE,
    TOKEN_BUFFER_MULTIPLIER,
    TOKEN_BUFFER_ADDITION,
    CHARS_PER_TOKEN_ESTIMATE,
)

# Import monitoring utilities (optional)
try:
    from ..utils.monitoring import track_llm_api_call
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    track_llm_api_call = None  # type: ignore

if TYPE_CHECKING:
    # Type stubs for google.generativeai when type checking
    try:
        import google.generativeai as genai_types  # type: ignore
    except ImportError:
        genai_types = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore

logger = logging.getLogger(__name__)

# Gemini-specific model configuration
# Note: Dynamic model management is implemented in GeminiProvider.__init__()
# The client fetches available models from the API at initialization time.
# This fallback list is only used if the API call fails (security risk - should be updated regularly)
FALLBACK_ALLOWED_MODELS: List[str] = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
]

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Model context windows (approximate, in tokens)
GEMINI_CONTEXT_WINDOWS = {
    "gemini-2.5-flash": 1000000,
    "gemini-2.0-flash-exp": 1000000,
    "gemini-1.5-pro": 2000000,
    "gemini-1.5-flash": 1000000,
    "gemini-1.0-pro": 30000,
}

DEFAULT_GEMINI_CONTEXT_WINDOW = 1000000


def _validate_gemini_model_name(model_name: str, available_models: Optional[List[str]] = None) -> str:
    """
    Validate and normalize Gemini model name against dynamically fetched available models.
    
    Args:
        model_name: Model name (with or without 'models/' prefix)
        available_models: List of available model names from API (uses fallback if None)
        
    Returns:
        Normalized model name with 'models/' prefix
        
    Raises:
        ValueError: If model is not in available models
    """
    # Remove 'models/' prefix if present for comparison
    base_name = model_name.replace("models/", "")
    
    # Use provided available_models or fallback
    if available_models is None:
        available_models = FALLBACK_ALLOWED_MODELS
        logger.warning(
            "Using fallback model list. Dynamic model fetching should be used for security. "
            "Fallback models may include deprecated or insecure models."
        )
    
    # Normalize available models (remove 'models/' prefix for comparison)
    normalized_available = [m.replace("models/", "") for m in available_models]
    
    if base_name not in normalized_available:
        raise ValueError(
            f"Invalid Gemini model: {model_name}. Allowed models: {', '.join(normalized_available)}"
        )
    
    # Return with 'models/' prefix
    if not model_name.startswith("models/"):
        return f"models/{base_name}"
    return model_name


def _calculate_gemini_max_output_tokens(
    prompt: str,
    system_prompt: Optional[str] = None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    target_word_count: Optional[int] = None
) -> int:
    """
    Calculate maximum output tokens for Gemini based on prompt size and target word count.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        model_name: Model name
        target_word_count: Target word count for output (if specified)
        
    Returns:
        Maximum output tokens to request
    """
    from ..utils.llm import _estimate_tokens
    
    # Estimate prompt tokens
    prompt_tokens = _estimate_tokens(prompt, model_name)
    if system_prompt:
        prompt_tokens += _estimate_tokens(system_prompt, model_name)
    
    # Get model context window
    context_window = GEMINI_CONTEXT_WINDOWS.get(model_name.replace("models/", ""), DEFAULT_GEMINI_CONTEXT_WINDOW)
    
    # Calculate available output tokens (leave 20% buffer for prompt)
    available_tokens = int(context_window * 0.8) - prompt_tokens
    
    # If target word count is specified, calculate tokens needed
    if target_word_count:
        tokens_needed = int(target_word_count * TOKENS_PER_WORD_ESTIMATE * TOKEN_BUFFER_MULTIPLIER) + TOKEN_BUFFER_ADDITION
        # Use the minimum of: tokens needed, available tokens, max output tokens
        max_tokens = min(tokens_needed, available_tokens, GEMINI_MAX_OUTPUT_TOKENS)
        max_tokens = max(max_tokens, DEFAULT_MIN_TOKENS)  # Ensure minimum
    else:
        # Default to a reasonable output size
        max_tokens = min(available_tokens, GEMINI_MAX_OUTPUT_TOKENS)
        max_tokens = max(max_tokens, DEFAULT_MIN_TOKENS)
    
    return max_tokens


class GeminiProvider(BaseLLMClient):
    """
    Provider for interacting with Google Gemini API.
    
    This class provides a clean interface for generating content using
    Google's Generative AI models. It implements the BaseLLMClient interface
    for provider-agnostic LLM access.
    
    All Gemini-specific code (imports, constants, configuration) is isolated
    in this module to enable easy switching between LLM providers.
    
    Architecture Note:
    This implementation is tightly coupled to the `google.generativeai` module.
    While `BaseLLMClient` provides an abstraction layer, this concrete implementation
    directly imports and uses `google.generativeai`. For better decoupling and testability,
    consider using dependency injection to pass the `genai` module as a dependency
    rather than importing it directly. This would make the class easier to test and
    allow for alternative implementations without modifying the class itself.
    
    Current coupling points:
    - Direct import of `google.generativeai` at module level
    - Direct use of `self._genai.GenerativeModel()` in `generate()`
    - Direct import of `google.generativeai.types.GenerationConfig` in `generate()`
    
    This coupling is acceptable for the current use case but limits flexibility
    for future multi-provider support or testing scenarios. Future refactoring could
    use dependency injection to pass the `genai` module as a constructor parameter.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GEMINI_MODEL,
        temperature: float = 0.7
    ):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
            model_name: Model name (default: gemini-2.5-flash)
            temperature: Generation temperature (default: 0.7)
            
        Raises:
            ImportError: If google.generativeai is not available
            ValueError: If model name is invalid
        """
        if not GENAI_AVAILABLE:
            raise ImportError("google.generativeai is not available. Install it with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        if genai:
            genai.configure(api_key=self.api_key)  # type: ignore[attr-defined]
        
        # Store genai module reference for API calls
        # Use proper type annotation for better IDE support
        if TYPE_CHECKING:
            self._genai: genai_types  # type: ignore
        self._genai = genai  # type: ignore[assignment]
        
        # Fetch available models dynamically for security (prevents using deprecated/insecure models)
        try:
            raw_available_models = list(self._genai.list_models())  # type: ignore
            # Extract model names from the response
            self.available_models = []
            for model in raw_available_models:
                if hasattr(model, 'name'):
                    # Remove 'models/' prefix for consistency
                    model_name_clean = model.name.replace("models/", "")
                    if model_name_clean:  # Only add non-empty names
                        self.available_models.append(model_name_clean)
                elif isinstance(model, str):
                    model_name_clean = model.replace("models/", "")
                    if model_name_clean:  # Only add non-empty names
                        self.available_models.append(model_name_clean)
            
            # Remove duplicates while preserving order
            seen = set()
            self.available_models = [
                m for m in self.available_models 
                if not (m in seen or seen.add(m))
            ]
            
            logger.info(f"Fetched {len(self.available_models)} available Gemini models dynamically")
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error(
                f"Failed to fetch available Gemini models dynamically (network error), using fallback list (security risk): {e}",
                exc_info=True
            )
            # Fallback to predefined list if API call fails
            # This is a security risk as deprecated/insecure models may still be in the list
            self.available_models = FALLBACK_ALLOWED_MODELS.copy()
        except Exception as e:
            # Catch any other unexpected errors (API errors, etc.)
            logger.error(
                f"Failed to fetch available Gemini models dynamically (unexpected error), using fallback list (security risk): {e}",
                exc_info=True
            )
            # Fallback to predefined list if API call fails
            # This is a security risk as deprecated/insecure models may still be in the list
            self.available_models = FALLBACK_ALLOWED_MODELS.copy()
        
        # Validate model name against dynamically fetched list
        self._model_name = _validate_gemini_model_name(model_name, self.available_models)
        self.temperature = temperature
        
        logger.info(f"Initialized GeminiProvider with model: {self._model_name}")
    
    @property
    def model_name(self) -> str:
        """Get the model name being used by this provider."""
        return self._model_name
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using the configured Gemini model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Generation temperature (overrides instance default)
            max_tokens: Maximum output tokens (if None, calculated automatically)
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        start_time = time.time()
        input_tokens = None
        output_tokens = None
        error_type = None
        
        try:
            model = self._genai.GenerativeModel(self.model_name)  # type: ignore
            
            # Build full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Calculate max_tokens if not provided
            if max_tokens is None:
                max_tokens = _calculate_gemini_max_output_tokens(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model_name=self.model_name
                )
            
            # Estimate input tokens for monitoring
            try:
                # Try to use model's count_tokens if available
                input_tokens = model.count_tokens(full_prompt).total_tokens  # type: ignore
            except (AttributeError, TypeError, ValueError) as e:
                # Fallback to estimation if count_tokens fails
                logger.debug(f"Token counting failed, using estimation: {e}")
                from ..utils.llm import _estimate_tokens
                input_tokens = _estimate_tokens(full_prompt, self.model_name)
            
            # Configure generation
            from google.generativeai.types import GenerationConfig  # type: ignore
            generation_config = GenerationConfig(  # type: ignore
                temperature=temperature if temperature is not None else self.temperature,
                max_output_tokens=max_tokens,
            )
            
            # Generate content
            response = model.generate_content(  # type: ignore
                full_prompt,
                generation_config=generation_config,
            )
            
            # Extract usage information if available
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get token count from candidates
                candidate = response.candidates[0]
                if hasattr(candidate, 'token_count'):
                    output_tokens = candidate.token_count
            
            # Estimate output tokens if not available
            if output_tokens is None and response.text:
                from ..utils.llm import _estimate_tokens
                output_tokens = _estimate_tokens(response.text, self.model_name)
            
            # Extract text from response
            if not response.text:
                finish_reason = 'UNKNOWN'
                if hasattr(response, 'candidates') and response.candidates:
                    finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN')
                logger.warning(f"Gemini generation finished with reason: {finish_reason}. No text returned.")
                
                # Track API call with error
                duration = time.time() - start_time
                if MONITORING_AVAILABLE and track_llm_api_call:
                    track_llm_api_call(
                        provider='gemini',
                        model=self.model_name.replace('models/', ''),
                        operation='generate',
                        duration=duration,
                        status='error',
                        input_tokens=input_tokens,
                        output_tokens=0,
                        error_type='no_text_returned'
                    )
                return ""
            
            # CRITICAL: Check finish_reason even when text is returned
            # MAX_TOKENS means the output was truncated and we need to continue
            finish_reason = 'STOP'  # Default assumption
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'STOP')
            
            text = response.text.strip()
            
            # Log finish_reason for debugging
            if finish_reason == 'MAX_TOKENS':
                logger.warning(
                    f"Gemini generation hit MAX_TOKENS limit ({max_tokens} tokens). "
                    f"Output may be truncated. Text length: {len(text)} chars, "
                    f"estimated words: {len(text.split())}"
                )
            else:
                logger.debug(f"Gemini generation finished with reason: {finish_reason}")
            
            # Track successful API call
            duration = time.time() - start_time
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='generate',
                    duration=duration,
                    status='success',
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
            
            return text
            
        except (ConnectionError, TimeoutError, OSError) as e:
            # Network-related errors
            duration = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"Network error generating content with Gemini: {e}", exc_info=True)
            
            # Track API call with error
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='generate',
                    duration=duration,
                    status='error',
                    input_tokens=input_tokens,
                    output_tokens=None,
                    error_type=error_type
                )
            raise
        except (ValueError, TypeError, AttributeError) as e:
            # Configuration or API usage errors
            duration = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"Configuration error generating content with Gemini: {e}", exc_info=True)
            
            # Track API call with error
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='generate',
                    duration=duration,
                    status='error',
                    input_tokens=input_tokens,
                    output_tokens=None,
                    error_type=error_type
                )
            raise
        except Exception as e:
            # Catch-all for other API errors (Google API exceptions, etc.)
            duration = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"Error generating content with Gemini: {e}", exc_info=True)
            
            # Track API call with error
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='generate',
                    duration=duration,
                    status='error',
                    input_tokens=input_tokens,
                    output_tokens=None,
                    error_type=error_type
                )
            raise
    
    def check_availability(self) -> bool:
        """
        Check if the Gemini API is available and configured correctly.
        
        Returns:
            True if API is available, False otherwise
        """
        start_time = time.time()
        try:
            # Check if configured model is in available models list
            base_model = self.model_name.replace("models/", "")
            is_available = base_model in self.available_models
            
            if not is_available:
                logger.warning(
                    f"Configured Gemini model '{self.model_name}' not found in available models: {self.available_models}"
                )
            
            # Track API call
            duration = time.time() - start_time
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='check_availability',
                    duration=duration,
                    status='success' if is_available else 'error',
                    error_type=None if is_available else 'model_not_available'
                )
            
            return is_available
        except (AttributeError, KeyError, TypeError) as e:
            # Configuration or data structure errors
            duration = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"Configuration error checking Gemini API availability: {e}", exc_info=True)
            
            # Track API call with error
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='check_availability',
                    duration=duration,
                    status='error',
                    error_type=error_type
                )
            
            return False
        except Exception as e:
            # Catch-all for other errors
            duration = time.time() - start_time
            error_type = type(e).__name__
            logger.error(f"Error checking Gemini API availability: {e}", exc_info=True)
            
            # Track API call with error
            if MONITORING_AVAILABLE and track_llm_api_call:
                track_llm_api_call(
                    provider='gemini',
                    model=self.model_name.replace('models/', ''),
                    operation='check_availability',
                    duration=duration,
                    status='error',
                    error_type=error_type
                )
            
            return False

