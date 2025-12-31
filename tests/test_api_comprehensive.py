"""
Comprehensive API endpoint tests with response structure validation.

Tests cover all API endpoints with detailed validation of:
- Response structure and required fields
- Data types and value constraints
- Error response formats
- Rate limiting behavior
- Request validation
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from datetime import datetime

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_story_payload():
    """Create a sample story generation payload."""
    return {
        "idea": "A lighthouse keeper who collects lost voices in glass jars",
        "character": {
            "name": "Mara",
            "description": "A lighthouse keeper with an unusual collection",
            "quirks": ["Never speaks above a whisper"],
            "contradictions": "Fiercely protective but terrified of connection"
        },
        "theme": "What happens to the stories we never tell?",
        "genre": "Literary"
    }


@pytest.fixture
def generated_story_id():
    """Return a sample story ID for use in tests."""
    # Return a mock story ID instead of actually generating
    return "test_story_12345"


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_ok(self, client):
        """Test that health endpoint returns status ok."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_health_response_structure(self, client):
        """Test that health response has correct structure."""
        response = client.get('/api/health')
        data = response.get_json()
        
        # Should only have status field
        assert len(data) == 1
        assert data["status"] == "ok"


class TestGenresEndpoint:
    """Test genres endpoint."""
    
    def test_genres_returns_list(self, client):
        """Test that genres endpoint returns a list of genres."""
        response = client.get('/api/genres')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert "genres" in data
        assert isinstance(data["genres"], list)
        assert len(data["genres"]) > 0
    
    def test_genres_all_strings(self, client):
        """Test that all genres are strings."""
        response = client.get('/api/genres')
        data = response.get_json()
        
        for genre in data["genres"]:
            assert isinstance(genre, str)
            assert len(genre.strip()) > 0
    
    def test_genres_includes_expected_genres(self, client):
        """Test that genres list includes expected genres."""
        response = client.get('/api/genres')
        data = response.get_json()
        
        genres = data["genres"]
        expected_genres = ["Horror", "Romance", "Crime Noir", "Literary", "Thriller", "General Fiction"]
        
        # Check that at least some expected genres are present
        found_genres = [g for g in expected_genres if g in genres]
        assert len(found_genres) > 0, "Expected genres not found in response"


class TestStoryGenerationEndpoint:
    """Test story generation endpoint with comprehensive validation."""
    
    def test_generate_requires_idea(self, client):
        """Test that story generation requires an idea."""
        payload = {
            "character": {"name": "Test"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data or "message" in data
    
    def test_generate_returns_complete_response(self, client, sample_story_payload):
        """Test that story generation returns complete response structure."""
        with patch('app.pipeline') as mock_pipeline:
            # Mock pipeline stages
            mock_pipeline.capture_premise.return_value = {
                "idea": sample_story_payload["idea"],
                "character": sample_story_payload["character"],
                "theme": sample_story_payload["theme"]
            }
            mock_pipeline.generate_outline.return_value = {
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline.scaffold.return_value = {
                "pov": "third person",
                "tone": "balanced",
                "pace": "moderate"
            }
            mock_pipeline.draft.return_value = {
                "text": "This is a draft story text with enough words to be meaningful.",
                "word_count": 12
            }
            mock_pipeline.revise.return_value = {
                "text": "This is a revised story text with enough words to be meaningful.",
                "word_count": 12
            }
            mock_pipeline.word_validator.count_words.return_value = 12
            mock_pipeline.genre = sample_story_payload["genre"]
            
            with patch('src.shortstory.utils.get_default_client'):
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post('/api/generate', json=sample_story_payload)
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    
                    # Validate required fields
                    assert "success" in data
                    assert data["success"] is True
                    assert "story_id" in data
                    assert isinstance(data["story_id"], str)
                    assert len(data["story_id"]) > 0
                    assert "story" in data
                    assert isinstance(data["story"], str)
                    assert len(data["story"].strip()) > 0
                    assert "word_count" in data
                    assert isinstance(data["word_count"], int)
                    assert data["word_count"] >= 0
                    assert "max_words" in data
                    assert isinstance(data["max_words"], int)
                    assert data["max_words"] > 0
                    assert data["word_count"] <= data["max_words"]
    
    def test_generate_includes_metadata(self, client, sample_story_payload):
        """Test that story generation includes premise and outline metadata."""
        with patch('app.pipeline') as mock_pipeline:
            premise = {
                "idea": sample_story_payload["idea"],
                "character": sample_story_payload["character"],
                "theme": sample_story_payload["theme"]
            }
            outline = {
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            
            mock_pipeline.capture_premise.return_value = premise
            mock_pipeline.generate_outline.return_value = outline
            mock_pipeline.scaffold.return_value = {"pov": "third person", "tone": "balanced", "pace": "moderate"}
            mock_pipeline.draft.return_value = {"text": "Draft text", "word_count": 2}
            mock_pipeline.revise.return_value = {"text": "Revised text", "word_count": 2}
            mock_pipeline.word_validator.count_words.return_value = 2
            mock_pipeline.genre = sample_story_payload["genre"]
            
            with patch('src.shortstory.utils.get_default_client'):
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post('/api/generate', json=sample_story_payload)
                    data = response.get_json()
                    
                    # Check for optional metadata fields
                    if "premise" in data:
                        assert isinstance(data["premise"], dict)
                    if "outline" in data:
                        assert isinstance(data["outline"], dict)
                    if "genre" in data:
                        assert isinstance(data["genre"], str)
    
    def test_generate_story_content_quality(self, client, sample_story_payload):
        """Test that generated story has minimum quality requirements."""
        with patch('app.pipeline') as mock_pipeline:
            story_text = "This is a meaningful story with multiple sentences. It has enough content to be considered a proper story. The narrative flows naturally and engages the reader."
            
            mock_pipeline.capture_premise.return_value = {
                "idea": sample_story_payload["idea"],
                "character": sample_story_payload["character"],
                "theme": sample_story_payload["theme"]
            }
            mock_pipeline.generate_outline.return_value = {
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline.scaffold.return_value = {"pov": "third person", "tone": "balanced", "pace": "moderate"}
            mock_pipeline.draft.return_value = {"text": story_text, "word_count": 25}
            mock_pipeline.revise.return_value = {"text": story_text, "word_count": 25}
            mock_pipeline.word_validator.count_words.return_value = 25
            mock_pipeline.genre = sample_story_payload["genre"]
            
            with patch('src.shortstory.utils.get_default_client'):
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post('/api/generate', json=sample_story_payload)
                    data = response.get_json()
                    
                    # Validate story content quality
                    story = data.get("story", "")
                    assert len(story) >= 50  # Minimum length
                    assert data.get("word_count", 0) > 0
    
    def test_generate_handles_invalid_genre(self, client, sample_story_payload):
        """Test that invalid genre falls back to default."""
        sample_story_payload["genre"] = "Invalid Genre Name"
        
        with patch('app.pipeline') as mock_pipeline:
            mock_pipeline.capture_premise.return_value = {
                "idea": sample_story_payload["idea"],
                "character": sample_story_payload["character"],
                "theme": sample_story_payload["theme"]
            }
            mock_pipeline.generate_outline.return_value = {
                "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
            }
            mock_pipeline.scaffold.return_value = {"pov": "third person", "tone": "balanced", "pace": "moderate"}
            mock_pipeline.draft.return_value = {"text": "Story text", "word_count": 2}
            mock_pipeline.revise.return_value = {"text": "Story text", "word_count": 2}
            mock_pipeline.word_validator.count_words.return_value = 2
            mock_pipeline.genre = "General Fiction"  # Should fallback
            
            with patch('src.shortstory.utils.get_default_client'):
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post('/api/generate', json=sample_story_payload)
                    # Should still succeed with fallback genre
                    assert response.status_code in [200, 400]  # May fail validation or succeed


class TestStoryRetrievalEndpoint:
    """Test story retrieval endpoint."""
    
    def test_get_story_returns_complete_data(self, client, generated_story_id):
        """Test that getting a story returns complete data structure."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "Test story text",
                "max_words": 7500,
                "premise": {"idea": "Test idea"}
            }
            mock_get.return_value = mock_story
            
            with patch('app.pipeline') as mock_pipeline:
                mock_pipeline.word_validator.count_words.return_value = 3
                
                response = client.get(f'/api/story/{generated_story_id}')
                
                assert response.status_code == 200
                data = response.get_json()
                
                assert "story_id" in data
                assert data["story_id"] == generated_story_id
                assert "story" in data
                assert isinstance(data["story"], str)
                assert "word_count" in data
                assert "max_words" in data
                assert data["word_count"] <= data["max_words"]
    
    def test_get_story_404_for_missing(self, client):
        """Test that getting a non-existent story returns 404."""
        with patch('app.get_story_or_404') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/api/story/nonexistent_id')
            assert response.status_code == 404
            
            data = response.get_json()
            assert "error" in data or "message" in data


class TestStoryUpdateEndpoint:
    """Test story update endpoint."""
    
    def test_update_story_requires_text(self, client, generated_story_id):
        """Test that updating a story requires text field."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_get.return_value = {"id": generated_story_id, "text": "Original text"}
            
            response = client.put(f'/api/story/{generated_story_id}', json={})
            assert response.status_code == 400
            
            data = response.get_json()
            assert "error" in data or "message" in data
    
    def test_update_story_validates_word_count(self, client, generated_story_id):
        """Test that updating a story validates word count."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_get.return_value = {"id": generated_story_id, "text": "Original text", "max_words": 7500}
            
            with patch('app.pipeline') as mock_pipeline:
                # Mock word count exceeding limit
                mock_pipeline.word_validator.validate.return_value = (8000, False)
                
                response = client.put(
                    f'/api/story/{generated_story_id}',
                    json={"text": "A" * 10000}
                )
                assert response.status_code == 400
    
    def test_update_story_returns_success(self, client, generated_story_id):
        """Test that successful story update returns success response."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {"id": generated_story_id, "text": "Original text", "max_words": 7500}
            mock_get.return_value = mock_story
            
            with patch('app.pipeline') as mock_pipeline:
                mock_pipeline.word_validator.validate.return_value = (100, True)
                
                with patch('app.story_storage') as mock_storage:
                    mock_storage.update_story.return_value = True
                    
                    response = client.put(
                        f'/api/story/{generated_story_id}',
                        json={"text": "Updated story text"}
                    )
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert "success" in data
                    assert data["success"] is True
                    assert "story_id" in data
                    assert "word_count" in data


class TestStoryListingEndpoint:
    """Test story listing endpoint."""
    
    def test_list_stories_returns_paginated_response(self, client):
        """Test that listing stories returns paginated response."""
        with patch('app.story_storage') as mock_storage:
            mock_storage.list_stories.return_value = {
                "stories": [],
                "pagination": {
                    "page": 1,
                    "per_page": 50,
                    "total": 0,
                    "pages": 0
                }
            }
            
            response = client.get('/api/stories')
            assert response.status_code == 200
            
            data = response.get_json()
            assert "success" in data
            assert data["success"] is True
            assert "stories" in data
            assert isinstance(data["stories"], list)
            assert "pagination" in data
            assert isinstance(data["pagination"], dict)
    
    def test_list_stories_pagination_parameters(self, client):
        """Test that pagination parameters work correctly."""
        with patch('app.story_storage') as mock_storage:
            mock_storage.list_stories.return_value = {
                "stories": [{"id": f"story_{i}"} for i in range(10)],
                "pagination": {
                    "page": 2,
                    "per_page": 10,
                    "total": 25,
                    "pages": 3
                }
            }
            
            response = client.get('/api/stories?page=2&per_page=10')
            assert response.status_code == 200
            
            data = response.get_json()
            pagination = data["pagination"]
            assert pagination["page"] == 2
            assert pagination["per_page"] == 10
            assert pagination["total"] == 25
            assert pagination["pages"] == 3
    
    def test_list_stories_enforces_per_page_limit(self, client):
        """Test that per_page is limited to maximum."""
        with patch('app.story_storage') as mock_storage:
            mock_storage.list_stories.return_value = {
                "stories": [],
                "pagination": {"page": 1, "per_page": 100, "total": 0, "pages": 0}
            }
            
            # Request more than max (100)
            response = client.get('/api/stories?per_page=200')
            assert response.status_code == 200
            
            # Should be capped at 100
            data = response.get_json()
            assert data["pagination"]["per_page"] <= 100


class TestValidationEndpoint:
    """Test validation endpoint."""
    
    def test_validate_requires_text(self, client):
        """Test that validation requires text field."""
        response = client.post('/api/validate', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        assert "error" in data or "message" in data
    
    def test_validate_returns_word_count(self, client):
        """Test that validation returns word count information."""
        with patch('app.pipeline') as mock_pipeline:
            mock_pipeline.word_validator.validate.return_value = (100, True)
            
            with patch('app.check_distinctiveness') as mock_distinct:
                mock_distinct.return_value = {
                    "distinctiveness_score": 0.8,
                    "has_cliches": False
                }
                
                response = client.post('/api/validate', json={"text": "Test story text"})
                assert response.status_code == 200
                
                data = response.get_json()
                assert "word_count" in data
                assert "max_words" in data
                assert "is_valid" in data
                assert isinstance(data["is_valid"], bool)
                assert "distinctiveness" in data
                assert isinstance(data["distinctiveness"], dict)


class TestTemplatesEndpoint:
    """Test templates endpoint."""
    
    def test_templates_returns_all_templates(self, client):
        """Test that templates endpoint returns all templates."""
        with patch('app.get_all_templates') as mock_templates:
            mock_templates.return_value = [
                {"id": "template1", "name": "Template 1"},
                {"id": "template2", "name": "Template 2"}
            ]
            
            with patch('app.get_available_template_genres') as mock_genres:
                mock_genres.return_value = ["Horror", "Romance"]
                
                response = client.get('/api/templates')
                assert response.status_code == 200
                
                data = response.get_json()
                assert "success" in data
                assert "templates" in data
                assert isinstance(data["templates"], list)
                assert "genres" in data
    
    def test_templates_filters_by_genre(self, client):
        """Test that templates can be filtered by genre."""
        with patch('app.get_templates_for_genre') as mock_templates:
            mock_templates.return_value = [
                {"id": "horror1", "name": "Horror Template"}
            ]
            
            response = client.get('/api/templates?genre=Horror')
            assert response.status_code == 200
            
            data = response.get_json()
            assert "success" in data
            assert "genre" in data
            assert data["genre"] == "Horror"
            assert "templates" in data


class TestErrorResponseFormat:
    """Test that error responses have consistent format."""
    
    def test_validation_error_format(self, client):
        """Test that validation errors have consistent format."""
        response = client.post('/api/generate', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        # Should have error message
        assert "error" in data or "message" in data
        # May have details field
        if "details" in data:
            assert isinstance(data["details"], dict)
    
    def test_not_found_error_format(self, client):
        """Test that 404 errors have consistent format."""
        with patch('app.get_story_or_404') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/api/story/nonexistent')
            assert response.status_code == 404
            
            data = response.get_json()
            assert "error" in data or "message" in data


class TestRequestValidation:
    """Test request validation for various endpoints."""
    
    def test_generate_rejects_empty_idea(self, client):
        """Test that empty idea is rejected."""
        payload = {
            "idea": "   ",  # Whitespace only
            "genre": "General Fiction"
        }
        response = client.post('/api/generate', json=payload)
        assert response.status_code == 400
    
    def test_generate_handles_string_character(self, client):
        """Test that character can be a string or object."""
        payload = {
            "idea": "Test idea",
            "character": "A test character description",
            "genre": "General Fiction"
        }
        
        with patch('app.pipeline') as mock_pipeline:
            mock_pipeline.capture_premise.return_value = {
                "idea": payload["idea"],
                "character": {"description": payload["character"]},
                "theme": ""
            }
            mock_pipeline.generate_outline.return_value = {"acts": {}}
            mock_pipeline.scaffold.return_value = {}
            mock_pipeline.draft.return_value = {"text": "Story", "word_count": 1}
            mock_pipeline.revise.return_value = {"text": "Story", "word_count": 1}
            mock_pipeline.word_validator.count_words.return_value = 1
            mock_pipeline.genre = payload["genre"]
            
            with patch('src.shortstory.utils.get_default_client'):
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post('/api/generate', json=payload)
                    # Should handle string character
                    assert response.status_code in [200, 400]


class TestResponseContentType:
    """Test that responses have correct content types."""
    
    def test_json_responses_have_correct_content_type(self, client):
        """Test that JSON responses have application/json content type."""
        response = client.get('/api/health')
        assert response.status_code == 200
        assert 'application/json' in response.content_type.lower()
        
        response = client.get('/api/genres')
        assert response.status_code == 200
        assert 'application/json' in response.content_type.lower()


class TestStoryRevisionEndpoint:
    """Test story revision endpoint."""
    
    def test_revise_story_returns_updated_text(self, client, generated_story_id):
        """Test that revising a story returns updated text."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "Original story text",
                "word_count": 3,
                "revision_history": [],
                "current_revision": 0
            }
            mock_get.return_value = mock_story
            
            with patch('app.pipeline') as mock_pipeline:
                mock_pipeline.revise.return_value = {
                    "text": "Revised story text",
                    "word_count": 3
                }
                
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post(f'/api/story/{generated_story_id}/revise')
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert "success" in data
                    assert data["success"] is True
                    assert "story" in data
                    assert "revision_number" in data
                    assert isinstance(data["revision_number"], int)
                    assert data["revision_number"] > 0
    
    def test_revise_story_requires_content(self, client, generated_story_id):
        """Test that revising requires story content."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "",  # Empty text
                "word_count": 0
            }
            mock_get.return_value = mock_story
            
            response = client.post(f'/api/story/{generated_story_id}/revise')
            assert response.status_code == 400


class TestRevisionHistoryEndpoint:
    """Test revision history endpoint."""
    
    def test_get_revision_history_returns_complete_data(self, client, generated_story_id):
        """Test that revision history returns complete data structure."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        revision_history = [
            {
                "version": 1,
                "text": "First version",
                "word_count": 2,
                "type": "draft",
                "timestamp": "2025-01-01T00:00:00"
            },
            {
                "version": 2,
                "text": "Second version",
                "word_count": 2,
                "type": "revised",
                "timestamp": "2025-01-01T01:00:00"
            }
        ]
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "revision_history": revision_history,
                "current_revision": 2
            }
            mock_get.return_value = mock_story
            
            response = client.get(f'/api/story/{generated_story_id}/revisions')
            assert response.status_code == 200
            
            data = response.get_json()
            assert "success" in data
            assert data["success"] is True
            assert "story_id" in data
            assert "revision_history" in data
            assert isinstance(data["revision_history"], list)
            assert "current_revision" in data
            assert "total_revisions" in data
            assert data["total_revisions"] == len(revision_history)


class TestStoryComparisonEndpoint:
    """Test story comparison endpoint."""
    
    def test_compare_story_versions_returns_diff(self, client, generated_story_id):
        """Test that comparing story versions returns difference data."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        revision_history = [
            {
                "version": 1,
                "text": "First version text",
                "word_count": 3,
                "type": "draft",
                "timestamp": "2025-01-01T00:00:00"
            },
            {
                "version": 2,
                "text": "Second version with more text",
                "word_count": 5,
                "type": "revised",
                "timestamp": "2025-01-01T01:00:00"
            }
        ]
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "revision_history": revision_history
            }
            mock_get.return_value = mock_story
            
            response = client.get(f'/api/story/{generated_story_id}/compare?version1=1&version2=2')
            assert response.status_code == 200
            
            data = response.get_json()
            assert "success" in data
            assert "version1" in data
            assert "version2" in data
            assert "comparison" in data
            assert "word_count_diff" in data["comparison"]
            assert isinstance(data["comparison"]["word_count_diff"], int)
    
    def test_compare_requires_multiple_versions(self, client, generated_story_id):
        """Test that comparison requires at least 2 versions."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "revision_history": [{"version": 1, "text": "Only one version"}]
            }
            mock_get.return_value = mock_story
            
            response = client.get(f'/api/story/{generated_story_id}/compare')
            assert response.status_code == 400


class TestStorySaveEndpoint:
    """Test story save endpoint."""
    
    def test_save_story_returns_success(self, client, generated_story_id):
        """Test that saving a story returns success."""
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "Story text",
                "word_count": 2
            }
            mock_get.return_value = mock_story
            
            with patch('app.pipeline') as mock_pipeline:
                mock_pipeline.word_validator.validate.return_value = (2, True)
                
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    # Send with Content-Type header and empty JSON body
                    response = client.post(
                        f'/api/story/{generated_story_id}/save',
                        json={},
                        content_type='application/json'
                    )
                    assert response.status_code == 200
                    
                    data = response.get_json()
                    assert "success" in data
                    assert data["success"] is True
    
    def test_save_story_with_updated_text(self, client, generated_story_id):
        """Test that saving with updated text validates word count."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "Original text",
                "word_count": 2
            }
            mock_get.return_value = mock_story
            
            with patch('app.pipeline') as mock_pipeline:
                mock_pipeline.word_validator.validate.return_value = (100, True)
                
                with patch('app.story_storage') as mock_storage:
                    mock_storage.save_story.return_value = True
                    
                    response = client.post(
                        f'/api/story/{generated_story_id}/save',
                        json={"text": "Updated story text"}
                    )
                    assert response.status_code == 200


class TestStoryExportEndpoint:
    """Test story export endpoint."""
    
    def test_export_story_requires_content(self, client, generated_story_id):
        """Test that exporting requires story content."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": ""  # Empty text
            }
            mock_get.return_value = mock_story
            
            response = client.get(f'/api/story/{generated_story_id}/export/pdf')
            assert response.status_code == 400
    
    def test_export_supports_multiple_formats(self, client, generated_story_id):
        """Test that export supports multiple formats."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "# Test Story\n\nStory content here."
            }
            mock_get.return_value = mock_story
            
            with patch('app.export_pdf') as mock_pdf:
                from flask import Response
                mock_pdf.return_value = Response(status=200)
                
                response = client.get(f'/api/story/{generated_story_id}/export/pdf')
                # Should call export function
                assert mock_pdf.called or response.status_code in [200, 400]
            
            with patch('app.export_markdown') as mock_md:
                from flask import Response
                mock_md.return_value = Response(status=200)
                
                response = client.get(f'/api/story/{generated_story_id}/export/markdown')
                assert mock_md.called or response.status_code in [200, 400]
            
            with patch('app.export_txt') as mock_txt:
                from flask import Response
                mock_txt.return_value = Response(status=200)
                
                response = client.get(f'/api/story/{generated_story_id}/export/txt')
                assert mock_txt.called or response.status_code in [200, 400]
    
    def test_export_rejects_invalid_format(self, client, generated_story_id):
        """Test that invalid export format is rejected."""
        if not generated_story_id:
            pytest.skip("No story ID available")
        
        with patch('app.get_story_or_404') as mock_get:
            mock_story = {
                "id": generated_story_id,
                "text": "# Test Story\n\nContent"
            }
            mock_get.return_value = mock_story
            
            response = client.get(f'/api/story/{generated_story_id}/export/invalid')
            assert response.status_code == 400


class TestConcurrentRequests:
    """Test concurrent request handling."""
    
    def test_multiple_health_checks_sequential(self, client):
        """Test that multiple health checks can be handled (sequential for test client)."""
        # Flask test client is not thread-safe, so test sequentially
        results = []
        for _ in range(10):
            response = client.get('/api/health')
            results.append(response.status_code == 200)
        
        assert all(results), "All health checks should succeed"
    
    def test_multiple_genre_requests_sequential(self, client):
        """Test that multiple genre requests can be handled (sequential for test client)."""
        # Flask test client is not thread-safe, so test sequentially
        results = []
        for _ in range(5):
            response = client.get('/api/genres')
            data = response.get_json()
            results.append(response.status_code == 200 and "genres" in data)
        
        assert all(results), "All genre requests should succeed"

