"""
Tests for distinctiveness and validation utilities.
"""

import pytest
from src.shortstory.utils.validation import (
    check_distinctiveness,
    validate_premise,
    COMMON_CLICHES,
    GENERIC_ARCHETYPES,
)


def test_check_distinctiveness_no_cliches():
    """Test distinctiveness check with no clichés."""
    text = "A unique story about a lighthouse keeper who collects voices."
    result = check_distinctiveness(text)
    assert result["has_cliches"] is False
    assert result["cliche_count"] == 0
    assert result["distinctiveness_score"] > 0.8


def test_check_distinctiveness_with_cliche():
    """Test distinctiveness check that detects clichés."""
    text = "It was a dark and stormy night when the hero arrived."
    result = check_distinctiveness(text)
    assert result["has_cliches"] is True
    assert result["cliche_count"] > 0
    assert "dark and stormy night" in result["found_cliches"]
    assert result["distinctiveness_score"] < 1.0


def test_check_distinctiveness_generic_archetype():
    """Test distinctiveness check with generic character archetype."""
    character = "A wise old mentor who guides the chosen one."
    result = check_distinctiveness(None, character=character)
    assert result["has_generic_archetype"] is True
    assert len(result["generic_elements"]) > 0
    assert result["distinctiveness_score"] < 1.0


def test_validate_premise_complete():
    """Test premise validation with complete inputs."""
    idea = "A lighthouse keeper collects lost voices in glass jars."
    character = {"name": "Mara", "quirk": "Never speaks above a whisper"}
    theme = "What happens to stories we never tell?"
    
    result = validate_premise(idea, character, theme)
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    assert result["completeness"]["has_idea"] is True
    assert result["completeness"]["has_character"] is True
    assert result["completeness"]["has_theme"] is True


def test_validate_premise_missing_idea():
    """Test premise validation with missing idea."""
    result = validate_premise("", {"name": "Test"}, "Test theme")
    assert result["is_valid"] is False
    assert "idea" in str(result["errors"][0]).lower()


def test_validate_premise_missing_character():
    """Test premise validation with missing character."""
    result = validate_premise("Test idea", None, "Test theme")
    assert result["is_valid"] is False
    assert "character" in str(result["errors"][0]).lower()


def test_validate_premise_missing_theme():
    """Test premise validation with missing theme."""
    result = validate_premise("Test idea", {"name": "Test"}, "")
    assert result["is_valid"] is False
    assert "theme" in str(result["errors"][0]).lower()


def test_validate_premise_low_distinctiveness():
    """Test premise validation with low distinctiveness score."""
    idea = "It was a dark and stormy night."
    character = "A wise old mentor"
    theme = "Good versus evil"
    
    result = validate_premise(idea, character, theme)
    # Should still be valid (has all required fields)
    assert result["is_valid"] is True
    # But should have warnings
    assert len(result["warnings"]) > 0
    assert result["distinctiveness"]["average_score"] < 0.7

