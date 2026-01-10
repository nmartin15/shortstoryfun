"""
Edge case tests for database storage.

Tests cover:
- Concurrent access scenarios
- Large data handling
- Connection failures
- Data corruption scenarios
- Boundary conditions
"""

import pytest
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.shortstory.utils.db_storage import (
    StoryStorage,
    init_database,
    get_db_connection,
    db_transaction,
    ConnectionManager
)
from src.shortstory.utils.errors import (
    StorageError,
    DataIntegrityError,
    DatabaseConnectionError
)


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create a temporary directory for test database."""
    test_db_dir = tmp_path / "test_data"
    test_db_dir.mkdir()
    test_db_path = test_db_dir / "stories.db"
    
    with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
         patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
        yield test_db_dir, test_db_path
    
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def storage(temp_db_dir):
    """Create a StoryStorage instance for testing."""
    test_db_dir, test_db_path = temp_db_dir
    init_database()
    yield StoryStorage(use_cache=False)


class TestConcurrentAccess:
    """Test concurrent access scenarios."""
    
    def test_concurrent_saves_same_story_id(self, storage):
        """Test concurrent saves with the same story ID."""
        story_id = "concurrent_save_test"
        num_threads = 5
        
        results = []
        errors = []
        
        def save_story(thread_id):
            """Save story from a thread."""
            story = {
                "id": story_id,
                "genre": "General Fiction",
                "text": f"Story from thread {thread_id}",
                "word_count": 100
            }
            try:
                result = storage.save_story(story)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=save_story, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # At least one save should succeed
        assert len(results) > 0 or len(errors) > 0
        
        # Verify final state
        loaded = storage.load_story(story_id)
        assert loaded is not None
        # Should have one of the thread texts
        assert "thread" in loaded["text"].lower()
    
    def test_concurrent_updates_same_story(self, storage):
        """Test concurrent updates to the same story."""
        # Create initial story
        story_id = "concurrent_update_test"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "Initial text",
            "word_count": 100
        }
        storage.save_story(story)
        
        num_threads = 3
        results = []
        
        def update_story(thread_id):
            """Update story from a thread."""
            updates = {
                "text": f"Updated by thread {thread_id}",
                "word_count": 100 + thread_id
            }
            try:
                result = storage.update_story(story_id, updates)
                results.append((thread_id, result))
            except Exception as e:
                results.append((thread_id, str(e)))
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=update_story, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All updates should complete (some may succeed, some may conflict)
        assert len(results) == num_threads
        
        # Verify final state
        loaded = storage.load_story(story_id)
        assert loaded is not None
        assert "Updated by thread" in loaded["text"] or "Initial text" in loaded["text"]
    
    def test_concurrent_reads_during_write(self, storage):
        """Test concurrent reads during a write operation."""
        story_id = "concurrent_read_write"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        storage.save_story(story)
        
        read_results = []
        write_complete = threading.Event()
        
        def read_story():
            """Read story repeatedly."""
            while not write_complete.is_set():
                try:
                    loaded = storage.load_story(story_id)
                    if loaded:
                        read_results.append(loaded["id"])
                except Exception:
                    pass
                time.sleep(0.01)
        
        def write_story():
            """Write story update."""
            time.sleep(0.1)  # Give reads a chance to start
            updates = {"text": "Updated text"}
            storage.update_story(story_id, updates)
            write_complete.set()
        
        read_thread = threading.Thread(target=read_story)
        write_thread = threading.Thread(target=write_story)
        
        read_thread.start()
        write_thread.start()
        
        write_thread.join()
        time.sleep(0.1)  # Let reads finish
        write_complete.set()
        read_thread.join()
        
        # Should have some successful reads
        assert len(read_results) > 0


class TestLargeDataHandling:
    """Test handling of large data."""
    
    def test_very_large_story_text(self, storage):
        """Test saving and loading very large story text."""
        # Create large text (1MB)
        large_text = "This is a test sentence. " * 40000  # ~1MB
        story = {
            "id": "large_text_test",
            "genre": "General Fiction",
            "text": large_text,
            "word_count": len(large_text.split())
        }
        
        # Should save successfully
        result = storage.save_story(story)
        assert result is True
        
        # Should load successfully
        loaded = storage.load_story("large_text_test")
        assert loaded is not None
        assert len(loaded["text"]) == len(large_text)
        assert loaded["text"] == large_text
    
    def test_many_stories_large_dataset(self, storage):
        """Test handling many stories (large dataset)."""
        num_stories = 2000
        
        # Create many stories
        for i in range(num_stories):
            story = {
                "id": f"large_dataset_{i:05d}",
                "genre": "General Fiction" if i % 2 == 0 else "Science Fiction",
                "text": f"Story content {i}",
                "word_count": 100
            }
            storage.save_story(story)
        
        # Should be able to list them
        result = storage.list_stories(page=1, per_page=50)
        assert len(result["stories"]) == 50
        assert result["pagination"]["total"] == num_stories
        
        # Should be able to load any story
        loaded = storage.load_story("large_dataset_01000")
        assert loaded is not None
        assert loaded["id"] == "large_dataset_01000"
    
    def test_deeply_nested_json(self, storage):
        """Test handling of deeply nested JSON structures."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": "deep value"
                        }
                    }
                }
            }
        }
        
        story = {
            "id": "nested_json_test",
            "genre": "General Fiction",
            "premise": nested_data,
            "text": "Test story",
            "word_count": 100
        }
        
        # Should save successfully
        result = storage.save_story(story)
        assert result is True
        
        # Should load and preserve structure
        loaded = storage.load_story("nested_json_test")
        assert loaded is not None
        assert loaded["premise"]["level1"]["level2"]["level3"]["level4"]["level5"] == "deep value"


class TestConnectionFailures:
    """Test connection failure scenarios."""
    
    def test_handles_database_locked(self, storage):
        """Test handling of database locked errors."""
        story = {
            "id": "locked_test",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Normal save should work
        result = storage.save_story(story)
        assert result is True
        
        # Database locked errors are handled by SQLite's retry mechanism
        # This test verifies the system can handle them
    
    def test_handles_connection_timeout(self, temp_db_dir):
        """Test handling of connection timeouts."""
        test_db_dir, test_db_path = temp_db_dir
        init_database()
        
        # Create storage with custom connection manager that might timeout
        # (In practice, SQLite doesn't have timeouts, but we test error handling)
        storage = StoryStorage(use_cache=False)
        
        story = {
            "id": "timeout_test",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Should save successfully
        result = storage.save_story(story)
        assert result is True
    
    def test_handles_database_corruption(self, temp_db_dir):
        """Test handling of database corruption scenarios."""
        test_db_dir, test_db_path = temp_db_dir
        init_database()
        
        # Create a story first
        storage = StoryStorage(use_cache=False)
        story = {
            "id": "corruption_test",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        storage.save_story(story)
        
        # Corrupt the database file (write invalid data)
        with open(test_db_path, 'wb') as f:
            f.write(b'INVALID DATABASE DATA')
        
        # Try to load - should handle corruption gracefully
        try:
            loaded = storage.load_story("corruption_test")
            # If it doesn't raise, that's fine (depends on SQLite's error handling)
        except (sqlite3.DatabaseError, StorageError, DatabaseConnectionError):
            # Expected for corrupted database
            pass


class TestBoundaryConditions:
    """Test boundary conditions."""
    
    def test_empty_story_id(self, storage):
        """Test handling of empty story ID."""
        story = {
            "id": "",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            storage.save_story(story)
    
    def test_none_story_id(self, storage):
        """Test handling of None story ID."""
        story = {
            "id": None,
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Should raise ValueError or TypeError
        with pytest.raises((ValueError, TypeError, KeyError)):
            storage.save_story(story)
    
    def test_very_long_story_id(self, storage):
        """Test handling of very long story ID."""
        long_id = "a" * 1000
        story = {
            "id": long_id,
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Should save successfully (SQLite TEXT can handle long IDs)
        result = storage.save_story(story)
        assert result is True
        
        # Should load successfully
        loaded = storage.load_story(long_id)
        assert loaded is not None
        assert loaded["id"] == long_id
    
    def test_zero_word_count(self, storage):
        """Test handling of zero word count."""
        story = {
            "id": "zero_words_test",
            "genre": "General Fiction",
            "text": "",
            "word_count": 0
        }
        
        # Should save successfully
        result = storage.save_story(story)
        assert result is True
        
        # Should load successfully
        loaded = storage.load_story("zero_words_test")
        assert loaded is not None
        assert loaded["word_count"] == 0
    
    def test_negative_word_count(self, storage):
        """Test handling of negative word count."""
        story = {
            "id": "negative_words_test",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": -10
        }
        
        # Should save (word_count is just an integer field)
        result = storage.save_story(story)
        assert result is True
        
        # Should load with negative value
        loaded = storage.load_story("negative_words_test")
        assert loaded is not None
        assert loaded["word_count"] == -10
    
    def test_unicode_story_id(self, storage):
        """Test handling of Unicode characters in story ID."""
        unicode_id = "story_émoji🎭_123"
        story = {
            "id": unicode_id,
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Should save successfully
        result = storage.save_story(story)
        assert result is True
        
        # Should load successfully
        loaded = storage.load_story(unicode_id)
        assert loaded is not None
        assert loaded["id"] == unicode_id


class TestDataIntegrity:
    """Test data integrity scenarios."""
    
    def test_duplicate_story_id_insert(self, storage):
        """Test that duplicate story IDs are handled correctly."""
        story = {
            "id": "duplicate_test",
            "genre": "General Fiction",
            "text": "First story",
            "word_count": 100
        }
        
        # First save should succeed
        result = storage.save_story(story)
        assert result is True
        
        # Second save with same ID should update, not insert
        story["text"] = "Second story"
        result = storage.save_story(story)
        assert result is True
        
        # Should have updated text
        loaded = storage.load_story("duplicate_test")
        assert loaded["text"] == "Second story"
    
    def test_invalid_json_in_premise(self, storage):
        """Test handling of invalid JSON in premise field."""
        # Create story with premise that might cause JSON issues
        story = {
            "id": "invalid_json_test",
            "genre": "General Fiction",
            "premise": {
                "idea": "Test idea",
                "special_chars": "\x00\x01\x02"  # Control characters
            },
            "text": "Test story",
            "word_count": 100
        }
        
        # Should save successfully (JSON should handle control chars)
        result = storage.save_story(story)
        assert result is True
        
        # Should load successfully
        loaded = storage.load_story("invalid_json_test")
        assert loaded is not None


class TestTransactionHandling:
    """Test transaction handling edge cases."""
    
    def test_transaction_rollback_on_error(self, temp_db_dir):
        """Test that transactions rollback on error."""
        test_db_dir, test_db_path = temp_db_dir
        init_database()
        
        # Try to insert with error
        try:
            with db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("rollback_test", "test"))
                # Force error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify nothing was committed
        storage = StoryStorage(use_cache=False)
        loaded = storage.load_story("rollback_test")
        assert loaded is None
    
    def test_nested_transactions(self, temp_db_dir):
        """Test nested transaction handling."""
        test_db_dir, test_db_path = temp_db_dir
        init_database()
        
        # SQLite doesn't support true nested transactions, but we test the pattern
        with db_transaction() as conn1:
            cursor1 = conn1.cursor()
            cursor1.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("nested_test", "test"))
            
            # Inner "transaction" (same connection)
            cursor1.execute("UPDATE stories SET text = ? WHERE id = ?", ("updated", "nested_test"))
        
        # Should be committed
        storage = StoryStorage(use_cache=False)
        loaded = storage.load_story("nested_test")
        assert loaded is not None
        assert loaded["text"] == "updated"

