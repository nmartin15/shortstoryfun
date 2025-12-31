"""
Database-backed storage for stories.

Provides a scalable storage solution using SQLite (with optional Redis caching)
to replace in-memory storage. Supports pagination and efficient querying.
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Get the project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_DIR = _PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "stories.db"


def ensure_db_dir() -> Path:
    """Ensure the database directory exists."""
    DB_DIR.mkdir(exist_ok=True)
    return DB_DIR


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection."""
    ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@contextmanager
def db_transaction():
    """Context manager for database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize the database schema."""
    with db_transaction() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                genre TEXT,
                premise TEXT,
                outline TEXT,
                scaffold TEXT,
                text TEXT,
                word_count INTEGER,
                max_words INTEGER DEFAULT 7500,
                draft TEXT,
                revised_draft TEXT,
                revision_history TEXT,
                current_revision INTEGER DEFAULT 1,
                genre_config TEXT,
                created_at TEXT,
                updated_at TEXT,
                saved_at TEXT
            )
        """)
        # Create index for faster queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_updated_at 
            ON stories(updated_at DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stories_genre 
            ON stories(genre)
        """)


class StoryStorage:
    """
    Database-backed story storage with optional Redis caching.
    
    Provides a scalable alternative to in-memory storage by using SQLite
    for persistence and optional Redis for caching frequently accessed stories.
    """
    
    def __init__(self, use_cache: bool = False, cache_ttl: int = 3600):
        """
        Initialize story storage.
        
        Args:
            use_cache: Whether to use Redis caching (default: False)
            cache_ttl: Cache time-to-live in seconds (default: 3600)
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self._cache = None
        
        if use_cache:
            try:
                import redis
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self._cache = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis cache enabled")
            except ImportError:
                logger.warning("Redis not available, caching disabled")
                self.use_cache = False
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, caching disabled")
                self.use_cache = False
        
        # Initialize database
        init_database()
    
    def _get_cache_key(self, story_id: str) -> str:
        """Get cache key for a story."""
        return f"story:{story_id}"
    
    def _serialize_story(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize story data for database storage."""
        serialized = story.copy()
        # Convert complex objects to JSON strings
        for key in ['premise', 'outline', 'scaffold', 'draft', 'revised_draft', 
                   'revision_history', 'genre_config']:
            if key in serialized and isinstance(serialized[key], (dict, list)):
                serialized[key] = json.dumps(serialized[key])
        return serialized
    
    def _deserialize_story(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Deserialize story data from database."""
        story = dict(row)
        # Convert JSON strings back to objects
        for key in ['premise', 'outline', 'scaffold', 'draft', 'revised_draft',
                   'revision_history', 'genre_config']:
            if story.get(key) and isinstance(story[key], str):
                try:
                    story[key] = json.loads(story[key])
                except (json.JSONDecodeError, TypeError):
                    pass  # Keep as string if not valid JSON
        return story
    
    def save_story(self, story: Dict[str, Any]) -> bool:
        """
        Save a story to the database.
        
        Args:
            story: Story dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            story_id = story.get("id")
            if not story_id:
                return False
            
            now = datetime.now().isoformat()
            serialized = self._serialize_story(story)
            
            # Set timestamps
            if 'created_at' not in serialized:
                serialized['created_at'] = now
            serialized['updated_at'] = now
            serialized['saved_at'] = now
            
            with db_transaction() as conn:
                # Check if story exists
                cursor = conn.execute("SELECT id FROM stories WHERE id = ?", (story_id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing story
                    conn.execute("""
                        UPDATE stories SET
                            genre = ?, premise = ?, outline = ?, scaffold = ?,
                            text = ?, word_count = ?, max_words = ?,
                            draft = ?, revised_draft = ?, revision_history = ?,
                            current_revision = ?, genre_config = ?,
                            updated_at = ?, saved_at = ?
                        WHERE id = ?
                    """, (
                        serialized.get('genre'),
                        serialized.get('premise'),
                        serialized.get('outline'),
                        serialized.get('scaffold'),
                        serialized.get('text'),
                        serialized.get('word_count', 0),
                        serialized.get('max_words', 7500),
                        serialized.get('draft'),
                        serialized.get('revised_draft'),
                        serialized.get('revision_history'),
                        serialized.get('current_revision', 1),
                        serialized.get('genre_config'),
                        serialized['updated_at'],
                        serialized['saved_at'],
                        story_id
                    ))
                else:
                    # Insert new story
                    conn.execute("""
                        INSERT INTO stories (
                            id, genre, premise, outline, scaffold, text,
                            word_count, max_words, draft, revised_draft,
                            revision_history, current_revision, genre_config,
                            created_at, updated_at, saved_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        story_id,
                        serialized.get('genre'),
                        serialized.get('premise'),
                        serialized.get('outline'),
                        serialized.get('scaffold'),
                        serialized.get('text'),
                        serialized.get('word_count', 0),
                        serialized.get('max_words', 7500),
                        serialized.get('draft'),
                        serialized.get('revised_draft'),
                        serialized.get('revision_history'),
                        serialized.get('current_revision', 1),
                        serialized.get('genre_config'),
                        serialized['created_at'],
                        serialized['updated_at'],
                        serialized['saved_at']
                    ))
            
            # Update cache
            if self.use_cache and self._cache:
                try:
                    self._cache.setex(
                        self._get_cache_key(story_id),
                        self.cache_ttl,
                        json.dumps(story)
                    )
                except Exception as e:
                    logger.warning(f"Failed to update cache for story {story_id}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving story {story_id}: {e}", exc_info=True)
            return False
    
    def load_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a story from the database (with cache lookup).
        
        Args:
            story_id: ID of the story to load
            
        Returns:
            Story dictionary or None if not found
        """
        # Check cache first
        if self.use_cache and self._cache:
            try:
                cached = self._cache.get(self._get_cache_key(story_id))
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache lookup failed for story {story_id}: {e}")
        
        # Load from database
        try:
            with db_transaction() as conn:
                cursor = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
                row = cursor.fetchone()
                
                if row:
                    story = self._deserialize_story(row)
                    
                    # Update cache
                    if self.use_cache and self._cache:
                        try:
                            self._cache.setex(
                                self._get_cache_key(story_id),
                                self.cache_ttl,
                                json.dumps(story)
                            )
                        except Exception as e:
                            logger.warning(f"Failed to cache story {story_id}: {e}")
                    
                    return story
        except Exception as e:
            logger.error(f"Error loading story {story_id}: {e}", exc_info=True)
        
        return None
    
    def update_story(self, story_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a story in the database.
        
        Args:
            story_id: ID of the story to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            story = self.load_story(story_id)
            if not story:
                return False
            
            # Merge updates
            story.update(updates)
            story['updated_at'] = datetime.now().isoformat()
            
            return self.save_story(story)
        except Exception as e:
            logger.error(f"Error updating story {story_id}: {e}", exc_info=True)
            return False
    
    def delete_story(self, story_id: str) -> bool:
        """
        Delete a story from the database.
        
        Args:
            story_id: ID of the story to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with db_transaction() as conn:
                conn.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            
            # Remove from cache
            if self.use_cache and self._cache:
                try:
                    self._cache.delete(self._get_cache_key(story_id))
                except Exception as e:
                    logger.warning(f"Failed to remove story {story_id} from cache: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting story {story_id}: {e}", exc_info=True)
            return False
    
    def list_stories(self, page: int = 1, per_page: int = 50, 
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
        try:
            per_page = min(max(1, per_page), 100)  # Between 1 and 100
            page = max(1, page)
            offset = (page - 1) * per_page
            
            with db_transaction() as conn:
                # Build query
                query = "SELECT * FROM stories"
                params = []
                
                if genre:
                    query += " WHERE genre = ?"
                    params.append(genre)
                
                query += " ORDER BY updated_at DESC"
                
                # Get total count
                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cursor = conn.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Get paginated results
                query += " LIMIT ? OFFSET ?"
                params.extend([per_page, offset])
                cursor = conn.execute(query, params)
                
                stories = []
                for row in cursor.fetchall():
                    story = self._deserialize_story(row)
                    # Return only metadata for list view
                    stories.append({
                        "id": story.get("id"),
                        "genre": story.get("genre", "Unknown"),
                        "saved_at": story.get("saved_at"),
                        "updated_at": story.get("updated_at"),
                        "word_count": story.get("word_count", 0),
                        "premise": (
                            story.get("premise", {}).get("idea", "") 
                            if isinstance(story.get("premise"), dict) 
                            else str(story.get("premise", ""))
                        )
                    })
                
                total_pages = (total_count + per_page - 1) // per_page
                
                return {
                    "stories": stories,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total_count,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
        except Exception as e:
            logger.error(f"Error listing stories: {e}", exc_info=True)
            return {"stories": [], "pagination": {"page": 1, "per_page": per_page, 
                                                  "total": 0, "total_pages": 0,
                                                  "has_next": False, "has_prev": False}}
    
    def count_stories(self, genre: Optional[str] = None) -> int:
        """
        Count total number of stories.
        
        Args:
            genre: Optional genre filter
            
        Returns:
            Total count of stories
        """
        try:
            with db_transaction() as conn:
                if genre:
                    cursor = conn.execute("SELECT COUNT(*) FROM stories WHERE genre = ?", (genre,))
                else:
                    cursor = conn.execute("SELECT COUNT(*) FROM stories")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting stories: {e}", exc_info=True)
            return 0

