"""
Story validation service.

Handles all input validation for story operations, including:
- Story generation input validation
- Story body text validation
- Genre format validation
- Pagination parameter validation
"""

import re
import logging
from typing import Dict, Any, Optional

from src.shortstory.utils.errors import ValidationError
from src.shortstory.utils import MAX_WORD_COUNT

logger = logging.getLogger(__name__)


class StoryValidationService:
    """Service for validating story input parameters."""
    
    MAX_IDEA_LENGTH = 2000
    MAX_CHARACTER_DESC_LENGTH = 2000
    MAX_THEME_LENGTH = 1000
    
    def validate_generation_input(
        self,
        idea: Optional[str],
        character: Optional[Dict[str, Any]],
        theme: Optional[str],
        genre: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate story generation input parameters.
        
        Args:
            idea: Story idea/premise
            character: Character description (dict or None)
            theme: Story theme (optional)
            genre: Story genre (optional)
            
        Returns:
            Dict with validated and normalized input:
            {
                "idea": str,
                "character": Optional[Dict],
                "theme": Optional[str],
                "genre": str
            }
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate idea
        if not idea or not isinstance(idea, str):
            raise ValidationError(
                "Story idea is required. Please provide a creative premise for your story.",
                details={"field": "idea"}
            )
        
        idea = idea.strip()
        if not idea:
            raise ValidationError(
                "Story idea cannot be empty.",
                details={"field": "idea"}
            )
        
        if len(idea) > self.MAX_IDEA_LENGTH:
            raise ValidationError(
                f"Story idea is too long (maximum {self.MAX_IDEA_LENGTH} characters). "
                "Please provide a more concise premise.",
                details={
                    "field": "idea",
                    "length": len(idea),
                    "max_length": self.MAX_IDEA_LENGTH
                }
            )
        
        # Normalize and validate character
        normalized_character = None
        if character:
            if isinstance(character, str):
                normalized_character = {"description": character}
            elif isinstance(character, dict):
                normalized_character = character
            else:
                raise ValidationError(
                    "Character must be a dictionary or string if provided.",
                    details={"field": "character", "type": type(character).__name__}
                )
            
            # If character is empty dict, treat as None (optional field)
            if normalized_character == {}:
                normalized_character = None
            else:
                # Validate character description length
                char_desc = normalized_character.get("description", "")
                if char_desc and len(char_desc) > self.MAX_CHARACTER_DESC_LENGTH:
                    raise ValidationError(
                        f"Character description is too long (maximum {self.MAX_CHARACTER_DESC_LENGTH} characters).",
                        details={
                            "field": "character.description",
                            "length": len(char_desc),
                            "max_length": self.MAX_CHARACTER_DESC_LENGTH
                        }
                    )
        
        # Validate theme
        normalized_theme = None
        if theme:
            if not isinstance(theme, str):
                raise ValidationError(
                    "Theme must be a string if provided.",
                    details={"field": "theme", "type": type(theme).__name__}
                )
            normalized_theme = theme.strip()
            if normalized_theme and len(normalized_theme) > self.MAX_THEME_LENGTH:
                raise ValidationError(
                    f"Theme is too long (maximum {self.MAX_THEME_LENGTH} characters).",
                    details={
                        "field": "theme",
                        "length": len(normalized_theme),
                        "max_length": self.MAX_THEME_LENGTH
                    }
                )
        
        # Validate genre
        normalized_genre = genre or "General Fiction"
        if normalized_genre and not isinstance(normalized_genre, str):
            raise ValidationError(
                "Genre must be a string if provided.",
                details={"field": "genre", "type": type(normalized_genre).__name__}
            )
        
        return {
            "idea": idea,
            "character": normalized_character,
            "theme": normalized_theme,
            "genre": normalized_genre
        }
    
    def validate_story_body(
        self,
        body_text: str,
        max_words: int = MAX_WORD_COUNT
    ) -> Dict[str, Any]:
        """
        Validate story body text structure.
        
        Note: Word count validation should be done separately using pipeline.
        This method only validates structure and basic constraints.
        
        Args:
            body_text: Story body text to validate
            max_words: Maximum allowed word count (for character limit estimation)
            
        Returns:
            Dict with validation results:
                - body_text: str (validated text)
                - max_words: int
                
        Raises:
            ValidationError: If validation fails
        """
        if not body_text:
            raise ValidationError(
                "Story body/text is required.",
                details={"field": "body"}
            )
        
        if not isinstance(body_text, str):
            raise ValidationError(
                "Story body/text must be a string.",
                details={"field": "body", "type": type(body_text).__name__}
            )
        
        # Rough character limit check (10 chars per word max)
        max_chars = max_words * 10
        if len(body_text) > max_chars:
            raise ValidationError(
                f"Story body is too long (maximum {max_chars:,} characters).",
                details={
                    "field": "body",
                    "length": len(body_text),
                    "max_length": max_chars
                }
            )
        
        return {
            "body_text": body_text,
            "max_words": max_words
        }
    
    def validate_export_format(self, format_type: str) -> str:
        """
        Validate export format type.
        
        Args:
            format_type: Export format to validate
            
        Returns:
            Validated format type string
            
        Raises:
            ValidationError: If format is invalid
        """
        valid_formats = ['pdf', 'markdown', 'txt', 'docx', 'epub']
        if format_type not in valid_formats:
            raise ValidationError(
                f"Invalid format '{format_type}'. Supported formats: {', '.join(valid_formats)}",
                details={"format_type": format_type, "valid_formats": valid_formats}
            )
        return format_type
    
    def validate_genre_format(self, genre: str) -> str:
        """
        Validate genre format to prevent injection attacks.
        
        Args:
            genre: Genre string to validate
            
        Returns:
            Validated genre string
            
        Raises:
            ValidationError: If genre format is invalid
        """
        # Only allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', genre):
            raise ValidationError(
                f"Invalid genre format: '{genre}'. "
                "Genre must contain only alphanumeric characters, spaces, hyphens, and underscores.",
                details={"genre": genre}
            )
        return genre
    
    def validate_template_genre_format(self, genre: str) -> str:
        """
        Validate genre format for template queries (allows more characters).
        
        Args:
            genre: Genre string to validate
            
        Returns:
            Validated genre string
            
        Raises:
            ValidationError: If genre format is invalid
        """
        # Allow alphanumeric, spaces, hyphens, underscores, forward slashes, and ampersands
        if not re.match(r'^[a-zA-Z0-9\s_\-/&]+$', genre):
            raise ValidationError(
                f"Invalid genre format: '{genre}'. "
                "Genre must contain only alphanumeric characters, spaces, hyphens, underscores, "
                "forward slashes, and ampersands.",
                details={"genre": genre}
            )
        return genre
    
    def validate_pagination_params(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Validate and normalize pagination parameters.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dict with validated pagination:
                - page: int (validated, >= 1)
                - per_page: int (validated, 1-100)
        """
        # Normalize page
        if page is None or page < 1:
            page = 1
        
        # Normalize per_page (between 1 and 100 to prevent DoS)
        if per_page is None or per_page < 1:
            per_page = 50
        elif per_page > 100:
            per_page = 100
        
        return {
            "page": page,
            "per_page": per_page
        }
    
    def validate_version_number(self, version: int, field_name: str = "version") -> int:
        """
        Validate version number (must be positive integer).
        
        Args:
            version: Version number to validate
            field_name: Field name for error messages
            
        Returns:
            Validated version number
            
        Raises:
            ValidationError: If version is invalid
        """
        if version < 1:
            raise ValidationError(
                f"Invalid {field_name}: {version}. Version must be a positive integer.",
                details={field_name: version}
            )
        return version
