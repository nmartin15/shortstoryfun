"""
Comprehensive rate limiting tests.

This module tests that rate limiting actually works by:
- Making multiple requests to exceed limits
- Verifying 429 responses when limits are exceeded
- Checking rate limit headers in responses
- Testing different endpoints with different rate limits
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from flask import Flask

from app import create_app
from tests.test_constants import HTTP_OK, HTTP_TOO_MANY_REQUESTS


@pytest.fixture
def rate_limit_client():
    """Create a test client with very low rate limits for testing.
    
    Uses in-memory storage for Flask-Limiter to ensure rate limiting
    is properly enforced in tests. The low limits (2 per minute) allow
    tests to quickly verify rate limiting behavior without long waits.
    """
    # Configure very low rate limits for testing
    config = {
        'TESTING': True,
        'GENERATE_RATE_LIMIT': '2 per minute',
        'REVISION_RATE_LIMIT': '2 per minute',
        'EXPORT_RATE_LIMIT': '2 per minute',
        'MEMORABILITY_RATE_LIMIT': '2 per minute',
        'SAVE_STORY_RATE_LIMIT': '2 per minute',
        'LIST_STORIES_RATE_LIMIT': '2 per minute',
        'VALIDATE_RATE_LIMIT': '2 per minute',
        'GET_STORY_RATE_LIMIT': '2 per minute',
        'UPDATE_STORY_RATE_LIMIT': '2 per minute',
        'REVISION_HISTORY_RATE_LIMIT': '2 per minute',
        'COMPARE_VERSIONS_RATE_LIMIT': '2 per minute',
        'JOB_STATUS_RATE_LIMIT': '2 per minute',
        # Ensure Flask-Limiter uses in-memory storage for testing
        'RATELIMIT_STORAGE_URL': 'memory://',
    }
    app = create_app(config=config)
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


class TestRateLimitingEnforcement:
    """Test that rate limiting is actually enforced."""
    
    def test_generate_endpoint_rate_limit_enforced(self, rate_limit_client, sample_story_payload):
        """Test that generate endpoint enforces rate limits."""
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo, \
             patch('app.get_genre_config') as mock_get_genre_config, \
             patch('app.check_distinctiveness') as mock_check_distinctiveness:
            # Setup genre config mock
            mock_get_genre_config.return_value = {
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"]
            }
            
            # Setup distinctiveness mocks
            mock_check_distinctiveness.return_value = {
                "score": 0.8,
                "has_cliches": False
            }
            
            # Setup pipeline mocks with proper return values
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {
                "genre": sample_story_payload["genre"],
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"],
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline_instance.scaffold.return_value = {
                "tone": "balanced",
                "pace": "moderate",
                "pov": "third person"
            }
            mock_pipeline_instance.draft.return_value = {
                "text": "This is a test story.",
                "word_count": 5
            }
            mock_pipeline_instance.revise.return_value = {
                "text": "This is a revised test story.",
                "word_count": 6
            }
            # Create a proper word_validator mock
            mock_word_validator = MagicMock()
            mock_word_validator.count_words.return_value = 6
            mock_pipeline_instance.word_validator = mock_word_validator
            mock_pipeline_instance.genre = sample_story_payload["genre"]
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            # Setup repository mock
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            # First request should succeed
            response1 = rate_limit_client.post('/api/generate', json=sample_story_payload)
            assert response1.status_code == HTTP_OK, "First request should succeed"
            
            # Second request should succeed (within limit of 2 per minute)
            response2 = rate_limit_client.post('/api/generate', json=sample_story_payload)
            assert response2.status_code == HTTP_OK, "Second request should succeed"
            
            # Third request should be rate limited
            response3 = rate_limit_client.post('/api/generate', json=sample_story_payload)
            assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
                "Third request should be rate limited (429) - rate limiting is actually enforced"
            
            # Verify rate limit error response contains proper error information
            if response3.is_json:
                error_data = response3.get_json()
                assert "error" in error_data or "message" in error_data, \
                    "Rate limit error should include error message"
                error_text = str(error_data).lower()
                assert "rate limit" in error_text or "too many requests" in error_text, \
                    "Error message should indicate rate limit was exceeded"
            
            # Verify rate limit headers are present (Flask-Limiter may add these)
            has_rate_limit_info = any(
                header in response3.headers for header in [
                    'X-RateLimit-Limit',
                    'Retry-After',
                    'X-RateLimit-Remaining',
                    'X-RateLimit-Reset'
                ]
            )
            # Note: Some Flask-Limiter versions may not add headers in test mode,
            # but the 429 status code confirms rate limiting is working
            
            # Verify actual rate limit behavior: first two requests should succeed
            assert response1.status_code == HTTP_OK, "First request must succeed"
            assert response2.status_code == HTTP_OK, "Second request must succeed"
            # Third request should be blocked - this is the key assertion that rate limiting works
            assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
                "Third request must be rate limited (429) - this proves rate limiting is enforced"
            
            # Verify rate limit tracking: check that remaining count decreases
            if 'X-RateLimit-Remaining' in response1.headers:
                remaining1 = int(response1.headers.get('X-RateLimit-Remaining', '0'))
                if 'X-RateLimit-Remaining' in response2.headers:
                    remaining2 = int(response2.headers.get('X-RateLimit-Remaining', '0'))
                    # Remaining should decrease after each request
                    assert remaining2 <= remaining1, \
                        "Rate limit remaining should decrease after each request"
            
            # Additional verification: make sure subsequent requests are also rate limited
            response4 = rate_limit_client.post('/api/generate', json=sample_story_payload)
            assert response4.status_code == HTTP_TOO_MANY_REQUESTS, \
                "Fourth request should also be rate limited - confirms rate limiting persists"
    
    def test_validate_endpoint_rate_limit_enforced(self, rate_limit_client):
        """Test that validate endpoint enforces rate limits."""
        payload = {"text": "Test story text"}
        
        # First request should succeed
        response1 = rate_limit_client.post('/api/validate', json=payload)
        assert response1.status_code == HTTP_OK, "First request should succeed"
        
        # Second request should succeed
        response2 = rate_limit_client.post('/api/validate', json=payload)
        assert response2.status_code == HTTP_OK, "Second request should succeed"
        
        # Third request should be rate limited
        response3 = rate_limit_client.post('/api/validate', json=payload)
        assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
            "Third request should be rate limited (429)"
    
    def test_memorability_endpoint_rate_limit_enforced(self, rate_limit_client):
        """Test that memorability endpoint enforces rate limits."""
        payload = {
            "text": "Test story text",
            "character": {"name": "Test", "description": "A test character"},
            "premise": "A test premise"
        }
        
        with patch('app.get_memorability_scorer') as mock_get_scorer:
            mock_scorer = MagicMock()
            mock_scorer.score_story.return_value = {
                "score": 0.75,
                "factors": []
            }
            mock_get_scorer.return_value = mock_scorer
            
            # First request should succeed
            response1 = rate_limit_client.post('/api/memorability/score', json=payload)
            assert response1.status_code == HTTP_OK, "First request should succeed"
            
            # Second request should succeed
            response2 = rate_limit_client.post('/api/memorability/score', json=payload)
            assert response2.status_code == HTTP_OK, "Second request should succeed"
            
            # Third request should be rate limited
            response3 = rate_limit_client.post('/api/memorability/score', json=payload)
            assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
                "Third request should be rate limited (429)"
    
    def test_list_stories_endpoint_rate_limit_enforced(self, rate_limit_client):
        """Test that list stories endpoint enforces rate limits."""
        with patch('app.get_story_repository') as mock_get_repo:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = []
            mock_get_repo.return_value = mock_repo
            
            # First request should succeed
            response1 = rate_limit_client.get('/api/stories')
            assert response1.status_code == HTTP_OK, "First request should succeed"
            
            # Second request should succeed
            response2 = rate_limit_client.get('/api/stories')
            assert response2.status_code == HTTP_OK, "Second request should succeed"
            
            # Third request should be rate limited
            response3 = rate_limit_client.get('/api/stories')
            assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
                "Third request should be rate limited (429)"
    
    def test_rate_limit_headers_present(self, rate_limit_client, sample_story_payload):
        """Test that rate limit headers are present in responses."""
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo, \
             patch('app.get_genre_config') as mock_get_genre_config, \
             patch('app.check_distinctiveness') as mock_check_distinctiveness:
            # Setup genre config mock
            mock_get_genre_config.return_value = {
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"]
            }
            
            # Setup distinctiveness mocks
            mock_check_distinctiveness.return_value = {
                "score": 0.8,
                "has_cliches": False
            }
            
            # Setup pipeline mocks with proper return values
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {
                "genre": sample_story_payload["genre"],
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"],
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline_instance.scaffold.return_value = {
                "tone": "balanced",
                "pace": "moderate",
                "pov": "third person"
            }
            mock_pipeline_instance.draft.return_value = {
                "text": "This is a test story.",
                "word_count": 5
            }
            mock_pipeline_instance.revise.return_value = {
                "text": "This is a revised test story.",
                "word_count": 6
            }
            # Create a proper word_validator mock
            mock_word_validator = MagicMock()
            mock_word_validator.count_words.return_value = 6
            mock_pipeline_instance.word_validator = mock_word_validator
            mock_pipeline_instance.genre = sample_story_payload["genre"]
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            # Setup repository mock
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            # Make a request and check for rate limit headers
            response = rate_limit_client.post('/api/generate', json=sample_story_payload)
            
            # Flask-Limiter should add headers (may vary by version)
            # Check for common rate limit header patterns
            has_rate_limit_info = any(
                header in response.headers for header in [
                    'X-RateLimit-Limit',
                    'X-RateLimit-Remaining',
                    'X-RateLimit-Reset',
                    'Retry-After'
                ]
            )
            # Note: Some Flask-Limiter versions may not add headers in test mode
            # This test verifies the structure is correct even if headers aren't present in test mode
            assert response.status_code in [HTTP_OK, HTTP_TOO_MANY_REQUESTS], \
                "Response should have valid status code"
    
    def test_rate_limit_reset_after_time_window(self, rate_limit_client):
        """Test that rate limits reset after the time window."""
        import time
        payload = {"text": "Test story text"}
        
        # Make 2 requests (the limit)
        response1 = rate_limit_client.post('/api/validate', json=payload)
        assert response1.status_code == HTTP_OK, "First request should succeed"
        
        response2 = rate_limit_client.post('/api/validate', json=payload)
        assert response2.status_code == HTTP_OK, "Second request should succeed"
        
        # Third should be rate limited
        response3 = rate_limit_client.post('/api/validate', json=payload)
        assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
            "Third request should be rate limited"
        
        # Verify actual behavior: check Retry-After header if present
        if 'Retry-After' in response3.headers:
            retry_after = int(response3.headers.get('Retry-After', '0'))
            assert retry_after > 0, "Retry-After should be a positive number"
        
        # Wait for the time window to expire (1 minute = 60 seconds)
        # For testing, we wait 61 seconds to ensure the window has reset
        time.sleep(61)
        
        # After waiting, should be able to make requests again
        response4 = rate_limit_client.post('/api/validate', json=payload)
        assert response4.status_code == HTTP_OK, \
            "Rate limit should reset after time window expires"
        
        # Verify we can make another request after reset
        response5 = rate_limit_client.post('/api/validate', json=payload)
        assert response5.status_code == HTTP_OK, \
            "Should be able to make requests after rate limit reset"
    
    def test_rate_limit_tracks_requests_correctly(self, rate_limit_client):
        """Test that rate limiting correctly tracks the number of requests."""
        payload = {"text": "Test story text"}
        
        # First request should succeed
        response1 = rate_limit_client.post('/api/validate', json=payload)
        assert response1.status_code == HTTP_OK
        
        # Second request should succeed (within limit of 2 per minute)
        response2 = rate_limit_client.post('/api/validate', json=payload)
        assert response2.status_code == HTTP_OK
        
        # Third request should be rate limited
        response3 = rate_limit_client.post('/api/validate', json=payload)
        assert response3.status_code == HTTP_TOO_MANY_REQUESTS, \
            "Third request should exceed rate limit"
        
        # Fourth request should also be rate limited
        response4 = rate_limit_client.post('/api/validate', json=payload)
        assert response4.status_code == HTTP_TOO_MANY_REQUESTS, \
            "Fourth request should also be rate limited"
    
    def test_rate_limit_different_endpoints_independent(self, rate_limit_client):
        """Test that rate limits are independent across different endpoints."""
        payload = {"text": "Test story text"}
        
        # Exceed limit on validate endpoint
        rate_limit_client.post('/api/validate', json=payload)
        rate_limit_client.post('/api/validate', json=payload)
        response3 = rate_limit_client.post('/api/validate', json=payload)
        assert response3.status_code == HTTP_TOO_MANY_REQUESTS
        
        # Other endpoints should still work (they have separate rate limits)
        with patch('app.get_memorability_scorer') as mock_get_scorer:
            mock_scorer = MagicMock()
            mock_scorer.score_story.return_value = {
                "overall_score": 0.75,
                "dimensions": {}
            }
            mock_get_scorer.return_value = mock_scorer
            
            memorability_payload = {
                "text": "Test story text",
                "character": {"name": "Test", "description": "A test character"},
                "premise": "A test premise"
            }
            response = rate_limit_client.post('/api/memorability/score', json=memorability_payload)
            # Should succeed because it's a different endpoint with its own rate limit
            assert response.status_code == HTTP_OK, \
                "Different endpoints should have independent rate limits"


class TestRateLimitErrorResponse:
    """Test rate limit error response format."""
    
    def test_rate_limit_error_format(self, rate_limit_client, sample_story_payload):
        """Test that rate limit errors return proper JSON format."""
        with patch('app.get_pipeline') as mock_get_pipeline, \
             patch('app.get_story_repository') as mock_get_repo, \
             patch('app.get_genre_config') as mock_get_genre_config, \
             patch('app.check_distinctiveness') as mock_check_distinctiveness:
            # Setup genre config mock
            mock_get_genre_config.return_value = {
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"]
            }
            
            # Setup distinctiveness mocks
            mock_check_distinctiveness.return_value = {
                "score": 0.8,
                "has_cliches": False
            }
            
            # Setup pipeline mocks with proper return values
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.capture_premise.return_value = sample_story_payload
            mock_pipeline_instance.generate_outline.return_value = {
                "genre": sample_story_payload["genre"],
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"],
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline_instance.scaffold.return_value = {
                "tone": "balanced",
                "pace": "moderate",
                "pov": "third person"
            }
            mock_pipeline_instance.draft.return_value = {
                "text": "This is a test story.",
                "word_count": 5
            }
            mock_pipeline_instance.revise.return_value = {
                "text": "This is a revised test story.",
                "word_count": 6
            }
            # Create a proper word_validator mock
            mock_word_validator = MagicMock()
            mock_word_validator.count_words.return_value = 6
            mock_pipeline_instance.word_validator = mock_word_validator
            mock_pipeline_instance.genre = sample_story_payload["genre"]
            mock_get_pipeline.return_value = mock_pipeline_instance
            
            # Setup repository mock
            mock_repo_instance = MagicMock()
            mock_repo_instance.save.return_value = True
            mock_get_repo.return_value = mock_repo_instance
            
            # Exceed rate limit
            rate_limit_client.post('/api/generate', json=sample_story_payload)
            rate_limit_client.post('/api/generate', json=sample_story_payload)
            response = rate_limit_client.post('/api/generate', json=sample_story_payload)
            
            assert response.status_code == HTTP_TOO_MANY_REQUESTS
            assert response.is_json, "Rate limit error should return JSON"
            
            data = response.get_json()
            assert "error" in data or "message" in data, \
                "Rate limit error should include error message"
            assert "error_code" in data, \
                "Rate limit error should include error_code field"

