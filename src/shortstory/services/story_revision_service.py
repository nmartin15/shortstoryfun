"""
Story revision service.

Handles story revision operations including:
- Running revision passes on stories
- Managing revision history
- Comparing story versions
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.shortstory.utils.repository import StoryRepository
    from src.shortstory.pipeline import ShortStoryPipeline

from src.shortstory.utils.errors import ValidationError, NotFoundError, ServiceUnavailableError
from src.shortstory.utils import MAX_WORD_COUNT
from src.shortstory.genres import get_genre_config
from src.shortstory.api.helpers import get_story_body, get_story_repository, get_pipeline

logger = logging.getLogger(__name__)


class StoryRevisionService:
    """Service for story revision operations."""
    
    def __init__(
        self,
        repository: Optional['StoryRepository'] = None,
        pipeline_factory: Optional[Callable[..., 'ShortStoryPipeline']] = None
    ):
        """
        Initialize story revision service.
        
        Args:
            repository: Story repository instance (uses get_story_repository() if None)
            pipeline_factory: Factory function to create pipeline instances
        """
        self._repository = repository
        self._pipeline_factory = pipeline_factory
    
    @property
    def repository(self) -> 'StoryRepository':
        """Get story repository instance."""
        if self._repository is None:
            return get_story_repository()
        return self._repository
    
    def revise_story(
        self,
        story_id: str,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Run a revision pass on a story and create a new revision entry.
        
        Args:
            story_id: Unique identifier for the story
            use_llm: Whether to use LLM for revision (default: True)
            
        Returns:
            Updated story data dictionary with new revision
            
        Raises:
            NotFoundError: If story not found
            ValidationError: If story has no content to revise
            ServiceUnavailableError: If revision fails
        """
        # Load story
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        # Get current story body
        current_body = get_story_body(story)
        if not current_body:
            raise ValidationError(
                "Story has no content to revise.",
                details={"story_id": story_id}
            )
        
        # Get genre and genre_config from story
        story_genre = story.get("genre", "General Fiction")
        story_genre_config = story.get("genre_config")
        
        # Fetch genre_config if missing or incomplete
        if story_genre_config is None or not isinstance(story_genre_config, dict):
            logger.warning(
                f"Story {story_id} missing genre_config, fetching fresh config for genre {story_genre}")
            story_genre_config = get_genre_config(story_genre)
            if story_genre_config is None:
                raise ServiceUnavailableError(
                    "genre_config",
                    f"Genre configuration unavailable for genre: {story_genre}"
                )
        
        # Get pipeline instance
        if self._pipeline_factory:
            pipeline = self._pipeline_factory(
                genre=story_genre,
                genre_config=story_genre_config
            )
        else:
            pipeline = get_pipeline(
                genre=story_genre,
                genre_config=story_genre_config
            )
        
        # Create temporary draft object for revision
        temp_draft = {
            "text": current_body,
            "word_count": story.get("word_count", 0)
        }
        
        # Run revision
        revised_draft = pipeline.revise(draft=temp_draft, use_llm=use_llm)
        revised_body = revised_draft.get('text', '')
        revised_word_count = revised_draft.get('word_count', 0)
        
        # Update story with revised body
        story["body"] = revised_body
        story["word_count"] = revised_word_count
        story["max_words"] = story.get("max_words", MAX_WORD_COUNT)
        
        # Add to revision history
        self._add_revision_to_history(
            story=story,
            revised_body=revised_body,
            revised_word_count=revised_word_count,
            revised_draft=revised_draft
        )
        
        # Save to repository
        self.repository.save(story)
        
        logger.info(
            f"Story {story_id} revised to version {story.get('current_revision', 0)}")
        return story
    
    def _add_revision_to_history(
        self,
        story: Dict[str, Any],
        revised_body: str,
        revised_word_count: int,
        revised_draft: Dict[str, Any]
    ) -> None:
        """
        Add a new revision to story's revision history.
        
        Args:
            story: Story data dictionary (modified in place)
            revised_body: Revised story body text
            revised_word_count: Word count of revised body
            revised_draft: Full revised draft data
        """
        # Initialize revision history if needed
        if "revision_history" not in story:
            story["revision_history"] = []
        if "current_revision" not in story:
            story["current_revision"] = 0
        
        # Create new revision entry
        new_version = story["current_revision"] + 1
        story["revision_history"].append({
            "version": new_version,
            "body": revised_body,  # Store body, not composite
            "word_count": revised_word_count,
            "type": "revised",
            "timestamp": datetime.now().isoformat()
        })
        
        # Update current revision
        story["current_revision"] = new_version
        story["revised_draft"] = revised_draft
    
    def get_revision_history(self, story_id: str) -> Dict[str, Any]:
        """
        Get revision history for a story.
        
        Args:
            story_id: Unique identifier for the story
            
        Returns:
            Dict with revision history data:
            {
                "success": bool,
                "story_id": str,
                "revision_history": [...],
                "current_revision": int,
                "total_revisions": int
            }
            
        Raises:
            NotFoundError: If story not found
        """
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        revision_history = story.get("revision_history", [])
        current_revision = story.get("current_revision", len(revision_history))
        
        return {
            "success": True,
            "story_id": story_id,
            "revision_history": revision_history,
            "current_revision": current_revision,
            "total_revisions": len(revision_history)
        }
    
    def compare_versions(
        self,
        story_id: str,
        version1: Optional[int] = None,
        version2: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare two versions of a story.
        
        Args:
            story_id: Unique identifier for the story
            version1: First version to compare (default: 1)
            version2: Second version to compare (default: latest)
            
        Returns:
            Dict with comparison data:
            {
                "success": bool,
                "story_id": str,
                "version1": {...},
                "version2": {...},
                "comparison": {...}
            }
            
        Raises:
            NotFoundError: If story not found
            ValidationError: If not enough revisions exist or versions not found
        """
        # Load story
        story = self.repository.load(story_id)
        if not story:
            raise NotFoundError("Story", story_id)
        
        revision_history = story.get("revision_history", [])
        if len(revision_history) < 2:
            raise ValidationError(
                "Not enough revisions to compare. Need at least 2 versions.",
                details={
                    "story_id": story_id,
                    "revision_count": len(revision_history)
                }
            )
        
        # Default to first and last if not specified
        if version1 is None or version2 is None:
            version1 = 1
            version2 = len(revision_history)
        
        # Find versions
        v1_data = next(
            (r for r in revision_history if r.get("version") == version1),
            None
        )
        v2_data = next(
            (r for r in revision_history if r.get("version") == version2),
            None
        )
        
        if not v1_data or not v2_data:
            available_versions = [r.get('version') for r in revision_history]
            raise ValidationError(
                f"Version(s) not found. Available versions: {available_versions}",
                details={
                    "story_id": story_id,
                    "requested_versions": {
                        "version1": version1,
                        "version2": version2
                    },
                    "available_versions": available_versions
                }
            )
        
        # Get body text from revision history (support both 'body' and 'text')
        text1 = v1_data.get("body") or v1_data.get("text", "")
        text2 = v2_data.get("body") or v2_data.get("text", "")
        
        words1 = text1.split()
        words2 = text2.split()
        
        # Calculate basic statistics
        word_count_diff = v2_data.get("word_count", 0) - v1_data.get("word_count", 0)
        
        return {
            "success": True,
            "story_id": story_id,
            "version1": {
                "version": version1,
                "body": text1,
                "word_count": v1_data.get("word_count", 0),
                "timestamp": v1_data.get("timestamp"),
                "type": v1_data.get("type", "unknown")
            },
            "version2": {
                "version": version2,
                "body": text2,
                "word_count": v2_data.get("word_count", 0),
                "timestamp": v2_data.get("timestamp"),
                "type": v2_data.get("type", "unknown")
            },
            "comparison": {
                "word_count_diff": word_count_diff,
                "text_length_diff": len(text2) - len(text1),
                "words_added": max(0, len(words2) - len(words1)),
                "words_removed": max(0, len(words1) - len(words2))
            }
        }
