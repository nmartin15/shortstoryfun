"""
Performance tests for the Short Story Pipeline.

Tests cover:
- Concurrent request handling
- Large dataset performance
- Database query performance
- Memory usage
- Response time benchmarks
- Basic utility function performance (word counting, validation)
- Pipeline stage performance (with mocked LLM)
"""

import pytest
import time
import threading
import concurrent.futures
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.shortstory.utils.db_storage import StoryStorage, init_database
from src.shortstory.utils.repository import DatabaseStoryRepository
from tests.conftest import check_optional_dependency


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


@pytest.fixture
def repository(temp_db_dir):
    """Create a DatabaseStoryRepository instance for testing."""
    test_db_dir, test_db_path = temp_db_dir
    init_database()
    yield DatabaseStoryRepository(use_cache=False)


class TestConcurrentRequests:
    """Test concurrent request handling."""
    
    def test_concurrent_story_saves(self, storage):
        """Test that multiple concurrent story saves work correctly."""
        num_threads = 10
        stories_per_thread = 5
        
        def save_stories(thread_id):
            """Save stories for a thread."""
            saved_ids = []
            for i in range(stories_per_thread):
                story_id = f"story_thread_{thread_id}_{i}"
                story = {
                    "id": story_id,
                    "genre": "General Fiction",
                    "text": f"Story content from thread {thread_id}, story {i}",
                    "word_count": 100
                }
                try:
                    result = storage.save_story(story)
                    if result:
                        saved_ids.append(story_id)
                except Exception as e:
                    print(f"Thread {thread_id} error saving {story_id}: {e}")
            return saved_ids
        
        # Run concurrent saves
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(save_stories, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        # Verify all stories were saved
        all_saved_ids = [story_id for thread_results in results for story_id in thread_results]
        assert len(all_saved_ids) == num_threads * stories_per_thread, \
            f"Expected {num_threads * stories_per_thread} stories, got {len(all_saved_ids)}"
        
        # Verify no duplicates
        assert len(all_saved_ids) == len(set(all_saved_ids)), "Duplicate story IDs found"
        
        # Performance assertion: should complete in reasonable time
        assert elapsed_time < 5.0, \
            f"Concurrent saves should complete in < 5s, took {elapsed_time:.2f}s"
        
        # Verify all stories can be loaded
        for story_id in all_saved_ids:
            loaded = storage.load_story(story_id)
            assert loaded is not None, f"Story {story_id} should be loadable"
    
    def test_concurrent_story_loads(self, storage):
        """Test that multiple concurrent story loads work correctly."""
        # First, create test stories
        num_stories = 20
        story_ids = []
        for i in range(num_stories):
            story_id = f"concurrent_load_{i}"
            story = {
                "id": story_id,
                "genre": "General Fiction",
                "text": f"Story content {i}",
                "word_count": 100
            }
            storage.save_story(story)
            story_ids.append(story_id)
        
        # Concurrent loads
        num_threads = 10
        
        def load_stories():
            """Load stories concurrently."""
            loaded_count = 0
            for story_id in story_ids:
                try:
                    loaded = storage.load_story(story_id)
                    if loaded is not None:
                        loaded_count += 1
                except Exception as e:
                    print(f"Error loading {story_id}: {e}")
            return loaded_count
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(load_stories) for _ in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        # All threads should have loaded all stories
        for result in results:
            assert result == num_stories, \
                f"Each thread should load {num_stories} stories, got {result}"
        
        # Performance assertion
        assert elapsed_time < 3.0, \
            f"Concurrent loads should complete in < 3s, took {elapsed_time:.2f}s"
    
    def test_concurrent_updates(self, storage):
        """Test that concurrent updates are handled correctly."""
        # Create a test story
        story_id = "concurrent_update_test"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "Initial text",
            "word_count": 100
        }
        storage.save_story(story)
        
        num_threads = 5
        
        def update_story(thread_id):
            """Update story from a thread."""
            updates = {
                "text": f"Updated by thread {thread_id}",
                "word_count": 100 + thread_id
            }
            try:
                return storage.update_story(story_id, updates)
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
                return False
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_story, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        # All updates should succeed
        assert all(results), "All concurrent updates should succeed"
        
        # Performance assertion
        assert elapsed_time < 2.0, \
            f"Concurrent updates should complete in < 2s, took {elapsed_time:.2f}s"
        
        # Verify final state (one of the updates should be present)
        loaded = storage.load_story(story_id)
        assert loaded is not None
        assert "Updated by thread" in loaded["text"]


class TestLargeDatasetPerformance:
    """Test performance with large datasets."""
    
    def test_list_performance_with_many_stories(self, storage):
        """Test that listing stories performs well with many stories."""
        num_stories = 500
        
        # Create many stories
        print(f"Creating {num_stories} stories...")
        start_create = time.perf_counter()
        for i in range(num_stories):
            story = {
                "id": f"perf_test_{i:04d}",
                "genre": "General Fiction" if i % 2 == 0 else "Science Fiction",
                "text": f"Story content {i}",
                "word_count": 100 + (i % 1000)
            }
            storage.save_story(story)
        end_create = time.perf_counter()
        create_time = end_create - start_create
        
        print(f"Created {num_stories} stories in {create_time:.2f}s")
        
        # Test list performance
        start_list = time.perf_counter()
        result = storage.list_stories(page=1, per_page=50)
        end_list = time.perf_counter()
        list_time = end_list - start_list
        
        assert len(result["stories"]) == 50
        assert result["pagination"]["total"] == num_stories
        
        # Performance assertions
        assert list_time < 1.0, \
            f"List with {num_stories} stories should complete in < 1s, took {list_time:.3f}s"
        
        # Test pagination performance (later pages)
        start_page = time.perf_counter()
        result = storage.list_stories(page=10, per_page=50)
        end_page = time.perf_counter()
        page_time = end_page - start_page
        
        assert len(result["stories"]) == 50
        assert result["pagination"]["page"] == 10
        
        # Later pages should be similarly fast
        assert page_time < 1.0, \
            f"Page 10 with {num_stories} stories should complete in < 1s, took {page_time:.3f}s"
    
    def test_count_performance_with_many_stories(self, storage):
        """Test that counting stories performs well with many stories."""
        num_stories = 1000
        
        # Create many stories
        for i in range(num_stories):
            story = {
                "id": f"count_test_{i:04d}",
                "genre": "General Fiction" if i % 3 == 0 else "Science Fiction",
                "text": f"Story content {i}",
                "word_count": 100
            }
            storage.save_story(story)
        
        # Test count performance
        start_time = time.perf_counter()
        total_count = storage.count_stories()
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        assert total_count == num_stories
        
        # Performance assertion: count should be fast even with many stories
        assert elapsed_time < 0.5, \
            f"Count with {num_stories} stories should complete in < 0.5s, took {elapsed_time:.3f}s"
        
        # Test genre-filtered count
        start_time = time.perf_counter()
        genre_count = storage.count_stories(genre="General Fiction")
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        # Should be approximately 1/3 of total (every 3rd story)
        expected_count = num_stories // 3
        assert abs(genre_count - expected_count) <= 1, \
            f"Expected ~{expected_count} General Fiction stories, got {genre_count}"
        
        # Genre-filtered count should also be fast
        assert elapsed_time < 0.5, \
            f"Genre count with {num_stories} stories should complete in < 0.5s, took {elapsed_time:.3f}s"
    
    def test_large_story_content(self, storage):
        """Test performance with large story content."""
        # Create story with large text content
        large_text = "This is a test sentence. " * 10000  # ~250KB of text
        story = {
            "id": "large_content_test",
            "genre": "General Fiction",
            "text": large_text,
            "word_count": len(large_text.split())
        }
        
        # Test save performance
        start_time = time.perf_counter()
        result = storage.save_story(story)
        end_time = time.perf_counter()
        save_time = end_time - start_time
        
        assert result is True
        
        # Save should complete in reasonable time
        assert save_time < 2.0, \
            f"Save large story should complete in < 2s, took {save_time:.3f}s"
        
        # Test load performance
        start_time = time.perf_counter()
        loaded = storage.load_story("large_content_test")
        end_time = time.perf_counter()
        load_time = end_time - start_time
        
        assert loaded is not None
        assert len(loaded["text"]) == len(large_text)
        
        # Load should complete in reasonable time
        assert load_time < 1.0, \
            f"Load large story should complete in < 1s, took {load_time:.3f}s"


class TestDatabaseQueryPerformance:
    """Test database query performance."""
    
    def test_indexed_queries_performance(self, storage):
        """Test that indexed queries (genre, updated_at) are fast."""
        num_stories = 200
        
        # Create stories with different genres and timestamps
        for i in range(num_stories):
            story = {
                "id": f"index_test_{i:04d}",
                "genre": "Horror" if i % 4 == 0 else "Romance" if i % 4 == 1 else "Science Fiction",
                "text": f"Story {i}",
                "word_count": 100
            }
            storage.save_story(story)
            # Small delay to ensure different timestamps
            time.sleep(0.001)
        
        # Test genre-filtered query (uses index)
        start_time = time.perf_counter()
        result = storage.list_stories(genre="Horror", page=1, per_page=50)
        end_time = time.perf_counter()
        query_time = end_time - start_time
        
        assert len(result["stories"]) <= 50
        # Should be approximately 1/4 of stories
        assert result["pagination"]["total"] >= num_stories // 4 - 5
        
        # Indexed query should be fast
        assert query_time < 0.5, \
            f"Indexed genre query should complete in < 0.5s, took {query_time:.3f}s"
    
    def test_pagination_performance(self, storage):
        """Test that pagination queries are efficient."""
        num_stories = 300
        
        # Create stories
        for i in range(num_stories):
            story = {
                "id": f"pagination_test_{i:04d}",
                "genre": "General Fiction",
                "text": f"Story {i}",
                "word_count": 100
            }
            storage.save_story(story)
        
        # Test first page
        start_time = time.perf_counter()
        result1 = storage.list_stories(page=1, per_page=50)
        end_time = time.perf_counter()
        page1_time = end_time - start_time
        
        # Test middle page
        start_time = time.perf_counter()
        result2 = storage.list_stories(page=5, per_page=50)
        end_time = time.perf_counter()
        page5_time = end_time - start_time
        
        # Test last page
        start_time = time.perf_counter()
        result3 = storage.list_stories(page=6, per_page=50)
        end_time = time.perf_counter()
        page6_time = end_time - start_time
        
        # All pages should be similarly fast (pagination should be efficient)
        assert page1_time < 0.5, f"Page 1 should be fast, took {page1_time:.3f}s"
        assert page5_time < 0.5, f"Page 5 should be fast, took {page5_time:.3f}s"
        assert page6_time < 0.5, f"Page 6 should be fast, took {page6_time:.3f}s"
        
        # Later pages shouldn't be significantly slower
        assert page6_time < page1_time * 2, \
            "Last page shouldn't be more than 2x slower than first page"


class TestResponseTimeBenchmarks:
    """Test response time benchmarks."""
    
    def test_single_story_save_time(self, storage):
        """Benchmark single story save time."""
        story = {
            "id": "benchmark_save",
            "genre": "General Fiction",
            "text": "Test story content",
            "word_count": 100
        }
        
        start_time = time.perf_counter()
        result = storage.save_story(story)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        assert result is True
        # Single save should be very fast
        assert elapsed_time < 0.1, \
            f"Single story save should complete in < 100ms, took {elapsed_time*1000:.2f}ms"
    
    def test_single_story_load_time(self, storage):
        """Benchmark single story load time."""
        # Create story first
        story = {
            "id": "benchmark_load",
            "genre": "General Fiction",
            "text": "Test story content",
            "word_count": 100
        }
        storage.save_story(story)
        
        start_time = time.perf_counter()
        loaded = storage.load_story("benchmark_load")
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        assert loaded is not None
        # Single load should be very fast
        assert elapsed_time < 0.1, \
            f"Single story load should complete in < 100ms, took {elapsed_time*1000:.2f}ms"
    
    def test_repository_list_time(self, repository):
        """Benchmark repository list operation."""
        # Create some test stories
        for i in range(10):
            story = {
                "id": f"repo_test_{i}",
                "genre": "General Fiction",
                "text": f"Story {i}",
                "word_count": 100
            }
            repository.save(story)
        
        start_time = time.perf_counter()
        result = repository.list(page=1, per_page=10)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        
        assert "stories" in result
        # Repository list should be fast
        assert elapsed_time < 0.2, \
            f"Repository list should complete in < 200ms, took {elapsed_time*1000:.2f}ms"


class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_memory_efficient_pagination(self, storage):
        """Test that pagination doesn't load all stories into memory."""
        # Create many stories
        num_stories = 1000
        for i in range(num_stories):
            story = {
                "id": f"memory_test_{i:04d}",
                "genre": "General Fiction",
                "text": f"Story content {i}",
                "word_count": 100
            }
            storage.save_story(story)
        
        # List with pagination - should only load one page
        result = storage.list_stories(page=1, per_page=50)
        
        # Should only return 50 stories, not all 1000
        assert len(result["stories"]) == 50
        assert result["pagination"]["total"] == num_stories
        
        # Verify we can access other pages without loading everything
        result2 = storage.list_stories(page=20, per_page=50)
        assert len(result2["stories"]) == 50
        assert result2["pagination"]["page"] == 20


class TestBasicUtilityPerformance:
    """Basic performance tests for core utility functions."""
    
    def test_word_count_small_text(self):
        """Test word counting performance on small text."""
        from src.shortstory.utils.word_count import WordCountValidator
        
        validator = WordCountValidator()
        text = "This is a test sentence with ten words total for performance testing."
        
        start_time = time.perf_counter()
        for _ in range(1000):
            count = validator.count_words(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert count == 12
        # Should be very fast - 1000 operations in < 0.1s
        assert elapsed_time < 0.1, \
            f"Word counting 1000 small texts should complete in < 100ms, took {elapsed_time*1000:.2f}ms"
    
    def test_word_count_medium_text(self):
        """Test word counting performance on medium text (~1000 words)."""
        from src.shortstory.utils.word_count import WordCountValidator
        
        validator = WordCountValidator()
        # Create ~1000 word text
        text = "word " * 1000
        
        start_time = time.perf_counter()
        for _ in range(100):
            count = validator.count_words(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert count == 1000
        # Should be fast - 100 operations in < 0.5s
        assert elapsed_time < 0.5, \
            f"Word counting 100 medium texts should complete in < 500ms, took {elapsed_time*1000:.2f}ms"
    
    def test_word_count_large_text(self):
        """Test word counting performance on large text (~5000 words)."""
        from src.shortstory.utils.word_count import WordCountValidator
        
        validator = WordCountValidator()
        # Create ~5000 word text
        text = "word " * 5000
        
        start_time = time.perf_counter()
        for _ in range(10):
            count = validator.count_words(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert count == 5000
        # Should complete in reasonable time - 10 operations in < 0.2s
        assert elapsed_time < 0.2, \
            f"Word counting 10 large texts should complete in < 200ms, took {elapsed_time*1000:.2f}ms"
    
    def test_distinctiveness_check_small_text(self):
        """Test distinctiveness check performance on small text."""
        from src.shortstory.utils.validation import check_distinctiveness
        
        text = "This is a test story with no clichés or generic patterns."
        
        start_time = time.perf_counter()
        for _ in range(100):
            result = check_distinctiveness(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert result["distinctiveness_score"] > 0
        # Should be fast - 100 operations in < 0.5s
        assert elapsed_time < 0.5, \
            f"Distinctiveness check 100 small texts should complete in < 500ms, took {elapsed_time*1000:.2f}ms"
    
    def test_distinctiveness_check_with_cliches(self):
        """Test distinctiveness check performance with clichés present."""
        from src.shortstory.utils.validation import check_distinctiveness
        
        text = "It was a dark and stormy night. Little did they know that time seemed to stand still."
        
        start_time = time.perf_counter()
        for _ in range(50):
            result = check_distinctiveness(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert result["has_cliches"] is True
        assert result["cliche_count"] > 0
        # Should be fast - 50 operations in < 0.3s
        assert elapsed_time < 0.3, \
            f"Distinctiveness check 50 texts with clichés should complete in < 300ms, took {elapsed_time*1000:.2f}ms"
    
    def test_detect_cliches_performance(self):
        """Test cliché detection performance."""
        from src.shortstory.utils.validation import detect_cliches
        
        text = "Once upon a time, it was a dark and stormy night. Little did they know what was coming."
        
        start_time = time.perf_counter()
        for _ in range(200):
            result = detect_cliches(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert result["has_cliches"] is True
        # Should be very fast - 200 operations in < 0.2s
        assert elapsed_time < 0.2, \
            f"Cliché detection 200 texts should complete in < 200ms, took {elapsed_time*1000:.2f}ms"
    
    def test_detect_generic_patterns_performance(self):
        """Test generic pattern detection performance."""
        from src.shortstory.utils.validation import detect_generic_patterns_from_text
        
        text = "It was very really quite something. She knew he realized it dawned on them suddenly."
        
        start_time = time.perf_counter()
        for _ in range(200):
            result = detect_generic_patterns_from_text(text)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert len(result) > 0
        # Should be fast - 200 operations in < 0.3s
        assert elapsed_time < 0.3, \
            f"Generic pattern detection 200 texts should complete in < 300ms, took {elapsed_time*1000:.2f}ms"
    
    def test_validate_premise_performance(self):
        """Test premise validation performance."""
        from src.shortstory.utils.validation import validate_premise
        
        idea = "A lighthouse keeper collects lost voices in glass jars"
        character = {"name": "Mara", "description": "A quiet keeper with an unusual collection"}
        theme = "What happens to the stories we never tell?"
        
        start_time = time.perf_counter()
        for _ in range(100):
            result = validate_premise(idea, character, theme)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert result["is_valid"] is True
        # Should be fast - 100 operations in < 0.5s
        assert elapsed_time < 0.5, \
            f"Premise validation 100 times should complete in < 500ms, took {elapsed_time*1000:.2f}ms"


class TestPipelineStagePerformance:
    """Basic performance tests for pipeline stages (with mocked LLM)."""
    
    def test_capture_premise_performance(self, basic_pipeline):
        """Test premise capture performance."""
        idea = "A lighthouse keeper collects lost voices in glass jars"
        character = {"name": "Mara", "description": "A quiet keeper with an unusual collection"}
        theme = "What happens to the stories we never tell?"
        
        start_time = time.perf_counter()
        for _ in range(50):
            premise = basic_pipeline.capture_premise(idea, character, theme, validate=False)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert premise is not None
        # Should be fast - 50 operations in < 0.5s
        assert elapsed_time < 0.5, \
            f"Premise capture 50 times should complete in < 500ms, took {elapsed_time*1000:.2f}ms"
    
    def test_generate_outline_performance(self, pipeline_with_premise, mock_llm_client):
        """Test outline generation performance with mocked LLM."""
        pipeline = pipeline_with_premise
        
        with patch('src.shortstory.providers.factory.get_default_provider', return_value=mock_llm_client):
            start_time = time.perf_counter()
            outline = pipeline.generate_outline(use_llm=True)
            end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert outline is not None
        # With mocked LLM, should be fast - < 0.1s
        assert elapsed_time < 0.1, \
            f"Outline generation with mocked LLM should complete in < 100ms, took {elapsed_time*1000:.2f}ms"
    
    def test_scaffold_performance(self, pipeline_with_premise, mock_llm_client):
        """Test scaffold generation performance with mocked LLM."""
        pipeline = pipeline_with_premise
        
        # Generate outline first with mocked LLM
        with patch('src.shortstory.providers.factory.get_default_provider', return_value=mock_llm_client):
            pipeline.generate_outline(use_llm=True)
            start_time = time.perf_counter()
            scaffold = pipeline.scaffold(use_llm=True)
            end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert scaffold is not None
        # With mocked LLM, should be fast - < 0.1s
        assert elapsed_time < 0.1, \
            f"Scaffold generation with mocked LLM should complete in < 100ms, took {elapsed_time*1000:.2f}ms"
    
    def test_draft_template_performance(self, pipeline_with_premise, mock_llm_client):
        """Test template draft generation performance (no LLM)."""
        pipeline = pipeline_with_premise
        
        # Set up pipeline stages without LLM
        with patch('src.shortstory.providers.factory.get_default_provider', return_value=mock_llm_client):
            pipeline.generate_outline(use_llm=True)
            pipeline.scaffold(use_llm=True)
        
        start_time = time.perf_counter()
        draft = pipeline.draft(use_llm=False)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert draft is not None
        assert draft.get("text") is not None
        # Template generation should be fast - < 0.5s
        assert elapsed_time < 0.5, \
            f"Template draft generation should complete in < 500ms, took {elapsed_time*1000:.2f}ms"
    
    def test_revise_rule_based_performance(self, pipeline_with_premise, mock_llm_client):
        """Test rule-based revision performance (no LLM)."""
        pipeline = pipeline_with_premise
        
        # Set up pipeline stages without LLM
        with patch('src.shortstory.providers.factory.get_default_provider', return_value=mock_llm_client):
            pipeline.generate_outline(use_llm=True)
            pipeline.scaffold(use_llm=True)
        
        # Generate draft first
        draft = pipeline.draft(use_llm=False)
        
        start_time = time.perf_counter()
        revised = pipeline.revise(use_llm=False)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        assert revised is not None
        assert revised.get("text") is not None
        # Rule-based revision should be fast - < 0.3s
        assert elapsed_time < 0.3, \
            f"Rule-based revision should complete in < 300ms, took {elapsed_time*1000:.2f}ms"
    
    def test_word_count_validation_performance(self):
        """Test word count validation performance on various text sizes."""
        from src.shortstory.utils.word_count import WordCountValidator
        
        validator = WordCountValidator(max_words=7500)
        
        # Test small text
        small_text = "word " * 100
        start_time = time.perf_counter()
        for _ in range(1000):
            word_count, is_valid = validator.validate(small_text, raise_error=False)
        end_time = time.perf_counter()
        small_time = end_time - start_time
        
        # Test medium text
        medium_text = "word " * 3000
        start_time = time.perf_counter()
        for _ in range(100):
            word_count, is_valid = validator.validate(medium_text, raise_error=False)
        end_time = time.perf_counter()
        medium_time = end_time - start_time
        
        # Test large text
        large_text = "word " * 7000
        start_time = time.perf_counter()
        for _ in range(10):
            word_count, is_valid = validator.validate(large_text, raise_error=False)
        end_time = time.perf_counter()
        large_time = end_time - start_time
        
        assert small_time < 0.2, \
            f"Word validation 1000 small texts should complete in < 200ms, took {small_time*1000:.2f}ms"
        assert medium_time < 0.3, \
            f"Word validation 100 medium texts should complete in < 300ms, took {medium_time*1000:.2f}ms"
        assert large_time < 0.2, \
            f"Word validation 10 large texts should complete in < 200ms, took {large_time*1000:.2f}ms"

