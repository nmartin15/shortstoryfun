"""
Utility modules for the Short Story Pipeline.

Modules:
- word_count: Word count validation and enforcement
- validation: Distinctiveness and quality checks
- storage: Story persistence to disk
- llm: Local LLM inference for story generation
"""

from .word_count import WordCountValidator, MAX_WORD_COUNT
from .validation import (
    check_distinctiveness,
    validate_premise,
    validate_story_voices,
    detect_cliches,
    detect_generic_archetypes,
    calculate_distinctiveness_score,
)
from .storage import (
    save_story,
    load_story,
    load_all_stories,
    update_story as update_story_storage,
    delete_story,
    list_stories,
)
from .llm import (
    LLMClient,
    get_default_client,
    generate_story_draft,
    revise_story_text,
    generate_outline_structure,
    generate_scaffold_structure,
)
from .repository import (
    StoryRepository,
    DatabaseStoryRepository,
    FileStoryRepository,
    create_story_repository,
)

__all__ = [
    "WordCountValidator",
    "MAX_WORD_COUNT",
    "check_distinctiveness",
    "validate_premise",
    "validate_story_voices",
    "detect_cliches",
    "detect_generic_archetypes",
    "calculate_distinctiveness_score",
    "save_story",
    "load_story",
    "load_all_stories",
    "update_story_storage",
    "delete_story",
    "list_stories",
    "LLMClient",
    "get_default_client",
    "generate_story_draft",
    "revise_story_text",
    "generate_outline_structure",
    "generate_scaffold_structure",
    "StoryRepository",
    "DatabaseStoryRepository",
    "FileStoryRepository",
    "create_story_repository",
]

