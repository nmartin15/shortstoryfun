"""
Story service for CRUD operations.

Handles story retrieval, updates, and listing operations.
Note: This is a partial implementation focusing on CRUD operations.
Story generation and revision services will be added after pipeline refactoring.
"""

import logging
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.shortstory.utils.repository import StoryRepository
    from src.shortstory.pipeline import ShortStoryPipeline

from src.shortstory.utils.errors import ValidationError, NotFoundError
from src.shortstory.utils import MAX_WORD_COUNT
from src.shortstory.api.helpers import get_story_body, get_story_repository
from .story_validation_service import StoryValidationService

logger = logging.getLogger(__name__)


class StoryService:
    """Service for story CRUD operations."""
    
    def __init__(
        self,
        repository: Optional['StoryRepository'] = None,
        pipeline_factory: Optional[Callable[[], 'ShortStoryPipeline']] = None
    ):
        """
        Initialize story service.
        
        Args:
            repository: Story repository instance (uses get_story_repository() if None)
            pipeline_factory: Factory function to create pipeline instances for word counting
        """
        self._repository = repository
        self._pipeline_factory = pipeline_factory
        self.validation_service = StoryValidationService()
    
    @property
    def repository(self) -> 'StoryRepository':
        """Get story repository instance."""
        if self._repository is None:
            return get_story_repository()
        return self._repository
    
    def get_story(self, story_id: str) -> Dict[str, Any]:
        """
        Get a story by ID with recalculated metrics.
        
        Args:
            story_id: Story identifier
            
        Returns:
            Story data dictionary with updated word count
            
        Raises:
            NotFoundError: If story not found
        """
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        # Recalculate word count
        if self._pipeline_factory:
            pipeline = self._pipeline_factory()
            body = get_story_body(story)
            word_count = pipeline.word_validator.count_words(body)
            
            # Update story with current metrics
            story["word_count"] = word_count
            story["max_words"] = story.get("max_words", MAX_WORD_COUNT)
        else:
            # Fallback: use existing word count if pipeline not available
            story["word_count"] = story.get("word_count", 0)
            story["max_words"] = story.get("max_words", MAX_WORD_COUNT)
        
        return story
    
    def update_story_body(
        self,
        story_id: str,
        body_text: str
    ) -> Dict[str, Any]:
        """
        Update a story's body text with validation.
        
        Args:
            story_id: Story identifier
            body_text: New story body text
            
        Returns:
            Updated story data dictionary
            
        Raises:
            NotFoundError: If story not found
            ValidationError: If body text is invalid
        """
        # Load story
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        # Validate body text structure
        self.validation_service.validate_story_body(body_text)
        
        # Validate word count (requires pipeline)
        if not self._pipeline_factory:
            raise ValidationError(
                "Word count validation requires pipeline factory. "
                "Please provide pipeline_factory when initializing StoryService."
            )
        
        pipeline = self._pipeline_factory()
        word_count, is_valid = pipeline.word_validator.validate(
            body_text, raise_error=False
        )
        
        if not is_valid:
            raise ValidationError(
                f"Story exceeds word limit ({word_count:,} > {MAX_WORD_COUNT:,} words). "
                "Please reduce the length.",
                details={
                    "word_count": word_count,
                    "max_words": MAX_WORD_COUNT
                }
            )
        
        # Update story
        story["body"] = body_text
        story["word_count"] = word_count
        story["max_words"] = story.get("max_words", MAX_WORD_COUNT)
        
        # Save to repository
        self.repository.update(story_id, {
            "body": body_text,
            "word_count": word_count
        })
        
        return story
    
    def list_stories(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List stories with pagination and optional genre filter.
        
        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 50, max: 100)
            genre: Optional genre filter
            
        Returns:
            Dict with 'stories' list and 'pagination' metadata:
            {
                "stories": [...],
                "pagination": {
                    "page": int,
                    "per_page": int,
                    "total": int,
                    "total_pages": int,
                    "has_next": bool,
                    "has_prev": bool
                }
            }
            
        Raises:
            ValidationError: If pagination parameters or genre format is invalid
        """
        # Validate and normalize pagination parameters
        pagination = self.validation_service.validate_pagination_params(page, per_page)
        page = pagination["page"]
        per_page = pagination["per_page"]
        
        # Validate genre format if provided
        if genre:
            self.validation_service.validate_genre_format(genre)
        
        # Get stories from repository
        return self.repository.list(page=page, per_page=per_page, genre=genre)
    
    def save_story(self, story: Dict[str, Any]) -> bool:
        """
        Save a story to the repository.
        
        Args:
            story: Story data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        return self.repository.save(story)
    
    def save_story_with_optional_update(
        self,
        story_id: str,
        body_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a story with optional body text update.
        
        Does NOT create new revisions - only updates the current story.
        Use revision service to create new revisions.
        
        Args:
            story_id: Story identifier
            body_text: Optional new body text to update before saving
            
        Returns:
            Updated story data dictionary
            
        Raises:
            NotFoundError: If story not found
            ValidationError: If body text is invalid or exceeds word limit
            ServiceUnavailableError: If save operation fails
        """
        # Load story
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        # Optionally update body if provided
        if body_text:
            # Validate and update body using existing method
            story = self.update_story_body(story_id, body_text)
        else:
            # Just save without updating body
            success = self.repository.save(story)
            if not success:
                from src.shortstory.utils.errors import ServiceUnavailableError
                raise ServiceUnavailableError(
                    "storage", "Failed to save story. Please try again."
                )
        
        return story