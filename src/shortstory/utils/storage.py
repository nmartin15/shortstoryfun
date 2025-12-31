"""Storage utilities for persisting stories to disk."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


# Get the project root (assuming this file is in src/shortstory/utils/)
# Go up 3 levels: utils -> shortstory -> src -> project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STORAGE_DIR = _PROJECT_ROOT / "stories"


def ensure_storage_dir() -> Path:
    """Ensure the stories directory exists."""
    STORAGE_DIR.mkdir(exist_ok=True)
    return STORAGE_DIR


def get_story_path(story_id: str) -> Path:
    """Get the file path for a story."""
    ensure_storage_dir()
    return STORAGE_DIR / f"{story_id}.json"


def save_story(story: Dict[str, Any]) -> bool:
    """
    Save a story to disk.
    
    Args:
        story: Story dictionary to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        story_id = story.get("id")
        if not story_id:
            return False
        
        # Add metadata
        story_with_meta = story.copy()
        story_with_meta["saved_at"] = datetime.now().isoformat()
        story_with_meta["updated_at"] = datetime.now().isoformat()
        
        file_path = get_story_path(story_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(story_with_meta, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving story {story_id}: {e}")
        return False


def load_story(story_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a story from disk.
    
    Args:
        story_id: ID of the story to load
        
    Returns:
        Story dictionary or None if not found
    """
    try:
        file_path = get_story_path(story_id)
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            story = json.load(f)
        
        return story
    except Exception as e:
        print(f"Error loading story {story_id}: {e}")
        return None


def load_all_stories() -> Dict[str, Dict[str, Any]]:
    """
    Load all stories from disk.
    
    Returns:
        Dictionary mapping story_id to story data
    """
    stories = {}
    try:
        ensure_storage_dir()
        for file_path in STORAGE_DIR.glob("*.json"):
            story_id = file_path.stem
            story = load_story(story_id)
            if story:
                stories[story_id] = story
    except Exception as e:
        print(f"Error loading stories: {e}")
    
    return stories


def update_story(story_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a story on disk.
    
    Args:
        story_id: ID of the story to update
        updates: Dictionary of fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        story = load_story(story_id)
        if not story:
            return False
        
        # Update fields
        story.update(updates)
        story["updated_at"] = datetime.now().isoformat()
        
        return save_story(story)
    except Exception as e:
        print(f"Error updating story {story_id}: {e}")
        return False


def delete_story(story_id: str) -> bool:
    """
    Delete a story from disk.
    
    Args:
        story_id: ID of the story to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = get_story_path(story_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting story {story_id}: {e}")
        return False


def list_stories() -> list[Dict[str, Any]]:
    """
    List all stories with metadata.
    
    Returns:
        List of story metadata dictionaries
    """
    stories = []
    try:
        ensure_storage_dir()
        for file_path in STORAGE_DIR.glob("*.json"):
            story_id = file_path.stem
            story = load_story(story_id)
            if story:
                stories.append({
                    "id": story_id,
                    "genre": story.get("genre", "Unknown"),
                    "saved_at": story.get("saved_at"),
                    "updated_at": story.get("updated_at"),
                    "word_count": story.get("word_count", 0),
                    "premise": story.get("premise", {}).get("idea", "") if isinstance(story.get("premise"), dict) else ""
                })
    except Exception as e:
        print(f"Error listing stories: {e}")
    
    return stories

