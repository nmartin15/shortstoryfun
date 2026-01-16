"""
Story generation service.

Handles story generation orchestration through the full pipeline.
"""

import uuid
import logging
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.shortstory.utils.repository import StoryRepository
    from src.shortstory.pipeline import ShortStoryPipeline

from src.shortstory.utils.errors import ServiceUnavailableError
from src.shortstory.utils import MAX_WORD_COUNT, check_distinctiveness
from src.shortstory.utils.story_builder import build_story_data
from src.shortstory.genres import get_genre_config
from src.shortstory.api.helpers import get_pipeline

logger = logging.getLogger(__name__)


class StoryGenerationService:
    """Service for orchestrating story generation through the pipeline."""
    
    def __init__(
        self,
        repository: Optional['StoryRepository'] = None,
        pipeline_factory: Optional[Callable[..., 'ShortStoryPipeline']] = None
    ):
        """
        Initialize story generation service.
        
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
            from src.shortstory.api.helpers import get_story_repository
            return get_story_repository()
        return self._repository
    
    def generate_story(
        self,
        idea: str,
        character: Optional[Dict[str, Any]],
        theme: Optional[str],
        genre: str = "General Fiction",
        max_word_count: int = MAX_WORD_COUNT
    ) -> Dict[str, Any]:
        """
        Generate a complete story through the full pipeline.
        
        Args:
            idea: Story premise/idea
            character: Character description (optional)
            theme: Story theme (optional)
            genre: Story genre (default: "General Fiction")
            max_word_count: Maximum word count (default: MAX_WORD_COUNT)
            
        Returns:
            Complete story data dictionary ready for storage
            
        Raises:
            ServiceUnavailableError: If genre config or pipeline is unavailable
            ValueError: If pipeline execution fails
        """
        # Get pipeline instance
        if self._pipeline_factory:
            pipeline = self._pipeline_factory(genre=genre)
        else:
            pipeline = get_pipeline(genre=genre)
        
        # Ensure genre_config is available
        genre_config = pipeline.genre_config
        if genre_config is None:
            genre_config = get_genre_config(genre)
            if genre_config is None:
                raise ServiceUnavailableError(
                    "genre_config",
                    f"Genre configuration service unavailable for genre: {genre}"
                )
            pipeline.genre_config = genre_config
        
        # Run pipeline stages
        premise = pipeline.capture_premise(idea, character, theme, validate=True)
        outline = pipeline.generate_outline(genre=genre)
        scaffold = pipeline.scaffold(genre=genre)
        draft = pipeline.draft()
        revised_draft = pipeline.revise()
        
        # Extract metadata from scaffold and genre config
        story_metadata = self._extract_story_metadata(
            scaffold=scaffold,
            genre_config=genre_config,
            idea=idea,
            character=character
        )
        
        # Get revised story text and calculate word count
        revised_story_text = revised_draft.get('text', '')
        story_word_count = pipeline.word_validator.count_words(revised_story_text)
        
        # Log word count discrepancy if significant
        draft_word_count = revised_draft.get('word_count', 0)
        if abs(story_word_count - draft_word_count) > 50:
            logger.warning(
                f"Word count discrepancy: draft reported {draft_word_count}, "
                f"actual story text is {story_word_count} words"
            )
        
        # Generate story ID
        story_id = f"story_{uuid.uuid4().hex[:8]}"
        
        # Convert Pydantic models to dicts for storage
        premise_dict = self._model_to_dict(premise)
        outline_dict = self._model_to_dict(outline)
        
        # Build standardized story data
        story_data = build_story_data(
            story_id=story_id,
            premise=premise_dict,
            outline=outline_dict,
            genre=genre,
            genre_config=genre_config,
            body=revised_story_text,
            word_count=story_word_count,
            scaffold=scaffold,
            metadata=story_metadata,
            draft=draft,
            revised_draft=revised_draft,
            max_words=max_word_count
        )
        
        # Save to repository
        self.repository.save(story_data)
        
        logger.info(f"Successfully generated story {story_id}")
        return story_data
    
    def _extract_story_metadata(
        self,
        scaffold: Dict[str, Any],
        genre_config: Dict[str, Any],
        idea: str,
        character: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract and build story metadata from pipeline outputs.
        
        Args:
            scaffold: Scaffold data from pipeline
            genre_config: Genre configuration
            idea: Story idea
            character: Character description
            
        Returns:
            Metadata dictionary with tone, pace, pov, and distinctiveness scores
        """
        constraints = genre_config.get('constraints', {})
        
        # Extract tone, pace, pov from scaffold with fallbacks
        if isinstance(scaffold, dict):
            tone = scaffold.get('tone', constraints.get('tone', 'balanced'))
            pace = scaffold.get('pace', constraints.get('pace', 'moderate'))
            pov = scaffold.get('pov', constraints.get('pov_preference', 'flexible'))
        else:
            tone = constraints.get('tone', 'balanced')
            pace = constraints.get('pace', 'moderate')
            pov = constraints.get('pov_preference', 'flexible')
        
        # Calculate distinctiveness scores
        idea_dist = check_distinctiveness(idea)
        char_dist = check_distinctiveness(None, character=character)
        
        return {
            "tone": tone,
            "pace": pace,
            "pov": pov,
            "idea_distinctiveness": idea_dist,
            "character_distinctiveness": char_dist
        }
    
    def _model_to_dict(self, model: Any) -> Dict[str, Any]:
        """
        Convert Pydantic model to dictionary, handling both v1 and v2 APIs.
        
        Args:
            model: Pydantic model instance or dict
            
        Returns:
            Dictionary representation of the model
        """
        if model is None:
            return {}
        
        if isinstance(model, dict):
            return model
        
        # Try v2 API first (model_dump)
        if hasattr(model, 'model_dump'):
            return model.model_dump(exclude_none=True)
        
        # Fall back to v1 API (dict)
        if hasattr(model, 'dict'):
            return model.dict(exclude_none=True)
        
        # If it's not a model or dict, return empty dict
        logger.warning(f"Unexpected model type: {type(model).__name__}")
        return {}
