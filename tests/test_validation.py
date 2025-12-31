"""
Tests for distinctiveness and validation utilities.
"""

import pytest
from src.shortstory.utils.validation import (
    check_distinctiveness,
    validate_premise,
    detect_cliches,
    detect_generic_archetypes,
    calculate_distinctiveness_score,
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
    """Test premise validation with missing character (now optional)."""
    result = validate_premise("Test idea", None, "Test theme")
    # Character is now optional, so should still be valid
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    # But should have a warning
    assert len(result["warnings"]) > 0
    assert any("character" in w.lower() for w in result["warnings"])


def test_validate_premise_missing_theme():
    """Test premise validation with missing theme (now optional)."""
    result = validate_premise("Test idea", {"name": "Test"}, "")
    # Theme is now optional, so should still be valid
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    # But should have a warning
    assert len(result["warnings"]) > 0
    assert any("theme" in w.lower() for w in result["warnings"])


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
    # With one cliché and one archetype, score should be below 0.85
    assert result["distinctiveness"]["average_score"] < 0.85


def test_check_distinctiveness_cliche_variation():
    """Test that cliché variations are detected."""
    # Test variation: "dark stormy night" (without "and")
    text = "It was a dark stormy night when everything changed."
    result = check_distinctiveness(text)
    assert result["has_cliches"] is True
    assert "dark and stormy night" in result["found_cliches"]


def test_check_distinctiveness_context_aware_dialogue():
    """Test context-aware detection distinguishes dialogue from narrative."""
    # Cliché in dialogue should be detected but with less penalty
    text = 'She said, "It was a dark and stormy night, you know."'
    result = check_distinctiveness(text)
    assert result["has_cliches"] is True
    assert len(result["cliche_details"]) > 0
    # Check that dialogue detection is working
    assert any(detail["in_dialogue"] for detail in result["cliche_details"])


def test_check_distinctiveness_generic_patterns():
    """Test detection of generic language patterns."""
    text = "She felt very sad and really angry. Her heart pounded and eyes widened."
    result = check_distinctiveness(text)
    assert result["generic_pattern_count"] > 0
    assert len(result["generic_patterns"]) > 0
    # Should detect vague intensifiers and overused phrases
    pattern_types = [p["type"] for p in result["generic_patterns"]]
    assert "vague_intensifier" in pattern_types or "overused_phrase" in pattern_types


def test_check_distinctiveness_archetype_variations():
    """Test semantic archetype detection with variations."""
    # Test with variation: "wise mentor" instead of "wise old mentor"
    character = "A wise mentor who teaches the protagonist."
    result = check_distinctiveness(None, character=character)
    assert result["has_generic_archetype"] is True
    assert len(result["generic_elements"]) > 0


def test_check_distinctiveness_archetype_semantic():
    """Test archetype detection using related terms."""
    # Character with multiple related terms should be detected
    character = "An elder guide with prophetic knowledge of the hero's destiny."
    result = check_distinctiveness(None, character=character)
    # Should detect "chosen one" archetype through related terms
    assert result["has_generic_archetype"] is True or result["distinctiveness_score"] < 1.0


def test_check_distinctiveness_word_boundaries():
    """Test that word boundary matching prevents false positives."""
    # "darkness" should not match "dark and stormy night"
    text = "The darkness was overwhelming, but it wasn't a stormy night."
    result = check_distinctiveness(text)
    # Should not detect false positive
    assert "dark and stormy night" not in result["found_cliches"]


def test_check_distinctiveness_enhanced_suggestions():
    """Test that enhanced suggestions are provided."""
    text = "It was very dark. Her heart pounded. She felt sad."
    result = check_distinctiveness(text)
    assert len(result["suggestions"]) > 0
    # Should have suggestions for generic patterns
    suggestions_text = " ".join(result["suggestions"]).lower()
    assert "specific" in suggestions_text or "replace" in suggestions_text


# Tests for separated detection functions

def test_detect_cliches_no_cliches():
    """Test detect_cliches with no clichés."""
    text = "A unique story about a lighthouse keeper."
    result = detect_cliches(text)
    assert result["has_cliches"] is False
    assert result["cliche_count"] == 0
    assert len(result["found_cliches"]) == 0
    assert len(result["cliche_details"]) == 0


def test_detect_cliches_with_cliche():
    """Test detect_cliches that detects clichés."""
    text = "It was a dark and stormy night when the hero arrived."
    result = detect_cliches(text)
    assert result["has_cliches"] is True
    assert result["cliche_count"] > 0
    assert "dark and stormy night" in result["found_cliches"]
    assert len(result["cliche_details"]) > 0
    assert result["cliche_details"][0]["phrase"] == "dark and stormy night"


def test_detect_cliches_dialogue_context():
    """Test that detect_cliches identifies dialogue context."""
    text = 'She said, "It was a dark and stormy night, you know."'
    result = detect_cliches(text)
    assert result["has_cliches"] is True
    # Check that dialogue detection is working
    assert any(detail["in_dialogue"] for detail in result["cliche_details"])


def test_detect_generic_archetypes_no_archetype():
    """Test detect_generic_archetypes with no archetypes."""
    character = "A unique character with specific quirks."
    result = detect_generic_archetypes(character)
    assert result["has_generic_archetype"] is False
    assert len(result["generic_elements"]) == 0
    assert len(result["archetype_details"]) == 0


def test_detect_generic_archetypes_with_archetype():
    """Test detect_generic_archetypes that detects archetypes."""
    character = "A wise old mentor who guides the chosen one."
    result = detect_generic_archetypes(character)
    assert result["has_generic_archetype"] is True
    assert len(result["generic_elements"]) > 0
    assert len(result["archetype_details"]) > 0


def test_detect_generic_archetypes_none():
    """Test detect_generic_archetypes with None input."""
    result = detect_generic_archetypes(None)
    assert result["has_generic_archetype"] is False
    assert len(result["generic_elements"]) == 0


def test_calculate_distinctiveness_score_no_issues():
    """Test calculate_distinctiveness_score with no issues."""
    cliche_results = {"has_cliches": False, "cliche_count": 0, "cliche_details": []}
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score == 1.0


def test_calculate_distinctiveness_score_with_cliche():
    """Test calculate_distinctiveness_score with clichés."""
    cliche_results = {
        "has_cliches": True,
        "cliche_count": 1,
        "cliche_details": [{"in_dialogue": False}]
    }
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < 1.0
    assert score == 0.8  # 1.0 - 0.2 penalty


def test_calculate_distinctiveness_score_with_archetype():
    """Test calculate_distinctiveness_score with archetypes."""
    cliche_results = {"has_cliches": False, "cliche_count": 0, "cliche_details": []}
    archetype_results = {
        "has_generic_archetype": True,
        "generic_elements": ["chosen one"]
    }
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < 1.0
    assert score == 0.7  # 1.0 - 0.3 penalty


def test_calculate_distinctiveness_score_dialogue_penalty():
    """Test that dialogue clichés have less penalty."""
    cliche_results_narrative = {
        "has_cliches": True,
        "cliche_count": 1,
        "cliche_details": [{"in_dialogue": False}]
    }
    cliche_results_dialogue = {
        "has_cliches": True,
        "cliche_count": 1,
        "cliche_details": [{"in_dialogue": True}]
    }
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = []
    
    score_narrative = calculate_distinctiveness_score(
        cliche_results_narrative, archetype_results, pattern_results
    )
    score_dialogue = calculate_distinctiveness_score(
        cliche_results_dialogue, archetype_results, pattern_results
    )
    
    # Dialogue should have less penalty (0.1 vs 0.2)
    assert score_dialogue > score_narrative
    assert score_narrative == 0.8  # 1.0 - 0.2
    assert score_dialogue == 0.9   # 1.0 - 0.1


def test_separation_of_concerns():
    """Test that separated functions work independently."""
    # Test that we can use detect_cliches independently
    text = "It was a dark and stormy night."
    cliche_result = detect_cliches(text)
    assert cliche_result["has_cliches"] is True
    
    # Test that we can use detect_generic_archetypes independently
    character = "A wise old mentor"
    archetype_result = detect_generic_archetypes(character)
    assert archetype_result["has_generic_archetype"] is True
    
    # Test that calculate_distinctiveness_score works with results
    score = calculate_distinctiveness_score(cliche_result, archetype_result, [])
    assert score < 1.0
    
    # Test that check_distinctiveness still works (orchestrator)
    combined_result = check_distinctiveness(text, character=character)
    assert combined_result["has_cliches"] is True
    assert combined_result["has_generic_archetype"] is True
    assert combined_result["distinctiveness_score"] == score

