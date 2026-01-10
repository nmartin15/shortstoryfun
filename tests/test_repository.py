"""
Tests for story repository implementations.
"""

import pytest
from unittest.mock import patch
import tempfile
import shutil
from pathlib import Path

from src.shortstory.utils.repository import FileStoryRepository


@pytest.fixture
def temp_stories_dir():
    """Create a temporary directory for story files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


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
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


class TestFileRepository:
    """Test suite for FileStoryRepository."""
    
    @pytest.fixture(autouse=True)
    def isolated_repo(self, temp_stories_dir):
        """Create an isolated repository for each test."""
        # Convert string path to Path object for proper patching
        storage_path = Path(temp_stories_dir)
        with patch('src.shortstory.utils.storage.STORAGE_DIR', storage_path):
            repo = FileStoryRepository()
            yield repo
            # Cleanup: repository uses temp directory which is cleaned up by fixture
    
    def test_list_with_pagination(self, isolated_repo, sample_story):
        """Test listing stories with pagination."""
        repo = isolated_repo
        
        # Create multiple stories
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # List first page
        result = repo.list(page=1, per_page=2)
        assert "stories" in result
        assert "pagination" in result
        assert len(result["stories"]) == 2
        assert result["pagination"]["total"] == 5
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 2
        assert result["pagination"]["total_pages"] == 3  # 5 stories / 2 per page = 3 pages
        
        # List second page
        result_page2 = repo.list(page=2, per_page=2)
        assert len(result_page2["stories"]) == 2
        assert result_page2["pagination"]["page"] == 2
        assert result_page2["pagination"]["total"] == 5
        
        # List third page (last element)
        result_page3 = repo.list(page=3, per_page=2)
        assert len(result_page3["stories"]) == 1
        assert result_page3["pagination"]["page"] == 3
        assert result_page3["pagination"]["total"] == 5
    
    def test_list_pagination_edge_cases(self, isolated_repo, sample_story):
        """Test pagination edge cases: empty results, page beyond total, zero per_page."""
        repo = isolated_repo
        
        # Test with no stories
        result_empty = repo.list(page=1, per_page=10)
        assert "stories" in result_empty
        assert "pagination" in result_empty
        assert len(result_empty["stories"]) == 0
        assert result_empty["pagination"]["total"] == 0
        assert result_empty["pagination"]["page"] == 1
        
        # Create some stories
        for i in range(3):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # Test page beyond available pages (should return empty or last page)
        result_beyond = repo.list(page=10, per_page=2)
        assert "stories" in result_beyond
        assert "pagination" in result_beyond
        # Should either return empty or clamp to last page
        assert result_beyond["pagination"]["page"] >= 1
        
        # Test with per_page larger than total
        result_large_page = repo.list(page=1, per_page=100)
        assert len(result_large_page["stories"]) == 3
        assert result_large_page["pagination"]["total"] == 3
        assert result_large_page["pagination"]["total_pages"] == 1
    
    def test_count_with_genre_filter(self, isolated_repo, sample_story):
        """Test counting stories with genre filter for files."""
        repo = isolated_repo
        
        # Create stories with different genres
        story1 = sample_story.copy()
        story1["id"] = "story1"
        story1["genre"] = "Science Fiction"
        repo.save(story1)
        
        story2 = sample_story.copy()
        story2["id"] = "story2"
        story2["genre"] = "General Fiction"
        repo.save(story2)
        
        story3 = sample_story.copy()
        story3["id"] = "story3"
        story3["genre"] = "Science Fiction"
        repo.save(story3)
        
        # Test counts
        assert repo.count() == 3  # Total count
        assert repo.count(genre="Science Fiction") == 2
        assert repo.count(genre="General Fiction") == 1
        assert repo.count(genre="Fantasy") == 0
    
    def test_list_with_genre_filter(self, isolated_repo, sample_story):
        """Test listing stories filtered by genre from files."""
        repo = isolated_repo
        
        # Create stories with different genres
        story1 = sample_story.copy()
        story1["id"] = "story1"
        story1["genre"] = "Science Fiction"
        repo.save(story1)
        
        story2 = sample_story.copy()
        story2["id"] = "story2"
        story2["genre"] = "General Fiction"
        repo.save(story2)
        
        # List only Science Fiction
        result = repo.list(genre="Science Fiction")
        assert len(result["stories"]) == 1
        assert result["stories"][0]["genre"] == "Science Fiction"
        assert result["stories"][0]["id"] == "story1"
        
        # List only General Fiction
        result_gf = repo.list(genre="General Fiction")
        assert len(result_gf["stories"]) == 1
        assert result_gf["stories"][0]["genre"] == "General Fiction"
        assert result_gf["stories"][0]["id"] == "story2"
        
        # List non-existent genre
        result_none = repo.list(genre="Fantasy")
        assert len(result_none["stories"]) == 0
        assert result_none["pagination"]["total"] == 0
    
    def test_list_with_genre_filter_and_pagination(self, isolated_repo, sample_story):
        """Test listing stories with both genre filter and pagination."""
        repo = isolated_repo
        
        # Create multiple stories with different genres
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            story["genre"] = "Science Fiction" if i % 2 == 0 else "General Fiction"
            repo.save(story)
        
        # List Science Fiction with pagination
        result = repo.list(genre="Science Fiction", page=1, per_page=1)
        assert len(result["stories"]) == 1
        assert result["stories"][0]["genre"] == "Science Fiction"
        assert result["pagination"]["total"] == 3  # 3 Science Fiction stories (0, 2, 4)
        assert result["pagination"]["page"] == 1
    
    def test_list_pagination_with_negative_page(self, isolated_repo, sample_story):
        """Test pagination handles negative page numbers correctly."""
        repo = isolated_repo
        
        # Create some stories
        for i in range(3):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # Negative page should be clamped to 1
        result = repo.list(page=-1, per_page=2)
        assert result["pagination"]["page"] == 1
        assert len(result["stories"]) == 2
    
    def test_list_pagination_with_zero_per_page(self, isolated_repo, sample_story):
        """Test pagination handles zero per_page correctly."""
        repo = isolated_repo
        
        # Create some stories
        for i in range(3):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # Zero per_page should be clamped to minimum 1
        result = repo.list(page=1, per_page=0)
        assert result["pagination"]["per_page"] >= 1
        assert len(result["stories"]) >= 1
    
    def test_list_pagination_with_very_large_page(self, isolated_repo, sample_story):
        """Test pagination handles very large page numbers correctly."""
        repo = isolated_repo
        
        # Create some stories
        for i in range(3):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # Very large page number should return empty results or last page
        result = repo.list(page=1000, per_page=2)
        assert result["pagination"]["page"] >= 1
        # Should either be empty or on the last valid page
        assert len(result["stories"]) <= 2
    
    def test_list_pagination_with_very_large_per_page(self, isolated_repo, sample_story):
        """Test pagination handles very large per_page values correctly."""
        repo = isolated_repo
        
        # Create some stories
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            repo.save(story)
        
        # Very large per_page should be clamped to maximum 100
        result = repo.list(page=1, per_page=10000)
        assert result["pagination"]["per_page"] <= 100
        assert len(result["stories"]) <= 5  # Should return all stories
    
    def test_list_pagination_with_genre_filter_edge_cases(self, isolated_repo, sample_story):
        """Test pagination edge cases when combined with genre filtering."""
        repo = isolated_repo
        
        # Create stories with different genres
        for i in range(10):
            story = sample_story.copy()
            story["id"] = f"story_{i}"
            story["genre"] = "Science Fiction" if i % 2 == 0 else "General Fiction"
            repo.save(story)
        
        # Test pagination with genre filter - page beyond available
        result = repo.list(genre="Science Fiction", page=10, per_page=2)
        assert result["pagination"]["total"] == 5  # 5 Science Fiction stories
        assert result["pagination"]["page"] >= 1
        # Should be on last page or empty
        
        # Test pagination with genre filter - exact page count
        result = repo.list(genre="Science Fiction", page=3, per_page=2)
        assert result["pagination"]["total"] == 5
        assert result["pagination"]["page"] == 3
        assert len(result["stories"]) == 1  # Last page with 1 story
    
    def test_genre_filter_case_sensitivity(self, isolated_repo, sample_story):
        """Test that genre filtering is case-sensitive."""
        repo = isolated_repo
        
        # Create story with specific genre
        story = sample_story.copy()
        story["id"] = "story1"
        story["genre"] = "Science Fiction"
        repo.save(story)
        
        # Case-sensitive matching
        result_exact = repo.list(genre="Science Fiction")
        assert len(result_exact["stories"]) == 1
        
        # Case mismatch should return empty
        result_lower = repo.list(genre="science fiction")
        assert len(result_lower["stories"]) == 0
        
        result_upper = repo.list(genre="SCIENCE FICTION")
        assert len(result_upper["stories"]) == 0
    
    def test_genre_filter_with_none_genre(self, isolated_repo, sample_story):
        """Test genre filtering when genre is None (should return all stories)."""
        repo = isolated_repo
        
        # Create stories with and without genre
        story1 = sample_story.copy()
        story1["id"] = "story1"
        story1["genre"] = "Science Fiction"
        repo.save(story1)
        
        story2 = sample_story.copy()
        story2["id"] = "story2"
        story2["genre"] = "General Fiction"
        repo.save(story2)
        
        story3 = sample_story.copy()
        story3["id"] = "story3"
        story3.pop("genre", None)  # Remove genre
        repo.save(story3)
        
        # None genre should return all stories
        result_all = repo.list(genre=None)
        assert len(result_all["stories"]) == 3
        
        # Explicit genre should filter
        result_sf = repo.list(genre="Science Fiction")
        assert len(result_sf["stories"]) == 1
    
    def test_genre_filter_with_empty_string(self, isolated_repo, sample_story):
        """Test genre filtering with empty string."""
        repo = isolated_repo
        
        # Create story with empty genre
        story1 = sample_story.copy()
        story1["id"] = "story1"
        story1["genre"] = ""
        repo.save(story1)
        
        # Create story with normal genre
        story2 = sample_story.copy()
        story2["id"] = "story2"
        story2["genre"] = "Science Fiction"
        repo.save(story2)
        
        # Empty string filter behavior: may return all or only empty genre stories
        # depending on implementation (empty string might be treated as no filter)
        result_empty = repo.list(genre="")
        # Should return at least the story with empty genre
        empty_genre_stories = [s for s in result_empty["stories"] if s.get("genre") == ""]
        assert len(empty_genre_stories) >= 1
        
        # Normal genre should still work
        result_sf = repo.list(genre="Science Fiction")
        assert len(result_sf["stories"]) == 1
        assert result_sf["stories"][0]["genre"] == "Science Fiction"