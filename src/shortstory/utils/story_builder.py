"""
Standardized story data builder.

This module provides a single source of truth for creating story data structures.
All story creation should use build_story_data() to ensure consistency.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def build_story_data(
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
) -> Dict[str, Any]:
    """
    Build standardized story data structure.
    
    This is the canonical way to create story dictionaries. All story creation
    should go through this function to ensure consistency.
    
    Args:
        story_id: Unique story identifier (format: story_XXXXXXXX)
        premise: Premise dictionary with idea, character, theme, validation
        outline: Outline dictionary with genre, framework, structure, acts
        genre: Genre name string
        genre_config: Genre configuration dictionary
        body: Pure narrative text (without metadata headers)
        word_count: Word count of the body text
        scaffold: Optional scaffold data dictionary
        metadata: Optional metadata dictionary (tone, pace, pov, distinctiveness)
        draft: Optional draft dictionary
        revised_draft: Optional revised draft dictionary
        max_words: Maximum allowed word count (default: 7500)
        
    Returns:
        Dictionary with standardized story structure
        
    Example:
        >>> story = build_story_data(
        ...     story_id="story_abc123",
        ...     premise={"idea": "...", "character": {...}},
        ...     outline={"genre": "...", "framework": "..."},
        ...     genre="General Fiction",
        ...     genre_config={...},
        ...     body="The story text...",
        ...     word_count=1500,
        ...     metadata={"tone": "balanced", "pace": "moderate"}
        ... )
    """
    # Ensure metadata is a dict
    if metadata is None:
        metadata = {}
    
    # Ensure scaffold is a dict
    if scaffold is None:
        scaffold = {}
    
    # Build revision history from drafts
    revision_history = []
    if draft:
        revision_history.append({
            "version": 1,
            "body": draft.get('text', body),
            "word_count": draft.get('word_count', word_count),
            "type": "draft",
            "timestamp": datetime.now().isoformat()
        })
    
    if revised_draft:
        revision_history.append({
            "version": 2,
            "body": revised_draft.get('text', body),
            "word_count": revised_draft.get('word_count', word_count),
            "type": "revised",
            "timestamp": datetime.now().isoformat()
        })
    
    # Determine current revision number
    current_revision = len(revision_history) if revision_history else 1
    
    # Build standardized story structure
    story_data = {
        "id": story_id,
        "premise": premise,
        "outline": outline,
        "genre": genre,
        "genre_config": genre_config,
        "scaffold": scaffold,
        "body": body,  # Pure narrative text (new format)
        "metadata": metadata,  # Separated metadata (new format)
        "word_count": word_count,
        "max_words": max_words,
        "draft": draft,
        "revised_draft": revised_draft,
        "revision_history": revision_history,
        "current_revision": current_revision,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Validate word count
    if word_count > max_words:
        logger.warning(
            f"Story {story_id} has word_count ({word_count}) exceeding "
            f"max_words ({max_words})"
        )
    
    # Validate revision history consistency
    if revision_history:
        max_version = max(rev.get("version", 0) for rev in revision_history)
        if current_revision > max_version:
            logger.warning(
                f"Story {story_id} has current_revision ({current_revision}) "
                f"exceeding max version in history ({max_version})"
            )
    
    return story_data


def normalize_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a story dictionary to standard format.
    
    Handles legacy formats and ensures all required fields are present.
    This is useful for migrating existing stories or normalizing data
    from different sources.
    
    Args:
        story: Story dictionary (may be in legacy format)
        
    Returns:
        Normalized story dictionary
    """
    # Ensure required fields exist
    if "id" not in story:
        logger.warning("Story missing 'id' field")
        story["id"] = f"story_unknown_{datetime.now().isoformat()}"
    
    # Handle legacy 'text' field - extract 'body' if needed
    if "body" not in story and "text" in story:
        # Try to extract body from composite text
        text = story["text"]
        import re
        story_match = re.search(r'## Story\s*\n\s*\n(.+)$', text, re.DOTALL)
        if story_match:
            story["body"] = story_match.group(1).strip()
        else:
            # If no "## Story" marker, assume whole text is body
            story["body"] = text
    
    # Ensure metadata exists
    if "metadata" not in story:
        story["metadata"] = {}
        # Try to extract metadata from scaffold
        scaffold = story.get("scaffold", {})
        if isinstance(scaffold, dict):
            if "tone" in scaffold and "tone" not in story["metadata"]:
                story["metadata"]["tone"] = scaffold.get("tone")
            if "pace" in scaffold and "pace" not in story["metadata"]:
                story["metadata"]["pace"] = scaffold.get("pace")
            if "pov" in scaffold and "pov" not in story["metadata"]:
                story["metadata"]["pov"] = scaffold.get("pov")
    
    # Ensure revision_history is properly formatted
    if "revision_history" in story and story["revision_history"]:
        for rev in story["revision_history"]:
            if not isinstance(rev, dict):
                continue
            # Ensure required fields
            if "version" not in rev:
                rev["version"] = 1
            if "type" not in rev:
                rev["type"] = "draft"
            if "timestamp" not in rev:
                rev["timestamp"] = datetime.now().isoformat()
            # Handle legacy 'text' field in revisions
            if "body" not in rev and "text" in rev:
                rev["body"] = rev["text"]
    
    # Ensure timestamps
    if "created_at" not in story:
        story["created_at"] = datetime.now().isoformat()
    if "updated_at" not in story:
        story["updated_at"] = datetime.now().isoformat()
    
    # Ensure max_words
    if "max_words" not in story:
        story["max_words"] = 7500
    
    return story

