"""
Database-backed storage for stories.

Provides a scalable storage solution using SQLite (with optional Redis caching)
to replace in-memory storage. Supports pagination and efficient querying.
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import Dict, Optional, Any, Iterator
from datetime import datetime
from contextlib import contextmanager
import logging

from .errors import (
    StorageError,
    DataIntegrityError,
    DatabaseConnectionError,
)

logger: logging.Logger = logging.getLogger(__name__)

# Get the project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_DIR = _PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "stories.db"


def ensure_db_dir() -> Path:
    """Ensure the database directory exists."""
    DB_DIR.mkdir(exist_ok=True)
    return DB_DIR


class ConnectionManager:
    """
    Manages database connections and transactions.
    
    Encapsulates database connection logic to improve testability
    and reduce coupling between StoryStorage and raw SQLite functions.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize connection manager.
        
        Args:
            db_path: Path to database file (defaults to DB_PATH)
        """
        self.db_path = db_path or DB_PATH
        ensure_db_dir()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database transactions."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseConnectionError(f"Database transaction failed: {e}", details={"error_type": type(e).__name__})
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()


# Global connection manager for backward compatibility
_default_connection_manager = ConnectionManager()


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection (backward compatibility wrapper)."""
    return _default_connection_manager.get_connection()


@contextmanager
def db_transaction() -> Iterator[sqlite3.Connection]:
    """Context manager for database transactions (backward compatibility wrapper)."""
    with _default_connection_manager.transaction() as conn:
        yield conn


# Database schema definition
# This centralizes the schema definition to make it easier to maintain and version.
# For schema changes, update this constant and consider implementing migrations.
DB_SCHEMA = """
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
);

CREATE INDEX IF NOT EXISTS idx_stories_updated_at 
ON stories(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_stories_genre 
ON stories(genre);
"""


def init_database(connection_manager: Optional[ConnectionManager] = None) -> None:
    """
    Initialize the database schema.
    
    Uses the centralized DB_SCHEMA constant to create tables and indexes.
    This makes schema changes easier to manage and version.
    
    Args:
        connection_manager: Optional ConnectionManager instance.
                           If not provided, uses default connection manager.
    """
    conn_mgr = connection_manager or _default_connection_manager
    with conn_mgr.transaction() as conn:
        conn.executescript(DB_SCHEMA)


class StoryStorage:
    """
    Database-backed story storage with optional Redis caching.
    
    Provides a scalable alternative to in-memory storage by using SQLite
    for persistence and optional Redis for caching frequently accessed stories.
    """
    
    def __init__(
        self,
        use_cache: bool = False,
        cache_ttl: int = 3600,
        connection_manager: Optional[ConnectionManager] = None
    ):
        """
        Initialize story storage.
        
        Args:
            use_cache: Whether to use Redis caching (default: False)
            cache_ttl: Cache time-to-live in seconds (default: 3600)
            connection_manager: Optional ConnectionManager instance for database access.
                               If not provided, uses default connection manager.
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self._cache = None
        self._conn_manager = connection_manager or _default_connection_manager
        
        if use_cache:
            try:
                import redis
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self._cache = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis cache enabled")
            except ImportError:
                logger.warning("Redis not available, caching disabled")
                self.use_cache = False
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"Failed to connect to Redis (network error): {e}, caching disabled")
                self.use_cache = False
            except Exception as e:
                logger.warning(f"Failed to connect to Redis (unexpected error): {e}, caching disabled")
                self.use_cache = False
        
        # Initialize database (should ideally be called at application startup)
        init_database()
    
    def _get_cache_key(self, story_id: str) -> str:
        """Get cache key for a story."""
        return f"story:{story_id}"
    
    def _serialize_story(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize story data for database storage."""
        serialized = story.copy()
        
        # Convert Pydantic models to dicts first (recursively)
        from src.shortstory.models import PremiseModel, OutlineModel, CharacterModel, StoryMetadata
        # Check if StoryMetadata is a Pydantic model by checking for BaseModel
        from pydantic import BaseModel
        pydantic_models = (PremiseModel, OutlineModel, CharacterModel, StoryMetadata, BaseModel)
        
        def convert_pydantic_models(obj):
            """Recursively convert Pydantic models to dicts."""
            if isinstance(obj, pydantic_models):
                # Convert Pydantic model to dict
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump(exclude_none=True)
                else:
                    return obj.dict(exclude_none=True)
            elif isinstance(obj, dict):
                # Recursively process dict values
                return {k: convert_pydantic_models(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                # Recursively process list items
                return [convert_pydantic_models(item) for item in obj]
            else:
                return obj
        
        # Convert all Pydantic models in the story dict
        for key, value in serialized.items():
            serialized[key] = convert_pydantic_models(value)
        
        # Convert complex objects to JSON strings
        # Fields that are always serialized (frequently accessed)
        json_fields = ['premise', 'outline', 'scaffold', 'draft', 'revised_draft', 
                      'revision_history', 'genre_config']
        for key in json_fields:
            if key in serialized:
                value = serialized[key]
                # Skip if already a string (already serialized)
                if isinstance(value, str):
                    continue
                # Convert dict/list to JSON string
                if isinstance(value, (dict, list)):
                    try:
                        serialized[key] = json.dumps(value)
                    except TypeError as e:
                        # If still can't serialize, log and try to convert again
                        logger.error(f"Failed to serialize {key}: {e}, type: {type(value)}")
                        # Try one more conversion pass
                        converted = convert_pydantic_models(value)
                        if isinstance(converted, (dict, list)):
                            serialized[key] = json.dumps(converted)
                        else:
                            raise
        return serialized
    
    def _deserialize_story(self, row: sqlite3.Row, lazy_fields: bool = False) -> Dict[str, Any]:
        """
        Deserialize story data from database.
        
        Args:
            row: Database row to deserialize
            lazy_fields: If True, skip deserialization of large fields (draft, revised_draft, 
                        revision_history) for performance. These can be deserialized on-demand.
        
        Returns:
            Deserialized story dictionary
        """
        story = dict(row)
        
        # Fields that are always deserialized (frequently accessed, typically small)
        always_deserialize = ['premise', 'outline', 'scaffold', 'genre_config']
        
        # Fields that can be lazily deserialized (potentially large, not always needed)
        lazy_deserialize = ['draft', 'revised_draft', 'revision_history']
        
        # Always deserialize frequently accessed fields
        for key in always_deserialize:
            if story.get(key) and isinstance(story[key], str):
                try:
                    story[key] = json.loads(story[key])
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to deserialize '{key}' for story {story.get('id')}: {e}. "
                        "Keeping as string."
                    )
        
        # Conditionally deserialize large fields
        if not lazy_fields:
            for key in lazy_deserialize:
                if story.get(key) and isinstance(story[key], str):
                    try:
                        story[key] = json.loads(story[key])
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Failed to deserialize '{key}' for story {story.get('id')}: {e}. "
                            "Keeping as string."
                        )
        # If lazy_fields=True, these remain as JSON strings and can be deserialized on-demand
        
        return story
    
    def save_story(self, story: Dict[str, Any]) -> bool:
        """
        Save a story to the database.
        
        Args:
            story: Story dictionary to save
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If story ID is missing
            DataIntegrityError: If data integrity constraints are violated
            DatabaseConnectionError: If database operational error occurs
            StorageError: For other unexpected storage errors
        """
        story_id = story.get("id")
        if not story_id:
            logger.error("Attempted to save story without an ID.")
            raise ValueError("Story ID is required to save a story.")
        
        try:
            
            now = datetime.now().isoformat()
            serialized = self._serialize_story(story)
            
            # Set timestamps
            if 'created_at' not in serialized:
                serialized['created_at'] = now
            serialized['updated_at'] = now
            serialized['saved_at'] = now
            
            with self._conn_manager.transaction() as conn:
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
                except (ConnectionError, TimeoutError, OSError) as e:
                    logger.warning(f"Failed to update cache for story {story_id} (network error): {e}")
                except Exception as e:
                    logger.warning(f"Failed to update cache for story {story_id} (unexpected error): {e}")
            
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Data integrity error saving story {story_id}: {e}", exc_info=True)
            raise DataIntegrityError(
                f"Failed to save story due to data integrity issue: {e}",
                details={"story_id": story_id}
            ) from e
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error saving story {story_id}: {e}", exc_info=True)
            raise DatabaseConnectionError(
                f"Failed to save story due to database error: {e}",
                details={"story_id": story_id}
            ) from e
        except (ValueError, TypeError) as e:  # ValueError for JSON decode errors
            logger.error(f"Serialization error saving story {story_id}: {e}", exc_info=True)
            raise StorageError(
                f"Failed to save story due to serialization error: {e}",
                details={"story_id": story_id}
            ) from e
        except Exception as e:
            logger.critical(f"Unexpected error saving story {story_id}: {e}", exc_info=True)
            raise StorageError(
                f"An unexpected storage error occurred: {e}",
                details={"story_id": story_id}
            ) from e
    
    def load_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a story from the database (with cache lookup).
        
        Args:
            story_id: ID of the story to load
            
        Returns:
            Story dictionary or None if not found
            
        Raises:
            DatabaseConnectionError: If database operational error occurs
            StorageError: For other unexpected storage errors
        """
        # Check cache first
        if self.use_cache and self._cache:
            try:
                cached = self._cache.get(self._get_cache_key(story_id))
                if cached and isinstance(cached, str):
                    return json.loads(cached)
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"Cache lookup failed for story {story_id} (network error): {e}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Cache lookup failed for story {story_id} (deserialization error): {e}")
            except Exception as e:
                logger.warning(f"Cache lookup failed for story {story_id} (unexpected error): {e}")
        
        # Load from database
        try:
            with self._conn_manager.transaction() as conn:
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
                        except (ConnectionError, TimeoutError, OSError) as e:
                            logger.warning(f"Failed to cache story {story_id} (network error): {e}")
                        except Exception as e:
                            logger.warning(f"Failed to cache story {story_id} (unexpected error): {e}")
                    
                    return story
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error loading story {story_id}: {e}", exc_info=True)
            raise DatabaseConnectionError(
                f"Failed to load story due to database error: {e}",
                details={"story_id": story_id}
            ) from e
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Deserialization error loading story {story_id}: {e}", exc_info=True)
            raise StorageError(
                f"Failed to load story due to deserialization error: {e}",
                details={"story_id": story_id}
            ) from e
        except Exception as e:
            logger.critical(f"Unexpected error loading story {story_id}: {e}", exc_info=True)
            raise StorageError(
                f"An unexpected storage error occurred: {e}",
                details={"story_id": story_id}
            ) from e
        
        return None
    
    def update_story(self, story_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a story in the database.
        
        Args:
            story_id: ID of the story to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If story is not found
            DataIntegrityError: If data integrity constraints are violated
            DatabaseConnectionError: If database operational error occurs
            StorageError: For other unexpected storage errors
        """
        story = self.load_story(story_id)
        if not story:
            from .errors import NotFoundError
            raise NotFoundError("Story", story_id)
        
        # Merge updates
        story.update(updates)
        story['updated_at'] = datetime.now().isoformat()
        
        return self.save_story(story)
    
    def delete_story(self, story_id: str) -> bool:
        """
        Delete a story from the database.
        
        Args:
            story_id: ID of the story to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._conn_manager.transaction() as conn:
                conn.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            
            # Remove from cache
            if self.use_cache and self._cache:
                try:
                    self._cache.delete(self._get_cache_key(story_id))
                except (ConnectionError, TimeoutError, OSError) as e:
                    logger.warning(f"Failed to remove story {story_id} from cache (network error): {e}")
                except Exception as e:
                    logger.warning(f"Failed to remove story {story_id} from cache (unexpected error): {e}")
            
            return True
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error deleting story {story_id}: {e}", exc_info=True)
            return False
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
            
            with self._conn_manager.transaction() as conn:
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
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error listing stories: {e}", exc_info=True)
            return {"stories": [], "pagination": {"page": 1, "per_page": per_page, 
                                                  "total": 0, "total_pages": 0,
                                                  "has_next": False, "has_prev": False}}
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Deserialization error listing stories: {e}", exc_info=True)
            return {"stories": [], "pagination": {"page": 1, "per_page": per_page, 
                                                  "total": 0, "total_pages": 0,
                                                  "has_next": False, "has_prev": False}}
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
            with self._conn_manager.transaction() as conn:
                if genre:
                    cursor = conn.execute("SELECT COUNT(*) FROM stories WHERE genre = ?", (genre,))
                else:
                    cursor = conn.execute("SELECT COUNT(*) FROM stories")
                return cursor.fetchone()[0]
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error counting stories: {e}", exc_info=True)
            return 0
        except Exception as e:
            logger.error(f"Error counting stories: {e}", exc_info=True)
            return 0

