"""
Unit tests for ShortStoryPipeline
"""

import pytest
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.utils.word_count import WordCountError


def test_pipeline_initialization():
    """Test that pipeline initializes correctly."""
    pipeline = ShortStoryPipeline()
    assert pipeline.premise is None
    assert pipeline.outline is None
    assert pipeline.scaffold is None
    assert pipeline.draft is None
    assert pipeline.revised_draft is None
    assert pipeline.word_validator is not None


def test_premise_capture():
    """Test premise capture stage."""
    pipeline = ShortStoryPipeline()
    premise = pipeline.capture_premise(
        idea="A lighthouse keeper collects voices",
        character={"name": "Mara", "quirk": "Whispers only"},
        theme="Untold stories",
        validate=False  # Skip validation for simple test
    )
    assert premise is not None
    assert premise["idea"] == "A lighthouse keeper collects voices"


def test_premise_capture_with_validation():
    """Test premise capture with validation."""
    pipeline = ShortStoryPipeline()
    premise = pipeline.capture_premise(
        idea="A unique story about collecting lost voices",
        character={"name": "Mara", "quirk": "Never speaks above a whisper"},
        theme="What happens to stories we never tell?",
        validate=True
    )
    assert premise is not None
    assert premise["validation"] is not None
    assert premise["validation"]["is_valid"] is True


def test_premise_capture_validation_fails():
    """Test that premise capture raises error on invalid premise."""
    pipeline = ShortStoryPipeline()
    with pytest.raises(ValueError):
        pipeline.capture_premise(
            idea="",  # Missing idea
            character={"name": "Test"},
            theme="Test theme",
            validate=True
        )

