"""
Helper utilities for consistent mocking strategy in tests.

This module provides fixtures and helpers to ensure all tests use a consistent
approach to mocking external dependencies, addressing the issue:
"Inconsistent Mocking Strategy for External Dependencies"

Standard Approach:
- Always mock factory/getter functions: `app.get_pipeline()` and `app.get_story_repository()`
- Never mock module-level instances directly: `app.pipeline` or `app.story_storage`
- This ensures tests reflect the actual code execution path and are more resilient to refactoring
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Generator, Tuple


@pytest.fixture
def mock_pipeline_and_repository():
    """
    Standardized fixture for mocking pipeline and repository dependencies.
    
    This fixture provides a consistent way to mock app.get_pipeline() and
    app.get_story_repository() across all tests.
    
    Yields:
        Tuple of (mock_pipeline_instance, mock_repository_instance, context_manager)
        The context_manager should be used in a 'with' statement to activate the mocks.
    
    Example:
        def test_something(self, mock_pipeline_and_repository):
            mock_pipeline, mock_repo, mock_context = mock_pipeline_and_repository
            
            with mock_context:
                # Your test code here
                # mock_pipeline and mock_repo are already configured
                pass
    """
    mock_pipeline_instance = MagicMock()
    mock_repo_instance = MagicMock()
    
    # Create context manager that patches both getters
    context_manager = patch.multiple(
        'app',
        get_pipeline=MagicMock(return_value=mock_pipeline_instance),
        get_story_repository=MagicMock(return_value=mock_repo_instance)
    )
    
    yield mock_pipeline_instance, mock_repo_instance, context_manager


@pytest.fixture
def configured_mock_pipeline():
    """
    Create a mock pipeline instance with common method return values pre-configured.
    
    This fixture sets up a mock pipeline with typical return values for common
    pipeline methods, reducing boilerplate in tests.
    
    Returns:
        MagicMock: Configured mock pipeline instance
    """
    mock_pipeline = MagicMock()
    
    # Configure common return values
    mock_pipeline.capture_premise.return_value = {
        "idea": "Test idea",
        "character": {"name": "Test", "description": "Test character"},
        "theme": "Test theme"
    }
    mock_pipeline.generate_outline.return_value = {
        "genre": "General Fiction",
        "framework": "narrative_arc",
        "structure": ["setup", "complication", "resolution"],
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    mock_pipeline.scaffold.return_value = {
        "tone": "balanced",
        "pace": "moderate",
        "pov": "third person",
        "voice": "developed"
    }
    mock_pipeline.draft.return_value = {
        "text": "Test story text",
        "word_count": 10
    }
    mock_pipeline.revise.return_value = {
        "text": "Revised test story text",
        "word_count": 12
    }
    
    # Mock word_validator
    mock_pipeline.word_validator = MagicMock()
    mock_pipeline.word_validator.count_words.return_value = 10
    
    return mock_pipeline


@pytest.fixture
def configured_mock_repository():
    """
    Create a mock repository instance with common method return values pre-configured.
    
    Returns:
        MagicMock: Configured mock repository instance
    """
    mock_repo = MagicMock()
    mock_repo.save.return_value = True
    mock_repo.load.return_value = None  # Override in tests as needed
    mock_repo.list.return_value = ([], {"page": 1, "per_page": 10, "total": 0})
    mock_repo.count.return_value = 0
    return mock_repo


# Context manager helper for consistent mocking pattern
class MockPipelineAndRepository:
    """
    Context manager for consistently mocking pipeline and repository.
    
    Usage:
        with MockPipelineAndRepository() as (mock_pipeline, mock_repo):
            # Your test code
            pass
    """
    
    def __init__(self):
        self.mock_pipeline = MagicMock()
        self.mock_repo = MagicMock()
        self.patches = None
    
    def __enter__(self) -> Tuple[MagicMock, MagicMock]:
        self.patches = patch.multiple(
            'app',
            get_pipeline=MagicMock(return_value=self.mock_pipeline),
            get_story_repository=MagicMock(return_value=self.mock_repo)
        )
        self.patches.__enter__()
        return self.mock_pipeline, self.mock_repo
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.patches:
            self.patches.__exit__(exc_type, exc_val, exc_tb)

