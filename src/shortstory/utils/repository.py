"""
Story repository abstraction layer.

Provides a unified interface for story storage, abstracting away the differences
between database storage and file-based storage. This allows the application to
switch storage backends without changing business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)


class StoryRepository(ABC):
    """
    Abstract interface for story storage operations.
    
    This interface defines the contract that all story storage implementations
    must follow, allowing the application to work with different storage backends
    (database, file system, cloud storage, etc.) without changing business logic.
    """
    
    @abstractmethod
    def save(self, story: Dict[str, Any]) -> bool:
        """
        Save a story to storage.
        
        Args:
            story: Story dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a story from storage.
        
        Args:
            story_id: Unique identifier for the story
            
        Returns:
            Story dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list(self, page: int = 1, per_page: int = 50, 
             genre: Optional[str] = None) -> Dict[str, Any]:
        """
        List stories with pagination.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            genre: Optional genre filter
            
        Returns:
            Dictionary with 'stories' list and 'pagination' metadata
        """
        pass
    
    @abstractmethod
    def update(self, story_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a story in storage.
        
        Args:
            story_id: ID of the story to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, story_id: str) -> bool:
        """
        Delete a story from storage.
        
        Args:
            story_id: ID of the story to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def count(self, genre: Optional[str] = None) -> int:
        """
        Count total number of stories.
        
        Args:
            genre: Optional genre filter
            
        Returns:
            Total count of stories
        """
        # Default implementation using list()
        result = self.list(page=1, per_page=1, genre=genre)
        return result.get("pagination", {}).get("total", 0)


class DatabaseStoryRepository(StoryRepository):
    """
    Database-backed story repository.
    
    Wraps the existing StoryStorage class to provide the repository interface.
    Uses SQLite for persistence with optional Redis caching.
    """
    
    def __init__(self, use_cache: bool = False, cache_ttl: int = 3600):
        """
        Initialize database repository.
        
        Args:
            use_cache: Whether to use Redis caching (default: False)
            cache_ttl: Cache time-to-live in seconds (default: 3600)
        """
        from .db_storage import StoryStorage, init_database
        
        # Initialize database
        init_database()
        
        # Create storage instance
        self._storage = StoryStorage(use_cache=use_cache, cache_ttl=cache_ttl)
    
    def save(self, story: Dict[str, Any]) -> bool:
        """Save a story to the database."""
        return self._storage.save_story(story)
    
    def load(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Load a story from the database."""
        return self._storage.load_story(story_id)
    
    def list(self, page: int = 1, per_page: int = 50, 
             genre: Optional[str] = None) -> Dict[str, Any]:
        """List stories with pagination."""
        return self._storage.list_stories(page=page, per_page=per_page, genre=genre)
    
    def update(self, story_id: str, updates: Dict[str, Any]) -> bool:
        """Update a story in the database."""
        return self._storage.update_story(story_id, updates)
    
    def delete(self, story_id: str) -> bool:
        """Delete a story from the database."""
        return self._storage.delete_story(story_id)
    
    def count(self, genre: Optional[str] = None) -> int:
        """Count total number of stories."""
        return self._storage.count_stories(genre=genre)


class FileStoryRepository(StoryRepository):
    """
    File-based story repository.
    
    Wraps the existing file storage functions to provide the repository interface.
    Stores stories as JSON files in the stories/ directory.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize file repository.
        
        Args:
            storage_path: Path to stories directory (default: "stories/")
        """
        from .storage import (
            save_story as _save_story,
            load_story as _load_story,
            load_all_stories as _load_all_stories,
            update_story as _update_story,
            delete_story as _delete_story,
            list_stories as _list_stories,
        )
        
        # Store function references
        self._save_story = _save_story
        self._load_story = _load_story
        self._load_all_stories = _load_all_stories
        self._update_story = _update_story
        self._delete_story = _delete_story
        self._list_stories = _list_stories
        
        # In-memory cache for loaded stories
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False
    
    def _ensure_cache_loaded(self):
        """Ensure the in-memory cache is loaded."""
        if not self._cache_loaded:
            self._cache = self._load_all_stories()
            self._cache_loaded = True
    
    def save(self, story: Dict[str, Any]) -> bool:
        """Save a story to disk."""
        result = self._save_story(story)
        if result:
            # Update cache
            story_id = story.get("id")
            if story_id:
                self._cache[story_id] = story
        return result
    
    def load(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Load a story from disk (with in-memory cache)."""
        # Check cache first
        self._ensure_cache_loaded()
        if story_id in self._cache:
            return self._cache[story_id]
        
        # Load from disk
        story = self._load_story(story_id)
        if story:
            self._cache[story_id] = story
        return story
    
    def list(self, page: int = 1, per_page: int = 50, 
             genre: Optional[str] = None) -> Dict[str, Any]:
        """List stories with pagination."""
        # Load all stories
        self._ensure_cache_loaded()
        all_stories = self._list_stories()
        
        # Filter by genre if specified
        if genre:
            all_stories = [s for s in all_stories if s.get("genre") == genre]
        
        # Sort by updated_at (most recent first)
        all_stories.sort(
            key=lambda x: x.get("updated_at", ""), 
            reverse=True
        )
        
        # Calculate pagination
        total_count = len(all_stories)
        per_page = min(max(1, per_page), 100)  # Between 1 and 100
        page = max(1, page)
        total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get paginated slice
        paginated_stories = all_stories[start_idx:end_idx]
        
        return {
            "stories": paginated_stories,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def update(self, story_id: str, updates: Dict[str, Any]) -> bool:
        """Update a story on disk."""
        result = self._update_story(story_id, updates)
        if result:
            # Update cache
            story = self.load(story_id)
            if story:
                self._cache[story_id] = story
        return result
    
    def delete(self, story_id: str) -> bool:
        """Delete a story from disk."""
        result = self._delete_story(story_id)
        if result:
            # Remove from cache
            self._cache.pop(story_id, None)
        return result
    
    def count(self, genre: Optional[str] = None) -> int:
        """Count total number of stories."""
        self._ensure_cache_loaded()
        if genre:
            return sum(1 for s in self._cache.values() if s.get("genre") == genre)
        return len(self._cache)


def create_story_repository() -> StoryRepository:
    """
    Factory function to create the appropriate story repository.
    
    Determines which storage backend to use based on environment variables:
    - USE_DB_STORAGE=true: Use DatabaseStoryRepository
    - USE_DB_STORAGE=false: Use FileStoryRepository
    
    Returns:
        StoryRepository instance configured based on environment
    """
    use_db_storage = os.getenv('USE_DB_STORAGE', 'true').lower() == 'true'
    use_redis_cache = os.getenv('USE_REDIS_CACHE', 'false').lower() == 'true'
    
    if use_db_storage:
        logger.info("Creating database story repository" + 
                   (" with Redis cache" if use_redis_cache else ""))
        return DatabaseStoryRepository(use_cache=use_redis_cache)
    else:
        logger.info("Creating file-based story repository (legacy mode)")
        return FileStoryRepository()

