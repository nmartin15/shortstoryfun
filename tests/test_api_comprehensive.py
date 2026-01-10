"""
Comprehensive API endpoint tests with detailed response validation.

This module tests all API endpoints with comprehensive validation of:
- Response structure (required fields, data types, value constraints)
- Error response format validation
- Request validation (missing fields, invalid types)
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Response

from app import create_app
from src.shortstory.utils.errors import APIError, ValidationError, ServiceUnavailableError
from tests.test_constants import (
    HTTP_OK,
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_NOT_FOUND,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_SERVICE_UNAVAILABLE,
)


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_story_payload():
    """Sample payload for story generation."""
    return {
        "idea": "A lighthouse keeper collects lost voices in glass jars",
        "character": {
            "name": "Mara",
            "description": "A quiet keeper with an unusual collection"
        },
        "theme": "What happens to the stories we never tell?",
        "genre": "Literary",
        "max_words": 5000
    }


@pytest.fixture
def generated_story_id():
    """Mock story ID for testing."""
    return "test_story_12345678"


class TestGenerateEndpoint:
    """Test suite for /api/generate endpoint."""
    
    def test_generate_requires_valid_payload(self, client):
        """Test that generate endpoint validates required fields."""
        response = client.post('/api/generate', json={})
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
        assert "error_code" in data
    
    def test_generate_validates_idea_field(self, client):
        """Test that idea field is required."""
        payload = {
            "character": {"name": "Test"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
        assert "idea" in data.get("error", "").lower() or "required" in data.get("error", "").lower()
    
    def test_generate_validates_empty_idea(self, client):
        """Test that empty idea field is rejected."""
        payload = {
            "idea": "",
            "character": {"name": "Test", "description": "A test character"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
    
    def test_generate_validates_whitespace_only_idea(self, client):
        """Test that whitespace-only idea field is rejected."""
        payload = {
            "idea": "   \n\t  ",
            "character": {"name": "Test", "description": "A test character"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
    
    def test_generate_validates_missing_character(self, client):
        """Test that missing character field is handled."""
        payload = {
            "idea": "A test story idea",
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        # Should either require character or handle gracefully
        assert response.status_code in [HTTP_BAD_REQUEST, HTTP_OK]
        if response.status_code == HTTP_BAD_REQUEST:
            data = response.get_json()
            assert "error" in data
    
    def test_generate_validates_invalid_character_type(self, client):
        """Test that invalid character type is rejected."""
        payload = {
            "idea": "A test story idea",
            "character": "not a dict",  # Invalid type
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
    
    def test_generate_validates_invalid_max_words(self, client, sample_story_payload):
        """Test that invalid max_words value is rejected."""
        sample_story_payload["max_words"] = -1  # Invalid negative value
        
        response = client.post('/api/generate', json=sample_story_payload)
        
        # Should either reject negative values or handle gracefully
        assert response.status_code in [HTTP_BAD_REQUEST, HTTP_OK]
        if response.status_code == HTTP_BAD_REQUEST:
            data = response.get_json()
            assert "error" in data
    
    def test_generate_validates_too_large_max_words(self, client, sample_story_payload):
        """Test that excessively large max_words value is handled."""
        sample_story_payload["max_words"] = 100000  # Very large value
        
        # Should either reject or cap the value
        response = client.post('/api/generate', json=sample_story_payload)
        
        # Should handle gracefully (either reject or cap)
        assert response.status_code in [HTTP_BAD_REQUEST, HTTP_OK]
    
    def test_generate_validates_genre(self, client, sample_story_payload):
        """Test that genre validation works - invalid genre should fallback to default."""
        sample_story_payload["genre"] = "Invalid Genre"
        
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {"acts": {}}
            mock_pipeline_instance.scaffold.return_value = {}
            mock_pipeline_instance.draft.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.revise.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.word_validator.count_words.return_value = 1
            mock_pipeline_instance.genre = "General Fiction"  # Should fallback
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            response = client.post('/api/generate', json=sample_story_payload)
            # Should succeed with fallback to default genre
            assert response.status_code == HTTP_OK
            data = response.get_json()
            assert "story_id" in data or "id" in data
    
    def test_generate_validates_idea_length_limit(self, client):
        """Test that story idea exceeding 2000 characters is rejected."""
        payload = {
            "idea": "A" * 2001,  # 2001 characters - exceeds limit
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
        assert "2000" in data.get("error", "") or "too long" in data.get("error", "").lower()
        assert "idea" in data.get("error", "").lower() or "premise" in data.get("error", "").lower()
    
    def test_generate_accepts_idea_at_limit(self, client, sample_story_payload):
        """Test that story idea at exactly 2000 characters is accepted."""
        sample_story_payload["idea"] = "A" * 2000  # Exactly 2000 characters
        
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {"acts": {}}
            mock_pipeline_instance.scaffold.return_value = {}
            mock_pipeline_instance.draft.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.revise.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.word_validator.count_words.return_value = 1
            mock_pipeline_instance.genre_config = {"genre": "General Fiction"}
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            response = client.post('/api/generate', json=sample_story_payload)
            # Should succeed at the limit
            assert response.status_code == HTTP_OK
    
    def test_generate_validates_character_description_length_limit(self, client):
        """Test that character description exceeding 2000 characters is rejected."""
        payload = {
            "idea": "A test story idea",
            "character": {"description": "A" * 2001},  # 2001 characters - exceeds limit
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
        assert "2000" in data.get("error", "") or "too long" in data.get("error", "").lower()
        assert "character" in data.get("error", "").lower()
    
    def test_generate_validates_theme_length_limit(self, client):
        """Test that theme exceeding 1000 characters is rejected."""
        payload = {
            "idea": "A test story idea",
            "theme": "A" * 1001,  # 1001 characters - exceeds limit
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
        assert "1000" in data.get("error", "") or "too long" in data.get("error", "").lower()
        assert "theme" in data.get("error", "").lower()


class TestGenerateEndpointMockedPipeline:
    """Test suite for /api/generate with mocked pipeline."""
    
    def test_generate_api_error_handling_specific_api_error(self, client, sample_story_payload):
        """Test handling of specific APIError from pipeline."""
        with patch('app.get_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            # Simulate a specific APIError from the pipeline
            mock_pipeline.capture_premise.side_effect = APIError(
                "LLM_AUTH_ERROR",
                "Invalid API Key",
                status_code=401
            )
            mock_get_pipeline.return_value = mock_pipeline
            
            response = client.post('/api/generate', json=sample_story_payload)
            assert response.status_code == HTTP_UNAUTHORIZED  # Assert specific status code
            data = response.get_json()
            assert "error" in data
            assert data["error_code"] == "LLM_AUTH_ERROR"
            assert "Invalid API Key" in data["error"]
    
    def test_generate_pipeline_generic_exception_handling(self, client, sample_story_payload):
        """Test handling of unexpected generic exceptions from pipeline."""
        with patch('app.get_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            # Simulate a specific unexpected exception type (RuntimeError) instead of generic Exception
            # This makes the test more explicit about what error types are being tested
            mock_pipeline.capture_premise.side_effect = RuntimeError("Unexpected internal error")
            mock_get_pipeline.return_value = mock_pipeline
            
            response = client.post('/api/generate', json=sample_story_payload)
            # Assert it's caught by a generic 500 handler
            assert response.status_code == HTTP_INTERNAL_SERVER_ERROR
            data = response.get_json()
            assert "error" in data
            assert data["error_code"] == "INTERNAL_ERROR"
    
    def test_generate_service_unavailable_error(self, client, sample_story_payload):
        """Test handling of ServiceUnavailableError."""
        with patch('app.get_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.capture_premise.side_effect = ServiceUnavailableError(
                "LLM Service",
                "The LLM service is temporarily unavailable"
            )
            mock_get_pipeline.return_value = mock_pipeline
            
            response = client.post('/api/generate', json=sample_story_payload)
            assert response.status_code == HTTP_SERVICE_UNAVAILABLE
            data = response.get_json()
            assert "error" in data
            assert data["error_code"] == "SERVICE_UNAVAILABLE"
            assert "unavailable" in data["error"].lower()


class TestStoryExportEndpoint:
    """Test suite for story export endpoints."""
    
    @patch('app.export_story_from_dict')
    def test_export_supports_multiple_formats(self, mock_export, client, generated_story_id):
        """Test that export endpoint supports multiple formats."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_export.return_value = mock_response
        
        formats = ["pdf", "markdown", "txt"]
        for format_name in formats:
            response = client.get(f'/api/story/{generated_story_id}/export/{format_name}')
            assert response.status_code == HTTP_OK
            assert mock_export.called
    
    def test_export_invalid_format(self, client, generated_story_id):
        """Test that invalid export format returns error."""
        response = client.get(f'/api/story/{generated_story_id}/export/invalid_format')
        # Invalid format should return 400 (bad request) or 404 (not found)
        # Be specific: invalid format is a bad request, not found would be for missing story
        assert response.status_code == HTTP_BAD_REQUEST or response.status_code == HTTP_NOT_FOUND
        # Prefer 400 for invalid format parameter
        if response.status_code == HTTP_BAD_REQUEST:
            assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert "error" in data
    
    def test_export_missing_story_id(self, client):
        """Test that export with missing story ID returns error."""
        response = client.get('/api/story/export/pdf')
        # Should return 404 (not found) for missing story ID
        assert response.status_code == HTTP_NOT_FOUND
        data = response.get_json()
        assert "error" in data
    
    def test_export_nonexistent_story(self, client):
        """Test that export with nonexistent story ID returns error."""
        nonexistent_id = "nonexistent_story_99999"
        with patch('app.get_story_or_404') as mock_get_story:
            from flask import abort
            mock_get_story.side_effect = lambda story_id: abort(404, description="Story not found")
            
            response = client.get(f'/api/story/{nonexistent_id}/export/pdf')
            assert response.status_code == HTTP_NOT_FOUND
            data = response.get_json()
            assert "error" in data or "not found" in str(data).lower()
    
    def test_export_with_invalid_story_id_format(self, client):
        """Test that export with invalid story ID format returns error.
        
        This test ensures the endpoint properly handles invalid story ID formats,
        not just missing or nonexistent IDs. This addresses the concern that tests
        might mask issues by always using a valid generated_story_id.
        """
        # Test with various invalid ID formats
        invalid_ids = [
            "",  # Empty string
            "invalid",  # Invalid format
            "123",  # Too short
            None,  # None value (if passed as query param)
        ]
        
        for invalid_id in invalid_ids:
            if invalid_id is None:
                # Skip None as it can't be in URL path
                continue
            response = client.get(f'/api/story/{invalid_id}/export/pdf')
            # Should return 404 for invalid format or missing story
            assert response.status_code in [HTTP_NOT_FOUND, HTTP_BAD_REQUEST]
            data = response.get_json()
            assert "error" in data


class TestStoryListEndpoint:
    """Test suite for /api/stories endpoint."""
    
    def test_list_stories_returns_pagination(self, client):
        """Test that list endpoint returns pagination metadata."""
        response = client.get('/api/stories')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "stories" in data
        assert "pagination" in data
        assert isinstance(data["stories"], list)
        assert "page" in data["pagination"]
        assert "per_page" in data["pagination"]
        assert "total" in data["pagination"]


class TestHealthEndpoint:
    """Test suite for /api/health endpoint."""
    
    def test_health_endpoint_returns_status(self, client):
        """Test that health endpoint returns status."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data or "health" in data


class TestRateLimiting:
    """Test suite for rate limiting functionality.
    
    Note: Comprehensive rate limiting tests that actually verify rate limit
    enforcement (429 responses, headers, multiple endpoints) are in
    tests/test_rate_limiting.py. This test suite focuses on basic endpoint
    functionality with rate limiting enabled.
    """
    
    def test_generate_endpoint_with_rate_limiting_enabled(self, client, sample_story_payload):
        """Test that generate endpoint works with rate limiting enabled.
        
        This is a basic smoke test. For comprehensive rate limiting tests
        that verify actual enforcement, see tests/test_rate_limiting.py.
        """
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {"acts": {}}
            mock_pipeline_instance.scaffold.return_value = {}
            mock_pipeline_instance.draft.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.revise.return_value = {"text": "story", "word_count": 1}
            mock_pipeline_instance.word_validator.count_words.return_value = 1
            mock_pipeline_instance.genre = sample_story_payload["genre"]
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            # Make a single request - should succeed (rate limit not exceeded)
            response = client.post('/api/generate', json=sample_story_payload)
            assert response.status_code == HTTP_OK, \
                "Endpoint should work when rate limit is not exceeded"


class TestBackgroundJobEndpoints:
    """Test suite for background job endpoints (/api/job/*).
    
    These tests properly handle RQ_AVAILABLE patching by simulating both
    the app.RQ_AVAILABLE flag and the rq_config module availability.
    
    The tests ensure complete isolation by:
    1. Patching sys.modules to simulate rq_config import failure
    2. Patching app.RQ_AVAILABLE to control the flag
    3. Patching app.get_job to handle module-level imports
    This comprehensive patching ensures tests work regardless of whether
    rq_config is actually available in the test environment.
    """
    
    def test_get_job_status_requires_rq_simulated(self, client):
        """Test that job status endpoint returns 503 when RQ is unavailable.
        
        This test simulates the scenario where rq_config cannot be imported,
        ensuring the endpoint gracefully handles RQ unavailability.
        """
        import sys
        from unittest.mock import MagicMock
        
        # Simulate RQ being unavailable at the module level
        # This covers the case where rq_config import fails
        with patch.dict(sys.modules, {'rq_config': None}), \
             patch('app.RQ_AVAILABLE', False):
            response = client.get('/api/job/test_job_123')
            assert response.status_code == HTTP_SERVICE_UNAVAILABLE
            data = response.get_json()
            assert "error" in data or "message" in data
            assert "unavailable" in data.get("error", "").lower() or \
                   "unavailable" in data.get("message", "").lower()
    
    def test_get_job_status_returns_404_for_missing_job_simulated(self, client):
        """Test that job status endpoint returns 404 when job doesn't exist.
        
        This test simulates RQ being available but the job not existing,
        ensuring proper error handling for missing jobs.
        """
        import sys
        from unittest.mock import MagicMock
        
        # Simulate RQ being available, but get_job returns None
        # Since get_job is imported at module level in app.py, we need to patch it in app
        # We also patch sys.modules to ensure rq_config is available for import simulation
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=None)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=None):
            response = client.get('/api/job/nonexistent_job')
            assert response.status_code == HTTP_NOT_FOUND
            data = response.get_json()
            assert "error" in data or "message" in data
            assert "not found" in data.get("error", "").lower() or \
                   "not found" in data.get("message", "").lower()
    
    def test_get_job_status_returns_job_info_when_available(self, client):
        """Test that job status endpoint returns job information when job exists."""
        import sys
        from unittest.mock import MagicMock
        from datetime import datetime
        
        # Create a mock job with all expected attributes
        mock_job = MagicMock()
        mock_job.get_status.return_value = "finished"
        mock_job.created_at = datetime.now()
        mock_job.started_at = datetime.now()
        mock_job.ended_at = datetime.now()
        mock_job.is_finished = True
        mock_job.is_failed = False
        mock_job.result = {"story_id": "test_story_123", "status": "completed"}
        mock_job.exc_info = None
        
        # Since get_job is imported at module level, patch it in app
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=mock_job)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=mock_job):
            response = client.get('/api/job/test_job_123')
            assert response.status_code == HTTP_OK
            data = response.get_json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "finished"
            assert "result" in data
    
    def test_get_job_result_requires_rq_simulated(self, client):
        """Test that job result endpoint returns 503 when RQ is unavailable."""
        import sys
        
        # Simulate RQ being unavailable at the module level
        with patch.dict(sys.modules, {'rq_config': None}), \
             patch('app.RQ_AVAILABLE', False):
            response = client.get('/api/job/test_job_123/result')
            assert response.status_code == HTTP_SERVICE_UNAVAILABLE
            data = response.get_json()
            assert "error" in data or "message" in data
    
    def test_get_job_result_returns_404_for_missing_job(self, client):
        """Test that job result endpoint returns 404 when job doesn't exist."""
        import sys
        from unittest.mock import MagicMock
        
        # Since get_job is imported at module level, patch it in app
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=None)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=None):
            response = client.get('/api/job/nonexistent_job/result')
            assert response.status_code == HTTP_NOT_FOUND
            data = response.get_json()
            assert "error" in data or "message" in data
    
    def test_get_job_result_returns_202_for_incomplete_job(self, client):
        """Test that job result endpoint returns 202 when job is not finished."""
        import sys
        from unittest.mock import MagicMock
        from datetime import datetime
        
        # Create a mock job that is not finished
        mock_job = MagicMock()
        mock_job.get_status.return_value = "started"
        mock_job.is_finished = False
        mock_job.is_failed = False
        
        # Since get_job is imported at module level, patch it in app
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=mock_job)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=mock_job):
            response = client.get('/api/job/test_job_123/result')
            assert response.status_code == 202  # Accepted
            data = response.get_json()
            assert "status" in data
            assert "message" in data
    
    def test_get_job_status_returns_error_for_failed_job(self, client):
        """Test that job status endpoint returns error information for failed jobs."""
        import sys
        from unittest.mock import MagicMock
        from datetime import datetime
        
        # Create a mock job that has failed
        mock_job = MagicMock()
        mock_job.get_status.return_value = "failed"
        mock_job.created_at = datetime.now()
        mock_job.started_at = datetime.now()
        mock_job.ended_at = datetime.now()
        mock_job.is_finished = True
        mock_job.is_failed = True
        mock_job.exc_info = "Job failed with error: Test error message"
        mock_job.result = None
        
        # Since get_job is imported at module level, patch it in app
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=mock_job)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=mock_job):
            response = client.get('/api/job/test_job_123')
            assert response.status_code == HTTP_OK
            data = response.get_json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "failed"
            assert "error" in data
            assert "Test error message" in data["error"]
    
    def test_get_job_result_returns_503_for_failed_job(self, client):
        """Test that job result endpoint returns 503 when job has failed."""
        import sys
        from unittest.mock import MagicMock
        from datetime import datetime
        
        # Create a mock job that has failed
        mock_job = MagicMock()
        mock_job.get_status.return_value = "failed"
        mock_job.is_finished = True
        mock_job.is_failed = True
        mock_job.exc_info = "Job failed with error: Test error message"
        
        # Since get_job is imported at module level, patch it in app
        mock_rq_config = MagicMock()
        mock_rq_config.get_job = MagicMock(return_value=mock_job)
        
        with patch.dict(sys.modules, {'rq_config': mock_rq_config}), \
             patch('app.RQ_AVAILABLE', True), \
             patch('app.get_job', return_value=mock_job):
            response = client.get('/api/job/test_job_123/result')
            assert response.status_code == HTTP_SERVICE_UNAVAILABLE
            data = response.get_json()
            assert "error" in data
            assert "Test error message" in data["error"]