"""
Utility modules for the Short Story Pipeline.

This module provides access to commonly used utilities. For better dependency management
and reduced coupling, prefer importing directly from specific submodules when possible.

For example:
    # Preferred: Direct import from submodule
    from shortstory.utils.word_count import WordCountValidator
    from shortstory.utils.validation import detect_cliches
    
    # Also available: Import from utils (for convenience)
    from shortstory.utils import WordCountValidator, create_story_repository
"""

# Only expose the most commonly used, high-level components
# This reduces coupling and makes dependencies explicit

from .repository import StoryRepository, create_story_repository
from .word_count import WordCountValidator, MAX_WORD_COUNT

# Commonly used validation functions (high-level only)
from .validation import (
    check_distinctiveness,
    validate_premise,
    validate_story_voices,
)

__all__ = [
    # Repository (primary interface for storage)
    "StoryRepository",
    "create_story_repository",
    # Word count (commonly used)
    "WordCountValidator",
    "MAX_WORD_COUNT",
    # Validation (commonly used high-level functions)
    "check_distinctiveness",
    "validate_premise",
    "validate_story_voices",
]

# Note: For other utilities, import directly from submodules:
#   - LLM functions: from shortstory.utils.llm import LLMClient, generate_story_draft
#   - Storage functions: from shortstory.utils.storage import save_story, load_story
#   - Validation details: from shortstory.utils.validation import detect_cliches, detect_generic_archetypes
#   - Repository implementations: from shortstory.utils.repository import DatabaseStoryRepository
