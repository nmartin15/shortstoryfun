"""
Shared pytest fixtures for test suite.

This module provides common fixtures used across multiple test files,
reducing duplication and ensuring consistency.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.genres import get_genre_config
from src.shortstory.providers.gemini import GeminiProvider
# Backward compatibility: LLMClient is now an alias for GeminiProvider
from src.shortstory.utils.llm import LLMClient


# Helper functions for optional dependencies
def check_optional_dependency(module_name: str) -> bool:
    """
    Check if an optional dependency is available.
    
    Args:
        module_name: Name of the module to check (e.g., 'docx', 'ebooklib', 'google.generativeai')
    
    Returns:
        bool: True if the module is available, False otherwise
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def require_optional_dependency(module_name: str):
    """
    Pytest skip decorator for tests requiring optional dependencies.
    
    Args:
        module_name: Name of the module to check
    
    Returns:
        pytest.mark.skipif decorator
    """
    is_available = check_optional_dependency(module_name)
    return pytest.mark.skipif(not is_available, reason=f"Requires {module_name} library")


# Genre configuration fixtures
@pytest.fixture
def general_fiction_config():
    """Get General Fiction genre configuration."""
    return get_genre_config("General Fiction")


@pytest.fixture
def horror_config():
    """Get Horror genre configuration."""
    return get_genre_config("Horror")


@pytest.fixture
def romance_config():
    """Get Romance genre configuration."""
    return get_genre_config("Romance")


@pytest.fixture
def literary_config():
    """Get Literary genre configuration."""
    return get_genre_config("Literary")


# Pipeline fixtures with different stages
@pytest.fixture
def basic_pipeline():
    """Create a basic ShortStoryPipeline instance."""
    return ShortStoryPipeline()


@pytest.fixture
def general_fiction_pipeline(general_fiction_config):
    """Create a pipeline configured for General Fiction."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = general_fiction_config
    return pipeline


@pytest.fixture
def pipeline_with_premise(general_fiction_pipeline):
    """Create a pipeline with a captured premise."""
    premise = general_fiction_pipeline.capture_premise(
        idea="A lighthouse keeper collects lost voices in glass jars",
        character={"name": "Mara", "description": "A quiet keeper with an unusual collection"},
        theme="What happens to the stories we never tell?",
        validate=False
    )
    assert premise is not None, "Premise capture should succeed"
    return general_fiction_pipeline


@pytest.fixture
def pipeline_with_outline(pipeline_with_premise):
    """Create a pipeline with a generated outline."""
    outline = pipeline_with_premise.generate_outline()
    assert outline is not None, "Outline generation should succeed"
    return pipeline_with_premise


@pytest.fixture
def pipeline_with_scaffold(pipeline_with_outline):
    """Create a pipeline with a generated scaffold."""
    scaffold = pipeline_with_outline.scaffold()
    assert scaffold is not None, "Scaffold generation should succeed"
    return pipeline_with_outline


# Test data fixtures
@pytest.fixture
def sample_premise():
    """Sample premise data for testing."""
    return {
        "idea": "A lighthouse keeper collects lost voices in glass jars",
        "character": {"name": "Mara", "description": "A quiet keeper with an unusual collection"},
        "theme": "What happens to the stories we never tell?"
    }


@pytest.fixture
def sample_outline(sample_premise):
    """Sample outline data for testing."""
    return {
        "premise": sample_premise,
        "genre": "General Fiction",
        "framework": "narrative_arc",
        "structure": ["setup", "complication", "resolution"],
        "acts": {
            "beginning": "setup",
            "middle": "complication",
            "end": "resolution"
        }
    }


@pytest.fixture
def sample_character():
    """Sample character data for testing."""
    return {
        "name": "Mara",
        "description": "A lighthouse keeper with an unusual collection",
        "quirks": ["Never speaks above a whisper", "Counts everything in threes"],
        "contradictions": "Fiercely protective but terrified of connection"
    }


# Standardized pipeline setup fixtures - eliminates redundant setup across test classes
@pytest.fixture
def pipeline_with_premise_setup(basic_pipeline, sample_premise):
    """
    Standardized fixture providing pipeline with premise setup.
    
    Returns a tuple of (pipeline, premise) to avoid redundant self.pipeline = basic_pipeline
    pattern in test classes. Use this instead of creating separate setup_pipeline fixtures.
    """
    pipeline = basic_pipeline
    pipeline.premise = sample_premise
    return pipeline, sample_premise


@pytest.fixture
def pipeline_with_outline_setup(basic_pipeline, sample_premise, sample_outline):
    """
    Standardized fixture providing pipeline with premise and outline setup.
    
    Returns a tuple of (pipeline, premise, outline) to avoid redundant setup patterns.
    """
    pipeline = basic_pipeline
    pipeline.premise = sample_premise
    pipeline.outline = sample_outline
    return pipeline, sample_premise, sample_outline


# ============================================================================
# Standardized Mocking Utilities
# ============================================================================
# These fixtures and helpers provide consistent mocking patterns across all tests,
# eliminating the need for duplicate mock_client fixtures and inconsistent mocking strategies.
#
# Mocking Strategy:
# 1. Use fixtures (mock_llm_client, mock_pipeline, mock_redis) for common mocks
# 2. Use helper functions (create_mock_pipeline_with_story) for parameterized mocks
# 3. Use @patch decorators for module-level patching
# 4. Use context managers (with patch(...)) for scoped patching
#
# Migration Guide:
# - Replace duplicate mock_client fixtures with mock_llm_client fixture
# - Replace inline MagicMock() pipeline creation with mock_pipeline fixture or create_mock_pipeline_with_story()
# - Replace duplicate Redis mocking with mock_redis fixture

@pytest.fixture
def mock_llm_client():
    """
    Standardized fixture for mocking LLM client.
    
    This fixture provides a consistent way to mock the LLM client across all tests.
    It handles:
    - Environment variable patching (GOOGLE_API_KEY)
    - google.generativeai module patching
    - Model and response mocking
    
    Usage:
        def test_something(mock_llm_client):
            result = mock_llm_client.generate("prompt")
            assert result == "Generated story text"
    """
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Generated story text"
                mock_model.generate_content.return_value = mock_response
                mock_model_class.return_value = mock_model
                
                # Use GeminiProvider directly for mocking
                client = GeminiProvider(api_key="test_key")
                # Store mocks for test verification if needed
                client._mock_model = mock_model
                client._mock_model_class = mock_model_class
                yield client


@pytest.fixture
def mock_pipeline():
    """
    Standardized fixture for mocking pipeline instance.
    
    Returns a MagicMock configured with common pipeline methods and return values.
    Use this instead of creating inline MagicMock() instances for pipelines.
    
    Usage:
        def test_something(mock_pipeline):
            with patch('app.get_pipeline', return_value=mock_pipeline):
                # test code
    """
    pipeline = MagicMock()
    # Set up common return values
    pipeline.capture_premise.return_value = {
        "idea": "Test idea",
        "character": {"name": "Test"},
        "theme": "Test theme"
    }
    pipeline.generate_outline.return_value = {
        "genre": "General Fiction",
        "framework": "narrative_arc",
        "structure": ["setup", "complication", "resolution"],
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    pipeline.scaffold.return_value = {
        "tone": "balanced",
        "pace": "moderate",
        "pov": "third person"
    }
    pipeline.draft.return_value = {
        "text": "Test story text",
        "word_count": 100
    }
    pipeline.revise.return_value = {
        "text": "Revised test story text",
        "word_count": 120
    }
    # Mock word_validator
    pipeline.word_validator = MagicMock()
    pipeline.word_validator.count_words.return_value = 100
    pipeline.genre = "General Fiction"
    return pipeline


@pytest.fixture
def mock_redis():
    """
    Standardized fixture for mocking Redis cache.
    
    Returns a tuple of (mock_redis_module, mock_redis_instance) for consistent
    Redis mocking across tests.
    
    Usage:
        def test_something(mock_redis):
            mock_redis_module, mock_redis_instance = mock_redis
            with patch.dict('sys.modules', {'redis': mock_redis_module}):
                # test code
    """
    mock_redis_module = MagicMock()
    mock_redis_instance = MagicMock()
    mock_redis_module.from_url.return_value = mock_redis_instance
    return mock_redis_module, mock_redis_instance


def create_mock_pipeline_with_story(story_payload):
    """
    Helper function to create a mock pipeline configured for a specific story payload.
    
    Args:
        story_payload: Dictionary containing story generation parameters
        
    Returns:
        MagicMock pipeline instance configured with the story payload
        
    Usage:
        mock_pipeline = create_mock_pipeline_with_story(sample_story_payload)
        with patch('app.get_pipeline', return_value=mock_pipeline):
            # test code
    """
    pipeline = MagicMock()
    pipeline.capture_premise.return_value = story_payload
    pipeline.generate_outline.return_value = {
        "genre": story_payload.get("genre", "General Fiction"),
        "framework": "narrative_arc",
        "structure": ["setup", "complication", "resolution"],
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    pipeline.scaffold.return_value = {
        "tone": "balanced",
        "pace": "moderate",
        "pov": "third person"
    }
    pipeline.draft.return_value = {
        "text": "Generated story text",
        "word_count": 100
    }
    pipeline.revise.return_value = {
        "text": "Revised story text",
        "word_count": 120
    }
    pipeline.word_validator = MagicMock()
    pipeline.word_validator.count_words.return_value = 100
    pipeline.genre = story_payload.get("genre", "General Fiction")
    return pipeline

