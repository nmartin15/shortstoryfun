"""
LLM client interface and story generation functions.

This module provides the BaseLLMClient abstract interface and provider-agnostic
utilities for story generation. Concrete provider implementations are in
the providers package (e.g., providers.gemini.GeminiProvider).
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .llm_constants import (
    STORY_DEFAULT_MAX_WORDS,
    DEFAULT_MIN_TOKENS,
    TOKENS_PER_WORD_ESTIMATE,
    TOKEN_BUFFER_MULTIPLIER,
    TOKEN_BUFFER_ADDITION,
    CHARS_PER_TOKEN_ESTIMATE,
    TARGET_WORD_COUNT_RATIO,
)

# Lazy imports for backward compatibility (avoid circular imports)
if TYPE_CHECKING:
    from ..providers.factory import get_default_provider  # noqa: F401
    from ..providers.gemini import GeminiProvider  # noqa: F401

# Initialize logger at module level
logger = logging.getLogger(__name__)

# Note: DEFAULT_MODEL is now provided via __getattr__ for backward compatibility
# It returns the Gemini default model. For provider-agnostic code, don't rely on this constant.


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.
    
    Defines the interface for interacting with LLM providers.
    This allows for multiple provider implementations (Gemini, OpenAI, etc.)
    while maintaining a consistent interface.
    
    Concrete implementations should be in the providers package.
    """
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name being used by this client.
        
        Returns:
            Model name string
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using the configured model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Generation temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def check_availability(self) -> bool:
        """
        Check if the API is available and configured correctly.
        
        Returns:
            True if API is available, False otherwise
        """
        pass


def _estimate_tokens(text: str, model_name: str = "default") -> int:
    """
    Estimate token count for a text string using character-based estimation.
    
    This is a provider-agnostic estimation method. For accurate token counting,
    it is recommended to use the LLM provider's native token counting method
    (e.g., model.count_tokens() for Gemini).
    
    Args:
        text: Text to estimate tokens for
        model_name: Model name (not directly used in this approximation, but kept for interface consistency)
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Character-based estimation (more consistent than mixed approach)
    # Rough estimate: 1 token ≈ 4 characters for English text
    estimated_tokens = len(text) / CHARS_PER_TOKEN_ESTIMATE
    
    # Add a buffer for safety (special tokens, formatting, and general underestimation)
    return int(estimated_tokens * TOKEN_BUFFER_MULTIPLIER) + TOKEN_BUFFER_ADDITION


def _is_story_complete_enough(story_text: str, min_words: int, target_words: int) -> bool:
    """
    Checks if the story is sufficiently long and appears to have a proper ending.
    
    Args:
        story_text: Story text to check
        min_words: Minimum word count required
        target_words: Target word count
        
    Returns:
        True if story is complete enough, False otherwise
    """
    if not story_text:
        return False

    word_count = len(story_text.split())
    stripped = story_text.rstrip()
    ends_with_punctuation = stripped.endswith(('.', '!', '?', '"', "'"))

    # Primary check: meets minimum word count AND ends with punctuation
    if word_count >= min_words and ends_with_punctuation:
        return True
    
    # Secondary check for very short stories that might be complete but below target
    # If it's over 80% of min_words and ends properly, we might accept it.
    if word_count >= min_words * 0.8 and ends_with_punctuation:
        logger.info(f"Story slightly short but ends properly: {word_count} words (min: {min_words})")
        return True
    
    return False


def _continue_story_if_needed(
    story_text: str,
    story_min_words: int,
    target_word_count: int,
    estimated_max_tokens: int,
    client: BaseLLMClient,
    max_continuation_attempts: int = 3
) -> str:
    """
    Continuously attempt to extend the story until it meets length requirements or attempts run out.
    
    Args:
        story_text: Current story text
        story_min_words: Minimum word count required
        target_word_count: Target word count
        estimated_max_tokens: Maximum tokens available
        client: BaseLLMClient instance
        max_continuation_attempts: Maximum number of continuation attempts (default: 3)
        
    Returns:
        Extended story text
    """
    current_story = story_text
    initial_word_count = len(current_story.split()) if current_story else 0
    
    # First, try to add a conclusion if it's long enough but just needs an ending
    if initial_word_count >= story_min_words and not _is_story_complete_enough(current_story, story_min_words, target_word_count):
        logger.warning(f"Story has {initial_word_count} words but doesn't feel complete. Adding conclusion...")
        # Use only last N words for prompt to save tokens
        last_words_for_prompt = " ".join(current_story.split()[-300:])
        conclusion_prompt = f"""This story is {initial_word_count} words but needs a proper conclusion. Add a satisfying ending that resolves the story and feels complete. Write at least 200-400 words.

**Last 300 words:**
{last_words_for_prompt}

**Write a proper conclusion now:**"""
        try:
            conclusion = client.generate(
                prompt=conclusion_prompt,
                system_prompt="Write a satisfying conclusion to this story. Make it feel complete, resolved, and emotionally satisfying. Write at least 200-400 words.",
                temperature=0.8,
                max_tokens=min(3000, estimated_max_tokens),
            )
            current_story += " " + conclusion
            logger.info(f"Added conclusion: {len(conclusion.split())} words (new total: {len(current_story.split())} words)")
            if _is_story_complete_enough(current_story, story_min_words, target_word_count):
                return current_story
        except Exception as e:
            logger.error(f"Failed to add conclusion: {e}", exc_info=True)

    # Now, proceed with general continuation if still needed
    for attempt in range(max_continuation_attempts):
        word_count = len(current_story.split()) if current_story else 0
        if _is_story_complete_enough(current_story, story_min_words, target_word_count):
            logger.info(f"Story length OK and complete after {attempt} continuations: {word_count} words (min: {story_min_words:,}, target: {target_word_count:,})")
            return current_story

        logger.warning(
            f"Attempt {attempt + 1}/{max_continuation_attempts}: Story is too short: {word_count} words (min: {story_min_words:,}, target: {target_word_count:,}). "
            f"Attempting to continue generation..."
        )

        remaining_words = max(story_min_words - word_count, target_word_count - word_count)
        if remaining_words <= 0:  # Should be caught by _is_story_complete_enough, but a safety check
            break 

        # Truncate the story in the prompt to avoid making prompt too long
        story_words_for_prompt = current_story.split()
        story_for_prompt = " ".join(story_words_for_prompt[-500:])  # Use last N words
        if len(story_words_for_prompt) > 500:
            logger.info(f"Truncating story in prompt to last 500 words for continuation (attempt {attempt + 1})")

        continuation_prompt = f"""Continue and complete this short story. It's currently only {word_count} words and MUST reach at least {story_min_words:,} words. Focus on adding more narrative, dialogue, and resolution.

**CRITICAL: You MUST write at least {remaining_words:,} more words. DO NOT STOP until the story is complete and reaches {story_min_words:,} words.**

**Current story (last 500 words):**
{story_for_prompt}

**CONTINUE NOW:**"""

        try:
            # Allocate tokens aggressively, but within overall estimated_max_tokens
            # Note: Provider-specific max token limits should be handled by the provider
            continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)  # More buffer
            allocated_tokens = min(estimated_max_tokens, continuation_tokens_needed)
            allocated_tokens = max(DEFAULT_MIN_TOKENS, allocated_tokens)  # Ensure a minimum reasonable output

            logger.info(
                f"Continuation attempt {attempt + 1}: current={word_count} words, need={remaining_words} more words, "
                f"allocating={allocated_tokens} tokens (calculated needed={continuation_tokens_needed})"
            )
            
            continuation = client.generate(
                prompt=continuation_prompt,
                system_prompt=f"You are completing a short story. The story is currently {word_count} words. Continue writing until the story is FULLY COMPLETE and reaches at least {story_min_words:,} words. Focus on developing plot, character, and resolution.",
                temperature=0.8,
                max_tokens=allocated_tokens,
            )
            
            if continuation:
                current_story += " " + continuation
                logger.info(f"Continuation added: {len(continuation.split())} words (total: {len(current_story.split())} words) for attempt {attempt + 1}")
            else:
                logger.warning(f"LLM returned empty continuation for attempt {attempt + 1}.")
        except Exception as e:
            logger.error(f"Failed to continue story on attempt {attempt + 1}: {e}", exc_info=True)
            # Continue to next attempt if this attempt failed

    final_word_count = len(current_story.split()) if current_story else 0
    if final_word_count < story_min_words:
        logger.error(
            f"CRITICAL: Story is still too short after {max_continuation_attempts} continuations: {final_word_count} words "
            f"(minimum required: {story_min_words:,} words). This may indicate an API issue or model limitation. "
            f"Returning partially generated story."
        )
    
    # Final check to strip metadata from any continuations
    current_story = _strip_metadata_from_story(current_story)
    
    return current_story


def _strip_metadata_from_story(text: str) -> str:
    """
    Remove metadata markers and headers from story text.
    
    Args:
        text: Story text that may contain metadata
        
    Returns:
        Cleaned story text
    """
    if not text:
        return text
    
    # Remove markdown headers that might indicate metadata sections
    patterns = [
        r'^#+\s*(Story|Narrative|Text|Content)\s*$',  # Headers like "# Story"
        r'^##+\s*(Story|Narrative|Text|Content)\s*$',  # Headers like "## Story"
        r'^\*\*Story\*\*:\s*',  # Bold "**Story**:"
        r'^Story:\s*',  # Plain "Story:"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    skip_next_empty = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip metadata headers
        if any(re.match(pattern, stripped, re.IGNORECASE) for pattern in patterns):
            skip_next_empty = True
            continue
        
        # Skip empty line after metadata header
        if skip_next_empty and not stripped:
            skip_next_empty = False
            continue
        
        skip_next_empty = False
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()


def _clean_markdown_from_story(text: str) -> str:
    """
    Remove markdown formatting from story text while preserving content.
    
    Args:
        text: Story text with markdown
        
    Returns:
        Cleaned story text
    """
    if not text:
        return text
    
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers (but keep the text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text.strip()


# Backward compatibility: Import provider factory functions
# These maintain compatibility with existing code while using the new provider architecture
# Imported here to avoid circular imports (providers depend on BaseLLMClient from this module)

def get_default_client() -> BaseLLMClient:
    """
    Get or create the default LLM client.
    
    This is a backward-compatibility wrapper around get_default_provider().
    New code should use get_default_provider() from providers.factory.
    
    Returns:
        BaseLLMClient instance
    """
    from ..providers.factory import get_default_provider
    return get_default_provider()

# Backward compatibility: LLMClient alias
# This is a lazy class reference - importing here would cause circular dependency
# Users should import GeminiProvider directly from providers.gemini for new code
def _get_llm_client_class():
    """Lazy import for backward compatibility."""
    from ..providers.gemini import GeminiProvider
    return GeminiProvider

# Create a class-like alias that will work for both instantiation and isinstance checks
class _LLMClientAlias:
    """Backward compatibility alias for LLMClient."""
    def __new__(cls, *args, **kwargs):
        GeminiProvider = _get_llm_client_class()
        return GeminiProvider(*args, **kwargs)
    
    @classmethod
    def __instancecheck__(cls, instance):
        GeminiProvider = _get_llm_client_class()
        return isinstance(instance, GeminiProvider)

LLMClient = _LLMClientAlias

# Backward compatibility: Re-export Gemini-specific constants and functions
# These are deprecated - new code should import from providers.gemini
def _get_gemini_exports():
    """Lazy import of Gemini-specific exports for backward compatibility."""
    from ..providers.gemini import (
        FALLBACK_ALLOWED_MODELS,
        DEFAULT_GEMINI_MODEL,
        _validate_gemini_model_name,
    )
    return {
        'FALLBACK_ALLOWED_MODELS': FALLBACK_ALLOWED_MODELS,
        'DEFAULT_MODEL': DEFAULT_GEMINI_MODEL,  # Return Gemini default for backward compatibility
        '_validate_model_name': _validate_gemini_model_name,
    }

# Create lazy accessors for backward compatibility
def __getattr__(name: str):
    """Lazy import for backward compatibility exports."""
    if name in ('FALLBACK_ALLOWED_MODELS', 'DEFAULT_MODEL', '_validate_model_name'):
        exports = _get_gemini_exports()
        return exports[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def generate_story_draft(
    idea: str,
    character: Dict[str, Any],
    theme: str,
    outline: Dict[str, Any],
    scaffold: Dict[str, Any],
    genre_config: Dict[str, Any],
    max_words: int = STORY_DEFAULT_MAX_WORDS,
    client: Optional[BaseLLMClient] = None,
) -> str:
    """
    Generate a story draft using LLM.
    
    Args:
        idea: Story idea/premise
        character: Character description
        theme: Story theme
        outline: Story outline
        scaffold: Story scaffold
        genre_config: Genre configuration
        max_words: Maximum word count
        client: Optional LLMClient (uses default if None)
        
    Returns:
        Generated story text
    """
    if client is None:
        client = get_default_client()
    
    # Import here to avoid circular dependency
    from .story_prompt_builder import (
        build_story_system_prompt,
        build_story_user_prompt,
        StoryParams,
        normalize_constraints,
    )
    
    # Build prompts
    system_prompt = build_story_system_prompt()
    
    # Extract character info
    char_name = character.get("name", "the character") if isinstance(character, dict) else "the character"
    char_desc = character.get("description", str(character)) if isinstance(character, dict) else str(character)
    char_quirks = character.get("quirks", []) if isinstance(character, dict) else []
    char_contradictions = character.get("contradictions", "") if isinstance(character, dict) else ""
    
    # Extract outline info
    acts = outline.get("acts", {}) if isinstance(outline, dict) else {}
    beginning_label = acts.get("beginning", "setup")
    middle_label = acts.get("middle", "complication")
    end_label = acts.get("end", "resolution")
    
    # Extract scaffold info
    # Import enums for default values
    from .story_prompt_builder import Tone, Pace
    
    tone = scaffold.get("tone", Tone.BALANCED.value) if isinstance(scaffold, dict) else Tone.BALANCED.value
    pace = scaffold.get("pace", Pace.MODERATE.value) if isinstance(scaffold, dict) else Pace.MODERATE.value
    pov = scaffold.get("pov", "third person") if isinstance(scaffold, dict) else "third person"
    
    # Normalize constraints to ensure proper typing
    raw_constraints = genre_config.get("constraints", {})
    normalized_constraints = normalize_constraints(raw_constraints)
    
    # Build story params
    params = StoryParams(
        idea=idea,
        char_desc=char_desc,
        char_name=char_name,
        char_quirks=char_quirks,
        char_contradictions=char_contradictions,
        theme=theme,
        beginning_label=beginning_label,
        middle_label=middle_label,
        end_label=end_label,
        pov=pov,
        tone=tone,
        pace=pace,
        constraints=normalized_constraints,
        max_words=max_words,
    )
    
    user_prompt, story_min_words, story_max_words, estimated_max_tokens = build_story_user_prompt(params)
    
    # Generate initial draft
    logger.info(f"Generating story draft: target_words={int(max_words * TARGET_WORD_COUNT_RATIO)}, max_words={max_words}")
    story_text = client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.8,
        max_tokens=estimated_max_tokens,
    )
    
    # Clean up the story text
    story_text = _strip_metadata_from_story(story_text)
    story_text = _clean_markdown_from_story(story_text)
    
    # Continue story if needed (client is guaranteed to be non-None here)
    target_word_count = int(max_words * TARGET_WORD_COUNT_RATIO)
    if client is None:
        # This should not happen as get_default_client() is called if None
        raise ValueError("LLM client is required for story continuation")
    story_text = _continue_story_if_needed(
        story_text=story_text,
        story_min_words=story_min_words,
        target_word_count=target_word_count,
        estimated_max_tokens=estimated_max_tokens,
        client=client,
        max_continuation_attempts=3,
    )
    
    return story_text


def revise_story_text(
    text: str,
    revision_notes: List[str],
    current_words: int,
    max_words: int,
    client: Optional[BaseLLMClient] = None,
) -> str:
    """
    Revise story text using LLM.
    
    Args:
        text: Original story text
        revision_notes: List of revision notes
        current_words: Current word count
        max_words: Maximum word count
        client: Optional LLMClient (uses default if None)
        
    Returns:
        Revised story text
    """
    if client is None:
        client = get_default_client()
    
    # Import here to avoid circular dependency
    from .story_prompt_builder import build_revision_system_prompt, build_revision_user_prompt
    
    # Build prompts
    system_prompt = build_revision_system_prompt()
    
    user_prompt, story_min_words, story_max_words, estimated_max_tokens = build_revision_user_prompt(
        text=text,
        revision_notes=revision_notes,
        current_words=current_words,
        max_words=max_words,
    )
    
    # Generate revision
    logger.info(f"Revising story: current_words={current_words}, max_words={max_words}")
    revised_text = client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=estimated_max_tokens,
    )
    
    # Clean up the revised text
    revised_text = _strip_metadata_from_story(revised_text)
    revised_text = _clean_markdown_from_story(revised_text)
    
    return revised_text


def generate_outline_structure(
    premise: Dict[str, Any],
    genre: str,
    genre_config: Dict[str, Any],
    client: Optional[BaseLLMClient] = None,
) -> Dict[str, Any]:
    """
    Generate story outline structure using LLM.
    
    Args:
        premise: Story premise
        genre: Story genre
        genre_config: Genre configuration
        client: Optional LLMClient (uses default if None)
        
    Returns:
        Outline structure dictionary
    """
    if client is None:
        client = get_default_client()
    
    # Simple template-based outline generation
    # In a full implementation, this would use LLM to generate detailed beats
    outline = {
        "genre": genre,
        "framework": genre_config.get("framework", "three-act"),
        "structure": ["beginning", "middle", "end"],
        "acts": {
            "beginning": "Setup and inciting incident",
            "middle": "Rising action and complications",
            "end": "Climax and resolution",
        },
    }
    
    logger.info(f"Generated outline structure for genre: {genre}")
    return outline


def generate_scaffold_structure(
    premise: Dict[str, Any],
    outline: Dict[str, Any],
    genre_config: Dict[str, Any],
    client: Optional[BaseLLMClient] = None,
) -> Dict[str, Any]:
    """
    Generate story scaffold structure using LLM.
    
    Args:
        premise: Story premise
        outline: Story outline
        genre_config: Genre configuration
        client: Optional LLMClient (uses default if None)
        
    Returns:
        Scaffold structure dictionary
    """
    if client is None:
        client = get_default_client()
    
    # Extract constraints from genre config
    constraints = genre_config.get("constraints", {})
    
    # Import enums for default values
    from .story_prompt_builder import Tone, Pace
    
    scaffold = {
        "tone": constraints.get("tone", Tone.BALANCED.value),
        "pace": constraints.get("pace", Pace.MODERATE.value),
        "pov": constraints.get("pov_preference", "flexible"),
        "style": constraints.get("style", "literary"),
    }
    
    logger.info("Generated scaffold structure")
    return scaffold
