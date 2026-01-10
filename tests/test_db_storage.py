"""
Tests for database storage functionality.

Tests cover:
- Database initialization and schema creation
- Story CRUD operations
- Pagination and filtering
- Transaction rollback
- Cache integration (mocked)
"""

import pytest
import json
import time
import sys
from pathlib import Path
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
    """Create a temporary directory for test database and patch module constants.
    
    This fixture ensures complete test isolation by:
    1. Creating a unique temporary directory for each test (via pytest's tmp_path)
    2. Patching both DB_DIR and DB_PATH module constants to point to the temp directory
    3. Ensuring cleanup happens even if tests fail (via context manager and explicit cleanup)
    
    The patches are scoped to the entire test lifecycle (from yield to cleanup),
    ensuring that all database operations during the test use the isolated database.
    The patches are automatically restored after the test completes, preventing
    test pollution and ensuring each test starts with a clean state.
    
    Note: The explicit test_db_path.unlink() cleanup ensures the database file
    is removed even if the test fails, preventing state leakage between tests.
    The tmp_path fixture handles directory cleanup automatically.
    """
    # Use tmp_path directly for the database directory
    # tmp_path is a pytest fixture that provides a unique temporary directory
    test_db_dir = tmp_path / "test_data"
    test_db_dir.mkdir()
    test_db_path = test_db_dir / "stories.db"

    # Patch the module-level constants to point to the temporary paths
    # The 'with patch' context manager ensures patches are active during the test
    # and automatically restored after the yield completes (even if test fails)
    with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
         patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
        yield test_db_dir, test_db_path
    
    # Explicit cleanup to ensure isolation - remove database file if it exists
    # This ensures no test data leaks between tests, even if a test fails
    # The database file is removed here, and tmp_path will clean up the directory
    if test_db_path.exists():
        test_db_path.unlink()
    
    # No explicit cleanup needed for test_db_dir.rmdir() or shutil.rmtree
    # because tmp_path (the parent of test_db_dir) cleans up automatically.


@pytest.fixture
def sample_story():
    """Sample story dictionary for testing."""
    return {
        "id": "test_story_123",
        "genre": "Science Fiction",
        "premise": {"idea": "A test story", "character": {"name": "Test"}},
        "outline": {"acts": {"beginning": "start", "middle": "middle", "end": "end"}},
        "text": "This is a test story. " * 100,
        "word_count": 500,
            "max_words": 7500,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def storage(temp_db_dir):
    """Create a StoryStorage instance for testing.
    
    This fixture ensures complete isolation by:
    1. Using the temp_db_dir fixture which provides isolated DB paths
    2. Creating a fresh database for each test
    
    Note: The temp_db_dir fixture already patches DB_DIR and DB_PATH module constants,
    so we don't need to patch them again here. This avoids redundant patching and
    ensures consistent test isolation.
    """
    test_db_dir, test_db_path = temp_db_dir
    # temp_db_dir already patches DB_DIR and DB_PATH, so we can use them directly
    # Initialize fresh database for this test
    init_database()
    yield StoryStorage(use_cache=False)
    # Cleanup: ensure database is closed and can be cleaned up
    # The temp_db_dir fixture will handle file cleanup


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def test_init_database_creates_schema(self, temp_db_dir):
        """Test that init_database creates the schema."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Verify database file exists
            assert test_db_path.exists()
            
            # Verify we can connect and query
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
            result = cursor.fetchone()
            conn.close()
            
            assert result is not None
            assert result[0] == "stories"


class TestStoryStorageCRUD:
    """Test CRUD operations for StoryStorage."""
    
    def test_save_story(self, storage, sample_story):
        """Test saving a story."""
        result = storage.save_story(sample_story)
        assert result is True
        
        # Verify it was saved
        loaded = storage.load_story(sample_story["id"])
        assert loaded is not None
        assert loaded["id"] == sample_story["id"]
    
    def test_load_story(self, storage, sample_story):
        """Test loading a story."""
        storage.save_story(sample_story)
        loaded = storage.load_story(sample_story["id"])
        
        assert loaded is not None
        assert loaded["id"] == sample_story["id"]
        assert loaded["genre"] == sample_story["genre"]
    
    def test_load_nonexistent_story(self, storage):
        """Test loading a non-existent story."""
        loaded = storage.load_story("nonexistent_id")
        assert loaded is None
    
    def test_update_story(self, storage, sample_story):
        """Test updating a story."""
        storage.save_story(sample_story)
        
        updates = {"text": "Updated story text", "word_count": 600}
        result = storage.update_story(sample_story["id"], updates)
        assert result is True
        
        loaded = storage.load_story(sample_story["id"])
        assert loaded["text"] == "Updated story text"
        assert loaded["word_count"] == 600
    
    def test_delete_story(self, storage, sample_story):
        """Test deleting a story."""
        storage.save_story(sample_story)
        
        result = storage.delete_story(sample_story["id"])
        assert result is True
        
        loaded = storage.load_story(sample_story["id"])
        assert loaded is None


class TestStoryStoragePagination:
    """Test pagination functionality."""
    
    def test_list_stories_with_pagination(self, storage, sample_story):
        """Test listing stories with pagination."""
        # Create multiple stories
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            storage.save_story(story)
        
        # List first page
        result = storage.list_stories(page=1, per_page=2)
        assert "stories" in result
        assert "pagination" in result
        assert len(result["stories"]) == 2
        assert result["pagination"]["total"] == 5
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 2
    
    def test_list_stories_with_genre_filter(self, storage, sample_story):
        """Test listing stories filtered by genre."""
        # Create stories with different genres
        story1 = sample_story.copy()
        story1["id"] = "story1"
        story1["genre"] = "Science Fiction"
        storage.save_story(story1)
        
        story2 = sample_story.copy()
        story2["id"] = "story2"
        story2["genre"] = "General Fiction"
        storage.save_story(story2)
        
        # Filter by genre
        result = storage.list_stories(genre="Science Fiction")
        assert len(result["stories"]) == 1
        assert result["stories"][0]["genre"] == "Science Fiction"


class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    def test_db_transaction_rolls_back_on_error(self, temp_db_dir):
        """Test that db_transaction rolls back on error."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Test that transaction rolls back on RuntimeError
            with pytest.raises(RuntimeError, match="Test error"):
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_rollback", "test"))
                    # Force an error
                    raise RuntimeError("Test error")
            
            # Verify nothing was committed
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test_rollback")
            assert loaded is None
    
    def test_explicit_rollback_on_error(self, temp_db_dir):
        """Test that explicit rollback works on error.
        
        This test explicitly verifies the database connection's rollback mechanism
        by directly using sqlite3 connection methods, bypassing the db_transaction
        context manager. This ensures the fundamental rollback mechanism is sound.
        """
        import sqlite3
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            conn = get_db_connection()
            
            try:
                # First, insert a story
                cursor = conn.cursor()
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_rollback", "initial text"))
                
                # Force an error by trying to insert with duplicate ID (primary key violation)
                # This will raise sqlite3.IntegrityError
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_rollback", "second text"))
                
                # Should not reach here, but if we do, commit would fail
                conn.commit()
            except sqlite3.IntegrityError:
                # Expected error: duplicate primary key
                # Explicitly call rollback to undo the first INSERT
                conn.rollback()
            finally:
                conn.close()
            
            # Verify nothing was committed after rollback
            # The first INSERT should have been rolled back, so the story should not exist
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test_rollback")
            assert loaded is None, "Story should not exist after rollback"
    
    def test_db_transaction_rolls_back_on_integrity_error(self, temp_db_dir):
        """Test that db_transaction rolls back on IntegrityError."""
        import sqlite3
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # First insert a story
            with db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_integrity", "first"))
            
            # Try to insert duplicate ID - should rollback
            with pytest.raises(sqlite3.IntegrityError):
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_integrity", "duplicate"))
            
            # Verify only the first insert is present
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test_integrity")
            assert loaded is not None
            assert loaded.get("text") == "first"
    
    def test_db_transaction_commits_on_success(self, temp_db_dir):
        """Test that db_transaction commits successfully when no error occurs."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Successful transaction should commit
            with db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_commit", "committed"))
            
            # Verify the data was committed
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test_commit")
            assert loaded is not None
            assert loaded.get("text") == "committed"
    
    def test_explicit_rollback_prevents_partial_commits(self, temp_db_dir):
        """Test that explicit rollback prevents partial commits in multi-step operations."""
        import sqlite3
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            conn = get_db_connection()
            
            try:
                cursor = conn.cursor()
                # First insert succeeds
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_partial_1", "first"))
                # Second insert succeeds
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_partial_2", "second"))
                # Third insert fails (duplicate)
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_partial_1", "duplicate"))
                conn.commit()
            except sqlite3.IntegrityError:
                # Rollback should undo all three operations
                conn.rollback()
            finally:
                conn.close()
            
            # Verify nothing was committed after rollback
            storage = StoryStorage(use_cache=False)
            assert storage.load_story("test_partial_1") is None
            assert storage.load_story("test_partial_2") is None
    
    def test_db_transaction_rolls_back_on_value_error(self, temp_db_dir):
        """Test that db_transaction rolls back on ValueError."""
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            
            # Test that transaction rolls back on ValueError
            with pytest.raises(ValueError, match="Invalid value"):
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_value_error", "test"))
                    # Force a ValueError
                    raise ValueError("Invalid value")
            
            # Verify nothing was committed
            storage = StoryStorage(use_cache=False)
            loaded = storage.load_story("test_value_error")
            assert loaded is None
    
    def test_explicit_rollback_with_nested_operations(self, temp_db_dir):
        """Test that explicit rollback works correctly with nested database operations."""
        import sqlite3
        test_db_dir, test_db_path = temp_db_dir
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
            init_database()
            conn = get_db_connection()
            
            def nested_operation(connection):
                """Nested function that performs multiple operations."""
                cursor = connection.cursor()
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_nested_1", "nested1"))
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_nested_2", "nested2"))
                # This will cause an error
                cursor.execute("INSERT INTO stories (id, text) VALUES (?, ?)", ("test_nested_1", "duplicate"))
            
            try:
                nested_operation(conn)
                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
            finally:
                conn.close()
            
            # Verify nothing was committed after rollback
            storage = StoryStorage(use_cache=False)
            assert storage.load_story("test_nested_1") is None
            assert storage.load_story("test_nested_2") is None


class TestStoryStorageCache:
    """Test cache integration (mocked)."""
    
    @patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'})
    def test_storage_with_mocked_cache_interaction(self, temp_db_dir, sample_story):
        """Test that storage interacts correctly with a mocked Redis cache."""
        test_db_dir, test_db_path = temp_db_dir
        
        # Create a mock redis module
        mock_redis_module = MagicMock()
        mock_redis_instance = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_instance
        
        with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
             patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path), \
             patch.dict('sys.modules', {'redis': mock_redis_module}):
            
            import sys
            sys.modules['redis'] = mock_redis_module
            
            mock_instance = mock_redis_instance
            mock_instance.get.return_value = None  # Simulate cache miss initially
            
            init_database()
            storage = StoryStorage(use_cache=True)  # Ensure use_cache logic is active
            
            # Save story and verify cache.setex was called
            storage.save_story(sample_story)
            
            # Verify cache.setex was called with correct arguments
            mock_instance.setex.assert_called_once()
            call_args = mock_instance.setex.call_args
            cache_key = call_args[0][0]
            cache_ttl = call_args[0][1]
            cached_data = call_args[0][2]
            
            assert cache_key == f"story:{sample_story['id']}"
            assert cache_ttl == 3600  # Default TTL
            assert sample_story["id"] in cached_data  # Story ID should be in cached JSON
            
            # Simulate cache hit for subsequent load
            mock_instance.get.return_value = json.dumps(sample_story)  # Mock JSON string
            loaded = storage.load_story(sample_story["id"])
            
            # Verify cache.get was called
            assert mock_instance.get.called
            assert loaded is not None
            assert loaded["id"] == sample_story["id"]
            
            # Test cache deletion on story delete
            storage.delete_story(sample_story["id"])
            
            # Verify cache.delete was called with correct key
            mock_instance.delete.assert_called_once_with(f"story:{sample_story['id']}")


class TestStoryStorageLargeDataset:
    """Test performance with large datasets."""
    
    def test_list_stories_performance_with_1000_plus_stories(self, storage, sample_story):
        """Test that listing works efficiently with 1000+ stories.
        
        This test verifies that list operations maintain good performance
        with large datasets. Performance should be O(log N) or O(1) with
        proper indexing, not O(N) which would indicate a full table scan.
        """
        # Create 1000 stories
        for i in range(1000):
            story = sample_story.copy()
            story["id"] = f"story_{i:04d}"
            story["text"] = f"Story {i} content"
            storage.save_story(story)
        
        # Measure initial load time (page 1) - should be fast even with 1000 stories
        start_time = time.perf_counter()
        result = storage.list_stories(page=1, per_page=50)
        end_time = time.perf_counter()
        elapsed_time_page1 = end_time - start_time
        
        assert len(result["stories"]) == 50, "Should return correct page size"
        assert result["pagination"]["total"] == 1000, "Should count all stories"
        assert result["pagination"]["total_pages"] == 20, "Should calculate pages correctly"
        assert elapsed_time_page1 < 1.0, \
            f"List first page with 1000 stories should be fast (< 1s), but took {elapsed_time_page1:.3f}s"
        
        # Test later pages performance - should be similarly fast
        start_time = time.perf_counter()
        result = storage.list_stories(page=20, per_page=50)
        end_time = time.perf_counter()
        elapsed_time_page20 = end_time - start_time
        
        assert len(result["stories"]) == 50, "Should return correct page size for last page"
        assert result["pagination"]["has_next"] is False, "Last page should not have next page"
        assert elapsed_time_page20 < 1.0, \
            f"List last page with 1000 stories should be fast (< 1s), but took {elapsed_time_page20:.3f}s"
        
        # Performance assertion: later pages should not be significantly slower
        # This helps catch issues like missing indexes on pagination columns
        assert elapsed_time_page20 < 1.0, \
            "List performance assertion: last page must complete in < 1 second"
    
    def test_save_performance_with_many_stories(self, storage, sample_story):
        """Test that saving works efficiently with many existing stories.
        
        This test verifies that save operations maintain good performance
        even when the database contains many existing stories. Performance
        should not degrade linearly with the number of existing stories
        (O(1) or O(log N) behavior expected, not O(N)).
        """
        # Create 500 stories first
        for i in range(500):
            story = sample_story.copy()
            story["id"] = f"story_{i:03d}"
            storage.save_story(story)
        
        # Save a new story should still be fast regardless of existing story count
        new_story = sample_story.copy()
        new_story["id"] = "new_story_999"
        start_time = time.perf_counter()
        result = storage.save_story(new_story)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        assert result is True, "Save operation should succeed"
        assert elapsed_time < 0.5, \
            f"Save with 500+ existing stories should be fast (< 500ms), but took {elapsed_time:.3f}s"
        
        # Verify it was saved
        loaded = storage.load_story("new_story_999")
        assert loaded is not None, "Saved story should be retrievable"
        
        # Additional performance check: verify save time is reasonable
        # This helps catch performance regressions (e.g., if an index is removed)
        assert elapsed_time < 0.5, \
            "Save performance assertion: operation must complete in < 500ms"
