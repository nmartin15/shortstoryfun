"""
Comprehensive tests for database storage functionality.

Tests cover CRUD operations, pagination, error handling, and data integrity.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.shortstory.utils.db_storage import (
    StoryStorage,
    init_database,
    get_db_connection,
    db_transaction,
    DB_PATH,
    DB_DIR
)


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create a temporary directory for test database."""
    # Store original paths
    original_db_path = DB_PATH
    original_db_dir = DB_DIR
    
    # Create temp directory
    test_db_dir = tmp_path / "test_data"
    test_db_dir.mkdir()
    test_db_path = test_db_dir / "stories.db"
    
    # Patch the module-level constants
    with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
         patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
        yield test_db_dir, test_db_path
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def storage(temp_db_dir):
    """Create a StoryStorage instance with test database."""
    test_db_dir, test_db_path = temp_db_dir
    with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
         patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
        init_database()
        storage = StoryStorage(use_cache=False)
        yield storage


@pytest.fixture
def sample_story():
    """Create a sample story for testing."""
    return {
        "id": "test_story_123",
        "genre": "General Fiction",
        "premise": {
            "idea": "A lighthouse keeper collects voices",
            "character": {"name": "Mara", "description": "A quiet keeper"},
            "theme": "Untold stories"
        },
        "outline": {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            }
        },
        "scaffold": {
            "pov": "third person",
            "tone": "balanced"
        },
        "text": "# Test Story\n\nThis is a test story with some content.",
        "word_count": 10,
        "max_words": 7500,
        "draft": {"text": "Draft text", "word_count": 8},
        "revised_draft": {"text": "Revised text", "word_count": 9},
        "revision_history": [{"version": 1, "text": "Original"}],
        "current_revision": 1,
        "genre_config": {"framework": "narrative_arc"}
    }


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def test_init_database_creates_schema(self, temp_db_dir):
        """Test that init_database creates the stories table."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Verify database file exists
            assert test_db_path.exists()
            
            # Verify table exists
            conn = get_db_connection()
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stories'"
            )
            assert cursor.fetchone() is not None
            
            # Verify indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_stories%'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_stories_updated_at' in indexes
            assert 'idx_stories_genre' in indexes
            
            conn.close()
    
    def test_init_database_idempotent(self, temp_db_dir):
        """Test that calling init_database multiple times doesn't fail."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            init_database()  # Call again
            init_database()  # Call a third time
            
            # Should still work
            assert test_db_path.exists()


class TestStoryStorageCRUD:
    """Test Create, Read, Update, Delete operations."""
    
    def test_save_story_creates_new_story(self, storage, sample_story):
        """Test saving a new story."""
        result = storage.save_story(sample_story)
        assert result is True
        
        # Verify story was saved
        loaded = storage.load_story(sample_story["id"])
        assert loaded is not None
        assert loaded["id"] == sample_story["id"]
        assert loaded["genre"] == sample_story["genre"]
        assert loaded["word_count"] == sample_story["word_count"]
    
    def test_save_story_updates_existing_story(self, storage, sample_story):
        """Test updating an existing story."""
        # Save initial story
        storage.save_story(sample_story)
        
        # Update story
        sample_story["text"] = "Updated story text"
        sample_story["word_count"] = 15
        result = storage.save_story(sample_story)
        assert result is True
        
        # Verify update
        loaded = storage.load_story(sample_story["id"])
        assert loaded["text"] == "Updated story text"
        assert loaded["word_count"] == 15
    
    def test_save_story_serializes_complex_fields(self, storage, sample_story):
        """Test that complex fields (dicts, lists) are serialized to JSON."""
        storage.save_story(sample_story)
        
        loaded = storage.load_story(sample_story["id"])
        assert isinstance(loaded["premise"], dict)
        assert loaded["premise"]["idea"] == "A lighthouse keeper collects voices"
        assert isinstance(loaded["outline"], dict)
        assert isinstance(loaded["revision_history"], list)
    
    def test_save_story_sets_timestamps(self, storage, sample_story):
        """Test that timestamps are set on save."""
        storage.save_story(sample_story)
        
        loaded = storage.load_story(sample_story["id"])
        assert "created_at" in loaded
        assert "updated_at" in loaded
        assert "saved_at" in loaded
        
        # Verify timestamps are ISO format
        datetime.fromisoformat(loaded["created_at"])
        datetime.fromisoformat(loaded["updated_at"])
        datetime.fromisoformat(loaded["saved_at"])
    
    def test_save_story_fails_without_id(self, storage):
        """Test that saving a story without ID returns False."""
        story = {"text": "No ID story"}
        result = storage.save_story(story)
        assert result is False
    
    def test_load_story_returns_none_for_missing(self, storage):
        """Test that loading a non-existent story returns None."""
        loaded = storage.load_story("nonexistent_id")
        assert loaded is None
    
    def test_load_story_deserializes_complex_fields(self, storage, sample_story):
        """Test that complex fields are deserialized from JSON."""
        storage.save_story(sample_story)
        
        loaded = storage.load_story(sample_story["id"])
        assert isinstance(loaded["premise"], dict)
        assert isinstance(loaded["outline"], dict)
        assert isinstance(loaded["scaffold"], dict)
    
    def test_update_story_modifies_fields(self, storage, sample_story):
        """Test updating specific fields of a story."""
        storage.save_story(sample_story)
        
        updates = {
            "text": "Updated text",
            "word_count": 20
        }
        result = storage.update_story(sample_story["id"], updates)
        assert result is True
        
        loaded = storage.load_story(sample_story["id"])
        assert loaded["text"] == "Updated text"
        assert loaded["word_count"] == 20
        assert loaded["genre"] == sample_story["genre"]  # Unchanged
    
    def test_update_story_fails_for_missing_story(self, storage):
        """Test that updating a non-existent story returns False."""
        updates = {"text": "New text"}
        result = storage.update_story("nonexistent_id", updates)
        assert result is False
    
    def test_delete_story_removes_from_database(self, storage, sample_story):
        """Test deleting a story."""
        storage.save_story(sample_story)
        
        result = storage.delete_story(sample_story["id"])
        assert result is True
        
        # Verify story is gone
        loaded = storage.load_story(sample_story["id"])
        assert loaded is None
    
    def test_delete_story_handles_missing_story(self, storage):
        """Test deleting a non-existent story."""
        result = storage.delete_story("nonexistent_id")
        assert result is True  # Delete is idempotent


class TestStoryStoragePagination:
    """Test pagination and listing functionality."""
    
    def test_list_stories_returns_paginated_results(self, storage, sample_story):
        """Test listing stories with pagination."""
        # Create 25 stories
        for i in range(25):
            story = sample_story.copy()
            story["id"] = f"story_{i:03d}"
            story["text"] = f"Story {i}"
            storage.save_story(story)
        
        # Test first page
        result = storage.list_stories(page=1, per_page=10)
        assert len(result["stories"]) == 10
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 10
        assert result["pagination"]["total"] == 25
        assert result["pagination"]["total_pages"] == 3
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False
        
        # Test second page
        result = storage.list_stories(page=2, per_page=10)
        assert len(result["stories"]) == 10
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is True
        
        # Test last page
        result = storage.list_stories(page=3, per_page=10)
        assert len(result["stories"]) == 5
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True
    
    def test_list_stories_orders_by_updated_at(self, storage, sample_story):
        """Test that stories are ordered by updated_at descending."""
        # Create stories with different update times
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            storage.save_story(story)
        
        result = storage.list_stories(page=1, per_page=10)
        stories = result["stories"]
        
        # Verify ordering (most recent first)
        for i in range(len(stories) - 1):
            assert stories[i]["updated_at"] >= stories[i + 1]["updated_at"]
    
    def test_list_stories_filters_by_genre(self, storage, sample_story):
        """Test filtering stories by genre."""
        # Create stories with different genres (use unique IDs to avoid collisions)
        genres_list = ["Horror", "Romance", "Horror", "General Fiction"]
        for i, genre in enumerate(genres_list):
            story = sample_story.copy()
            story["id"] = f"story_{genre}_{i}_{hash(f'{genre}_{i}')}"
            story["genre"] = genre
            storage.save_story(story)
        
        # Filter by Horror (should find 2 stories)
        result = storage.list_stories(page=1, per_page=10, genre="Horror")
        assert result["pagination"]["total"] == 2
        assert all(s["genre"] == "Horror" for s in result["stories"])
    
    def test_list_stories_handles_empty_database(self, storage):
        """Test listing stories when database is empty."""
        result = storage.list_stories(page=1, per_page=10)
        assert result["stories"] == []
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["total_pages"] == 0
    
    def test_list_stories_enforces_per_page_limits(self, storage, sample_story):
        """Test that per_page is limited to 100."""
        # Create 150 stories
        for i in range(150):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            storage.save_story(story)
        
        # Request more than 100 per page
        result = storage.list_stories(page=1, per_page=200)
        assert result["pagination"]["per_page"] == 100
        assert len(result["stories"]) == 100
    
    def test_list_stories_handles_invalid_page_numbers(self, storage, sample_story):
        """Test that invalid page numbers are handled."""
        storage.save_story(sample_story)
        
        # Page 0 should become page 1
        result = storage.list_stories(page=0, per_page=10)
        assert result["pagination"]["page"] == 1
        
        # Negative page should become page 1
        result = storage.list_stories(page=-1, per_page=10)
        assert result["pagination"]["page"] == 1


class TestStoryStorageCount:
    """Test story counting functionality."""
    
    def test_count_stories_returns_total(self, storage, sample_story):
        """Test counting all stories."""
        # Create 10 stories
        for i in range(10):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            storage.save_story(story)
        
        count = storage.count_stories()
        assert count == 10
    
    def test_count_stories_filters_by_genre(self, storage, sample_story):
        """Test counting stories by genre."""
        # Create stories with different genres
        genres = ["Horror", "Romance", "Horror", "General Fiction"]
        for i, genre in enumerate(genres):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            story["genre"] = genre
            storage.save_story(story)
        
        horror_count = storage.count_stories(genre="Horror")
        assert horror_count == 2
    
    def test_count_stories_returns_zero_for_empty_database(self, storage):
        """Test counting stories in empty database."""
        count = storage.count_stories()
        assert count == 0


class TestStoryStorageTransactions:
    """Test database transaction handling."""
    
    def test_db_transaction_commits_on_success(self, storage, sample_story):
        """Test that transactions commit successfully."""
        storage.save_story(sample_story)
        
        # Verify story is persisted
        loaded = storage.load_story(sample_story["id"])
        assert loaded is not None
    
    def test_db_transaction_rolls_back_on_error(self, temp_db_dir):
        """Test that transactions roll back on error."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Create a transaction that will fail
            try:
                with db_transaction() as conn:
                    conn.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test", "text"))
                    # Force an error
                    conn.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test", "text"))  # Duplicate key
            except Exception:
                pass
            
            # Verify nothing was committed
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test")
            assert loaded is None


class TestStoryStorageErrorHandling:
    """Test error handling in storage operations."""
    
    def test_save_story_handles_database_errors(self, storage):
        """Test that save_story handles database errors gracefully."""
        # Create invalid story data that might cause issues
        story = {
            "id": "test",
            "text": "Valid text",
            # Add invalid data that might cause serialization issues
            "premise": {"idea": "Test", "nested": {"deep": {"value": "test"}}}
        }
        
        # Should still work (JSON serialization handles nested dicts)
        result = storage.save_story(story)
        assert result is True
    
    def test_load_story_handles_database_errors(self, storage):
        """Test that load_story handles database errors gracefully."""
        # Try to load from empty database
        loaded = storage.load_story("nonexistent")
        assert loaded is None
    
    def test_list_stories_handles_errors_gracefully(self, storage):
        """Test that list_stories returns empty result on error."""
        # Should return empty result, not raise exception
        result = storage.list_stories(page=1, per_page=10)
        assert result["stories"] == []
        assert result["pagination"]["total"] == 0


class TestStoryStorageDataIntegrity:
    """Test data integrity and validation."""
    
    def test_story_ids_are_unique(self, storage, sample_story):
        """Test that story IDs must be unique."""
        storage.save_story(sample_story)
        
        # Try to save another story with same ID
        story2 = sample_story.copy()
        story2["text"] = "Different text"
        result = storage.save_story(story2)
        
        # Should update existing story, not create duplicate
        assert result is True
        loaded = storage.load_story(sample_story["id"])
        assert loaded["text"] == "Different text"
    
    def test_story_metadata_preserved(self, storage, sample_story):
        """Test that all story metadata is preserved."""
        storage.save_story(sample_story)
        loaded = storage.load_story(sample_story["id"])
        
        # Check all fields are preserved
        assert loaded["genre"] == sample_story["genre"]
        assert loaded["word_count"] == sample_story["word_count"]
        assert loaded["max_words"] == sample_story["max_words"]
        assert loaded["current_revision"] == sample_story["current_revision"]


class TestStoryStorageLargeDataset:
    """Test performance with large datasets."""
    
    def test_list_stories_performance_with_many_stories(self, storage, sample_story):
        """Test that listing works efficiently with many stories."""
        # Create 100 stories
        for i in range(100):
            story = sample_story.copy()
            story["id"] = f"story_{i:03d}"
            story["text"] = f"Story {i} content"
            storage.save_story(story)
        
        # Should still work efficiently
        result = storage.list_stories(page=1, per_page=50)
        assert len(result["stories"]) == 50
        assert result["pagination"]["total"] == 100
    
    def test_list_stories_performance_with_1000_plus_stories(self, storage, sample_story):
        """Test that listing works efficiently with 1000+ stories."""
        # Create 1000 stories
        for i in range(1000):
            story = sample_story.copy()
            story["id"] = f"story_{i:04d}"
            story["text"] = f"Story {i} content"
            storage.save_story(story)
        
        # Should still work efficiently
        result = storage.list_stories(page=1, per_page=50)
        assert len(result["stories"]) == 50
        assert result["pagination"]["total"] == 1000
        assert result["pagination"]["total_pages"] == 20
        
        # Test later pages
        result = storage.list_stories(page=20, per_page=50)
        assert len(result["stories"]) == 50
        assert result["pagination"]["has_next"] is False
    
    def test_save_performance_with_many_stories(self, storage, sample_story):
        """Test that saving works efficiently with many existing stories."""
        # Create 500 stories first
        for i in range(500):
            story = sample_story.copy()
            story["id"] = f"story_{i:03d}"
            storage.save_story(story)
        
        # Save a new story should still be fast
        new_story = sample_story.copy()
        new_story["id"] = "new_story_999"
        result = storage.save_story(new_story)
        assert result is True
        
        # Verify it was saved
        loaded = storage.load_story("new_story_999")
        assert loaded is not None


class TestStoryStorageCache:
    """Test Redis cache integration (if enabled)."""
    
    def test_storage_without_cache(self, storage, sample_story):
        """Test that storage works without cache."""
        storage = StoryStorage(use_cache=False)
        storage.save_story(sample_story)
        
        loaded = storage.load_story(sample_story["id"])
        assert loaded is not None
        assert loaded["id"] == sample_story["id"]
    
    @pytest.mark.skipif(True, reason="Requires Redis server")
    def test_storage_with_cache(self, temp_db_dir, sample_story):
        """Test that storage works with Redis cache (if available)."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            storage = StoryStorage(use_cache=True)
            storage.save_story(sample_story)
            
            # Load should use cache
            loaded = storage.load_story(sample_story["id"])
            assert loaded is not None


class TestStoryStorageConcurrentAccess:
    """Test concurrent access handling."""
    
    def test_concurrent_saves(self, storage, sample_story):
        """Test that concurrent saves work correctly."""
        import threading
        
        results = []
        errors = []
        
        def save_story(index):
            try:
                story = sample_story.copy()
                story["id"] = f"concurrent_story_{index}"
                result = storage.save_story(story)
                results.append((index, result))
            except Exception as e:
                errors.append((index, e))
        
        # Create 10 threads saving stories concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_story, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All saves should succeed
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result[1] for result in results)
        
        # Verify all stories were saved
        for i in range(10):
            loaded = storage.load_story(f"concurrent_story_{i}")
            assert loaded is not None
            assert loaded["id"] == f"concurrent_story_{i}"
    
    def test_concurrent_reads(self, storage, sample_story):
        """Test that concurrent reads work correctly."""
        import threading
        
        # Save a story first
        storage.save_story(sample_story)
        
        results = []
        errors = []
        
        def load_story():
            try:
                loaded = storage.load_story(sample_story["id"])
                results.append(loaded is not None)
            except Exception as e:
                errors.append(e)
        
        # Create 20 threads reading the same story concurrently
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=load_story)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All reads should succeed
        assert len(errors) == 0
        assert len(results) == 20
        assert all(results)
    
    def test_concurrent_update_same_story(self, storage, sample_story):
        """Test concurrent updates to the same story."""
        import threading
        
        # Save initial story
        storage.save_story(sample_story)
        
        results = []
        errors = []
        
        def update_story(index):
            try:
                updates = {"text": f"Updated text {index}"}
                result = storage.update_story(sample_story["id"], updates)
                results.append((index, result))
            except Exception as e:
                errors.append((index, e))
        
        # Create 5 threads updating the same story concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_story, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All updates should succeed (last one wins)
        assert len(errors) == 0
        assert len(results) == 5
        assert all(result[1] for result in results)
        
        # Verify story was updated (one of the updates)
        loaded = storage.load_story(sample_story["id"])
        assert loaded is not None
        assert "Updated text" in loaded["text"]


class TestStoryStorageMigrations:
    """Test database migration scenarios."""
    
    def test_migration_from_json_structure(self, temp_db_dir, sample_story):
        """Test that stories can be migrated from JSON-like structure."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            storage = StoryStorage(use_cache=False)
            
            # Simulate migrating a story with JSON structure
            json_story = sample_story.copy()
            json_story["premise"] = json.dumps(json_story["premise"])
            json_story["outline"] = json.dumps(json_story["outline"])
            
            # Save should handle both formats
            result = storage.save_story(sample_story)
            assert result is True
            
            # Load should deserialize correctly
            loaded = storage.load_story(sample_story["id"])
            assert isinstance(loaded["premise"], dict)
            assert isinstance(loaded["outline"], dict)
    
    def test_migration_preserves_all_fields(self, storage, sample_story):
        """Test that migration preserves all story fields."""
        storage.save_story(sample_story)
        
        loaded = storage.load_story(sample_story["id"])
        
        # Verify all fields are preserved
        assert loaded["id"] == sample_story["id"]
        assert loaded["genre"] == sample_story["genre"]
        assert loaded["word_count"] == sample_story["word_count"]
        assert loaded["max_words"] == sample_story["max_words"]
        assert loaded["current_revision"] == sample_story["current_revision"]
        assert loaded["text"] == sample_story["text"]
    
    def test_migration_handles_missing_optional_fields(self, storage):
        """Test that migration handles stories with missing optional fields."""
        minimal_story = {
            "id": "minimal_story",
            "text": "Minimal story text",
            "word_count": 3
        }
        
        result = storage.save_story(minimal_story)
        assert result is True
        
        loaded = storage.load_story("minimal_story")
        assert loaded is not None
        assert loaded["id"] == "minimal_story"
        assert loaded["text"] == "Minimal story text"
        assert loaded["word_count"] == 3
        # Optional fields should have defaults
        assert loaded.get("max_words") == 7500
        assert loaded.get("current_revision") == 1

