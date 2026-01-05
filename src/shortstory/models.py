"""
Standardized story data model.

This module defines the canonical structure for story objects using Pydantic
for validation and type safety. All story creation and manipulation should
use these models to ensure consistency.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json


class CharacterModel(BaseModel):
    """Character description model."""
    description: str
    name: Optional[str] = None
    quirks: Optional[List[str]] = None
    contradictions: Optional[str] = None


class PremiseModel(BaseModel):
    """Story premise model."""
    idea: str = Field(..., min_length=1, description="The core story concept")
    character: Optional[CharacterModel] = None
    theme: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class OutlineModel(BaseModel):
    """Story outline model."""
    genre: str
    framework: str
    structure: List[str]
    acts: Optional[Dict[str, str]] = None
    premise_id: Optional[str] = None  # Reference to premise instead of duplication


class RevisionEntry(BaseModel):
    """Single revision entry in revision history."""
    version: int
    body: str
    word_count: int
    type: str = Field(..., regex="^(draft|revised)$")
    timestamp: str


class StoryMetadata(BaseModel):
    """Separated metadata for story."""
    tone: Optional[str] = None
    pace: Optional[str] = None
    pov: Optional[str] = None
    idea_distinctiveness: Optional[Dict[str, Any]] = None
    character_distinctiveness: Optional[Dict[str, Any]] = None


class StoryModel(BaseModel):
    """
    Standardized story model.
    
    This is the canonical structure for all stories in the system.
    All story creation and storage should use this model.
    """
    id: str = Field(..., regex="^story_[a-f0-9]{8}$", description="Unique story identifier")
    premise: PremiseModel
    outline: OutlineModel
    genre: str
    genre_config: Dict[str, Any]
    scaffold: Optional[Dict[str, Any]] = None
    
    # Content fields
    body: str = Field(..., description="Pure narrative text without metadata")
    metadata: StoryMetadata = Field(default_factory=StoryMetadata)
    
    # Word count fields
    word_count: int = Field(..., ge=0, description="Current word count")
    max_words: int = Field(default=7500, ge=1, description="Maximum allowed word count")
    
    # Draft and revision fields
    draft: Optional[Dict[str, Any]] = None
    revised_draft: Optional[Dict[str, Any]] = None
    revision_history: List[RevisionEntry] = Field(default_factory=list)
    current_revision: int = Field(default=1, ge=1)
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    saved_at: Optional[str] = None
    
    # Legacy fields (for backward compatibility)
    text: Optional[str] = None  # Generated on demand from body + metadata
    
    @validator('word_count')
    def validate_word_count(cls, v, values):
        """Ensure word count doesn't exceed max_words."""
        max_words = values.get('max_words', 7500)
        if v > max_words:
            raise ValueError(f"Word count ({v}) exceeds maximum ({max_words})")
        return v
    
    @validator('revision_history')
    def validate_revision_history(cls, v, values):
        """Ensure current_revision matches highest version in history."""
        if v and values.get('current_revision'):
            max_version = max([rev.version for rev in v], default=0)
            if values['current_revision'] > max_version:
                raise ValueError(
                    f"current_revision ({values['current_revision']}) "
                    f"exceeds max version in history ({max_version})"
                )
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for storage."""
        return self.dict(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoryModel':
        """Create model from dictionary (with validation)."""
        # Handle legacy format: convert 'text' to 'body' if needed
        if 'body' not in data and 'text' in data:
            # Extract body from composite text
            text = data['text']
            # Try to extract body from markdown (look for "## Story" section)
            import re
            story_match = re.search(r'## Story\s*\n\s*\n(.+)$', text, re.DOTALL)
            if story_match:
                data['body'] = story_match.group(1).strip()
            else:
                data['body'] = text
        
        # Handle legacy metadata: extract from various places
        if 'metadata' not in data:
            metadata = StoryMetadata()
            # Extract from scaffold or other places
            scaffold = data.get('scaffold', {})
            if isinstance(scaffold, dict):
                metadata.tone = scaffold.get('tone')
                metadata.pace = scaffold.get('pace')
                metadata.pov = scaffold.get('pov')
            data['metadata'] = metadata.dict()
        
        # Ensure revision_history is list of RevisionEntry
        if 'revision_history' in data and data['revision_history']:
            if isinstance(data['revision_history'][0], dict):
                data['revision_history'] = [
                    RevisionEntry(**rev) for rev in data['revision_history']
                ]
        
        return cls(**data)
    
    def generate_text(self) -> str:
        """
        Generate composite markdown text from body and metadata.
        
        This is the legacy 'text' field, generated on demand.
        """
        from .templates import generate_story_text
        return generate_story_text(self.to_dict())


def validate_story(story: Dict[str, Any]) -> StoryModel:
    """
    Validate and normalize a story dictionary.
    
    Args:
        story: Story dictionary (may be in legacy format)
        
    Returns:
        Validated StoryModel instance
        
    Raises:
        ValidationError: If story structure is invalid
    """
    return StoryModel.from_dict(story)


def create_story(
    story_id: str,
    premise: Dict[str, Any],
    outline: Dict[str, Any],
    genre: str,
    genre_config: Dict[str, Any],
    body: str,
    word_count: int,
    scaffold: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    draft: Optional[Dict[str, Any]] = None,
    revised_draft: Optional[Dict[str, Any]] = None,
    max_words: int = 7500
) -> StoryModel:
    """
    Create a new validated story model.
    
    This is the canonical way to create stories in the system.
    All story creation should go through this function.
    
    Args:
        story_id: Unique story identifier
        premise: Premise dictionary
        outline: Outline dictionary
        genre: Genre name
        genre_config: Genre configuration
        body: Pure narrative text
        word_count: Word count of body
        scaffold: Optional scaffold data
        metadata: Optional metadata
        draft: Optional draft data
        revised_draft: Optional revised draft data
        max_words: Maximum word count (default: 7500)
        
    Returns:
        Validated StoryModel instance
    """
    from datetime import datetime
    
    # Build revision history
    revision_history = []
    if draft:
        revision_history.append(RevisionEntry(
            version=1,
            body=draft.get('text', body),
            word_count=draft.get('word_count', word_count),
            type='draft',
            timestamp=datetime.now().isoformat()
        ))
    if revised_draft:
        revision_history.append(RevisionEntry(
            version=2,
            body=revised_draft.get('text', body),
            word_count=revised_draft.get('word_count', word_count),
            type='revised',
            timestamp=datetime.now().isoformat()
        ))
    
    # Build story data
    story_data = {
        'id': story_id,
        'premise': premise,
        'outline': outline,
        'genre': genre,
        'genre_config': genre_config,
        'body': body,
        'word_count': word_count,
        'max_words': max_words,
        'scaffold': scaffold or {},
        'metadata': metadata or {},
        'draft': draft,
        'revised_draft': revised_draft,
        'revision_history': [rev.dict() for rev in revision_history],
        'current_revision': len(revision_history) if revision_history else 1,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return StoryModel.from_dict(story_data)

