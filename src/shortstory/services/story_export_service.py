"""
Story export service.

Handles story export operations in various formats.
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Response

from src.shortstory.utils.errors import ValidationError, NotFoundError
from src.shortstory.exports import export_story_from_dict
from src.shortstory.api.helpers import get_story_text, get_story_or_404
from .story_validation_service import StoryValidationService

logger = logging.getLogger(__name__)


class StoryExportService:
    """Service for exporting stories in various formats."""
    
    VALID_FORMATS = ['pdf', 'markdown', 'txt', 'docx', 'epub']
    
    def __init__(self):
        """Initialize export service."""
        self.validation_service = StoryValidationService()
    
    def export_story(
        self,
        story_id: str,
        format_type: str
    ) -> 'Response':
        """
        Export a story in the specified format.
        
        Args:
            story_id: Unique identifier for the story
            format_type: Export format (pdf, markdown, txt, docx, epub)
            
        Returns:
            Flask Response with exported file
            
        Raises:
            ValidationError: If format is invalid or story has no content
            NotFoundError: If story with given ID does not exist
            ServiceUnavailableError: If export fails
        """
        # Validate format
        format_type = self.validation_service.validate_export_format(format_type)
        
        # Load story
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)
        
        # Get composite text for export (includes metadata headers)
        story_text = get_story_text(story)
        
        # Use the centralized export function from exports.py
        return export_story_from_dict(story, story_id, format_type, story_text)
