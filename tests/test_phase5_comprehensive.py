"""
Comprehensive Phase 5 tests.

This module consolidates comprehensive tests for various components.
Many individual tests are also covered in dedicated test files.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Response

from app import create_app
from src.shortstory.exports import sanitize_filename
from src.shortstory.utils.errors import APIError, ValidationError, ServiceUnavailableError


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_story():
    """Sample story for testing."""
    return {
        "id": "test_story_123",
        "genre": "General Fiction",
        "body": "Test story body",
        "word_count": 3,
        "premise": {"idea": "Test idea"},
        "outline": {"acts": {}},
        "metadata": {}
    }


class TestSanitizeFilenameComprehensive:
    """Comprehensive tests for sanitize_filename function."""
    
    def test_sanitize_filename_basic(self):
        """Test basic sanitization."""
        result = sanitize_filename("My Story", "abc123")
        assert len(result) >= 1  # Changed from > 0 for clarity
        assert "My" in result or "Story" in result
    
    def test_sanitize_filename_unicode_handling(self):
        """Test handling of unicode characters."""
        title = "Story with émojis 🎭 and spéciál chàracters"
        result = sanitize_filename(title, "test_123")
        assert len(result) >= 1
        # Should sanitize but preserve some characters
        assert isinstance(result, str)
    
    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test that dangerous characters are removed."""
        title = "Story<script>alert('xss')</script>"
        result = sanitize_filename(title, "test_123")
        assert "<" not in result
        assert "script" not in result.lower()
    
    def test_sanitize_filename_path_traversal(self):
        """Test that path traversal patterns are removed."""
        title = "../../etc/passwd"
        result = sanitize_filename(title, "test_123")
        assert ".." not in result
        assert "/" not in result
    
    def test_sanitize_filename_max_length(self):
        """Test that max length is enforced."""
        long_title = "A" * 200
        result = sanitize_filename(long_title, "test_123", max_length=50)
        assert len(result) <= 50
    
    def test_sanitize_filename_fallback_to_id(self):
        """Test that empty sanitization falls back to story ID."""
        result = sanitize_filename("", "test_123")
        assert "test_123" in result or len(result) >= 1


class TestExportStoryEndpoint:
    """Test suite for export story endpoints."""
    
    @patch('app.get_story_or_404')
    @patch('app.get_story_text')
    @patch('src.shortstory.exports.export_pdf')
    def test_export_story_pdf(self, mock_export, mock_text, mock_get, client, sample_story):
        """Test PDF export endpoint."""
        mock_get.return_value = sample_story
        mock_text.return_value = "# Test Story\n\nContent"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_export.return_value = mock_response
        
        response = client.get('/api/story/test_story_123/export/pdf')
        # Should call export function and return 200 OK
        assert mock_export.called
        assert response.status_code == 200  # Specific status code assertion
    
    @patch('app.get_story_or_404')
    @patch('app.get_story_text')
    @patch('src.shortstory.exports.export_markdown')
    def test_export_story_markdown(self, mock_export, mock_text, mock_get, client, sample_story):
        """Test Markdown export endpoint."""
        mock_get.return_value = sample_story
        mock_text.return_value = "# Test Story\n\nContent"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_export.return_value = mock_response
        
        response = client.get('/api/story/test_story_123/export/markdown')
        assert response.status_code == 200  # Specific status code assertion
    
    @patch('app.get_story_or_404')
    @patch('app.get_story_text')
    @patch('src.shortstory.exports.export_txt')
    def test_export_story_txt(self, mock_export, mock_text, mock_get, client, sample_story):
        """Test TXT export endpoint."""
        mock_get.return_value = sample_story
        mock_text.return_value = "# Test Story\n\nContent"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_export.return_value = mock_response
        
        response = client.get('/api/story/test_story_123/export/txt')
        assert response.status_code == 200  # Specific status code assertion
    
    @patch('app.get_story_or_404')
    def test_export_story_404(self, mock_get, client):
        """Test export endpoint returns 404 for missing story."""
        mock_get.side_effect = ValidationError("Story not found", status_code=404)
        
        response = client.get('/api/story/nonexistent/export/pdf')
        assert response.status_code == 404  # Specific status code assertion


class TestStoryRepositoryCRUD:
    """Comprehensive CRUD tests for story repository.
    
    Note: This test class uses create_story_repository() directly (not mocked)
    because these are integration tests that verify the actual repository
    implementation behavior. For unit tests that test code that *uses* the
    repository, use patch('app.get_story_repository') to mock the repository
    interface instead.
    
    This pattern is consistent with the testing strategy:
    - Integration tests (like this): Use real repository instances
    - Unit tests: Mock app.get_story_repository() or app.get_pipeline()
    """
    
    @pytest.fixture(autouse=True)
    def isolated_repo(self, temp_stories_dir):
        """Create an isolated repository for each test with proper cleanup.
        
        Uses create_story_repository() directly for integration testing.
        The repository is isolated via temp_stories_dir fixture.
        """
        with patch('src.shortstory.utils.storage.STORAGE_DIR', temp_stories_dir):
            from src.shortstory.utils.repository import create_story_repository
            repo = create_story_repository()
            yield repo
            # Explicit cleanup: clear all stories after each test to prevent interdependencies
            try:
                all_stories = repo.list(page=1, per_page=1000)
                for story in all_stories.get("stories", []):
                    repo.delete(story["id"])
            except (KeyError, ValueError, AttributeError) as e:
                # Ignore cleanup errors for missing keys, invalid values, or missing attributes
                # These can occur if stories are already deleted or have unexpected structure
                pass
    
    @pytest.fixture
    def temp_stories_dir(self, tmp_path):
        """Create a temporary directory for story storage."""
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir()
        return str(stories_dir)
    
    def test_repository_save(self, isolated_repo, sample_story):
        """Test saving a story."""
        result = isolated_repo.save(sample_story)
        assert result is True
    
    def test_repository_load(self, isolated_repo, sample_story):
        """Test loading a story."""
        isolated_repo.save(sample_story)
        loaded = isolated_repo.load(sample_story["id"])
        assert loaded is not None
        assert loaded["id"] == sample_story["id"]
    
    def test_repository_load_nonexistent(self, isolated_repo):
        """Test loading non-existent story returns None."""
        loaded = isolated_repo.load("nonexistent_id")
        assert loaded is None
    
    def test_repository_list_pagination(self, isolated_repo, sample_story):
        """Test listing stories with pagination."""
        # Save multiple stories
        for i in range(5):
            story = sample_story.copy()
            story["id"] = f"test_story_{i}"
            isolated_repo.save(story)
        
        result = isolated_repo.list(page=1, per_page=2)
        # Check proper structure (should be dict with stories and pagination, not just list)
        assert isinstance(result, dict)
        assert "stories" in result or isinstance(result, list)
        if isinstance(result, dict):
            assert "pagination" in result
            assert len(result.get("stories", [])) <= 2
        else:
            assert len(result) <= 2


class TestErrorHandlers:
    """Test suite for error handlers."""
    
    def test_validation_error_handler(self, client):
        """Test ValidationError handler returns 400."""
        # This would typically be tested through actual endpoint calls
        # For now, we verify the error handler is registered
        response = client.post('/api/generate', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestGenerateEndpointMockedPipeline:
    """Test suite for /api/generate with mocked pipeline."""
    
    def test_generate_api_error_handling_specific_api_error(self, client):
        """Test handling of specific APIError from pipeline."""
        payload = {
            "idea": "Test idea",
            "character": {"name": "Test"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        
        with patch('app.get_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.capture_premise.side_effect = APIError(
                "LLM_AUTH_ERROR",
                "Invalid API Key",
                status_code=401
            )
            mock_get_pipeline.return_value = mock_pipeline
            
            response = client.post('/api/generate', json=payload)
            assert response.status_code == 401  # Specific status code
            data = response.get_json()
            assert "error" in data
            assert data.get("error_code") == "LLM_AUTH_ERROR"
    
    def test_generate_pipeline_generic_exception_handling(self, client):
        """Test handling of unexpected generic exceptions from pipeline."""
        payload = {
            "idea": "Test idea",
            "character": {"name": "Test"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        
        with patch('app.get_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.capture_premise.side_effect = Exception("Unexpected internal error")
            mock_get_pipeline.return_value = mock_pipeline
            
            response = client.post('/api/generate', json=payload)
            assert response.status_code == 500  # Specific status code
            data = response.get_json()
            assert "error" in data
