"""
Tests for validation utilities.
"""

import pytest
from src.shortstory.utils.validation import (
    validate_premise,
    check_distinctiveness,
    calculate_distinctiveness_score,
    detect_cliches,
    detect_generic_archetypes,
    detect_generic_patterns_from_text,
    _detect_generic_patterns,
    _generate_suggestions,
)

# Constants for distinctiveness score penalties based on actual implementation
# These match the values in src/shortstory/utils/validation.py calculate_distinctiveness_score()
CLICHE_PENALTY_PER_CLICHE = 0.1  # Each cliché reduces score by 0.1
MAX_CLICHE_PENALTY = 0.4  # Maximum total penalty for clichés
ARCHETYPE_PENALTY = 0.3  # Fixed penalty for generic archetypes
PATTERN_PENALTY_PER_PATTERN = 0.05  # Each pattern reduces score by 0.05
MAX_PATTERN_PENALTY = 0.3  # Maximum total penalty for patterns
PERFECT_SCORE = 1.0  # Perfect distinctiveness score

# Expected error message constants for more robust assertions
EXPECTED_IDEA_ERROR_KEYWORDS = ["idea", "required", "empty", "missing"]


def test_validate_premise_missing_idea():
    """Test premise validation with missing idea."""
    result = validate_premise("", {"name": "Test"}, "Test theme")
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    # More robust check: assert on error message keywords rather than exact string
    error_messages = " ".join(result["errors"]).lower()
    assert any(keyword in error_messages for keyword in EXPECTED_IDEA_ERROR_KEYWORDS), \
        f"Expected error message to contain one of {EXPECTED_IDEA_ERROR_KEYWORDS}, got: {result['errors']}"


def test_check_distinctiveness_no_cliches():
    """Test distinctiveness check with no clichés."""
    text = "A unique story about a lighthouse keeper who collects voices."
    result = check_distinctiveness(text)
    assert result["has_cliches"] is False
    assert result["cliche_count"] == 0
    assert result["distinctiveness_score"] == PERFECT_SCORE


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
    assert score < PERFECT_SCORE
    # 1 cliché = 0.1 penalty, so score should be 1.0 - 0.1 = 0.9
    expected_score = PERFECT_SCORE - (1 * CLICHE_PENALTY_PER_CLICHE)
    assert score == expected_score, \
        f"Expected score {expected_score} for 1 cliché, got {score}"


def test_calculate_distinctiveness_score_with_two_cliches():
    """Test calculate_distinctiveness_score with multiple clichés."""
    cliche_results = {
        "has_cliches": True,
        "cliche_count": 2,
        "cliche_details": [{"in_dialogue": False}, {"in_dialogue": False}]
    }
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < PERFECT_SCORE
    # 2 clichés = 0.2 penalty, so score should be 1.0 - 0.2 = 0.8
    expected_score = PERFECT_SCORE - (2 * CLICHE_PENALTY_PER_CLICHE)
    assert score == expected_score, \
        f"Expected score {expected_score} for 2 clichés, got {score}"


def test_calculate_distinctiveness_score_with_archetype():
    """Test calculate_distinctiveness_score with archetypes."""
    cliche_results = {"has_cliches": False, "cliche_count": 0, "cliche_details": []}
    archetype_results = {
        "has_generic_archetype": True,
        "generic_elements": ["chosen one"]
    }
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < PERFECT_SCORE
    # Archetype penalty is 0.3, so score should be 1.0 - 0.3 = 0.7
    expected_score = PERFECT_SCORE - ARCHETYPE_PENALTY
    assert score == expected_score, \
        f"Expected score {expected_score} for archetype, got {score}"


def test_calculate_distinctiveness_score_with_patterns():
    """Test calculate_distinctiveness_score with generic patterns."""
    cliche_results = {"has_cliches": False, "cliche_count": 0, "cliche_details": []}
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = [
        {"type": "generic_pattern_1"},
        {"type": "generic_pattern_2"}
    ]
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < PERFECT_SCORE
    # 2 patterns = 0.1 penalty (2 * 0.05), so score should be 1.0 - 0.1 = 0.9
    expected_score = PERFECT_SCORE - (2 * PATTERN_PENALTY_PER_PATTERN)
    assert score == expected_score, \
        f"Expected score {expected_score} for 2 patterns, got {score}"


def test_calculate_distinctiveness_score_combined_penalties():
    """Test calculate_distinctiveness_score with multiple penalty types."""
    cliche_results = {
        "has_cliches": True,
        "cliche_count": 1,
        "cliche_details": [{"in_dialogue": False}]
    }
    archetype_results = {
        "has_generic_archetype": True,
        "generic_elements": ["wise mentor"]
    }
    pattern_results = [{"type": "generic_pattern"}]
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score < PERFECT_SCORE
    # Combined: 1 cliché (0.1) + archetype (0.3) + 1 pattern (0.05) = 0.45 penalty
    expected_score = PERFECT_SCORE - CLICHE_PENALTY_PER_CLICHE - ARCHETYPE_PENALTY - PATTERN_PENALTY_PER_PATTERN
    assert score == expected_score, \
        f"Expected score {expected_score} for combined penalties, got {score}"


def test_calculate_distinctiveness_score_max_cliche_penalty():
    """Test that cliché penalty is capped at maximum."""
    cliche_results = {
        "has_cliches": True,
        "cliche_count": 10,  # More than would trigger max penalty
        "cliche_details": [{"in_dialogue": False}] * 10
    }
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    # Should be capped at MAX_CLICHE_PENALTY (0.4), not 10 * 0.1 = 1.0
    expected_score = PERFECT_SCORE - MAX_CLICHE_PENALTY
    assert score == expected_score, \
        f"Expected score {expected_score} for max cliché penalty, got {score}"


def test_calculate_distinctiveness_score_max_pattern_penalty():
    """Test that pattern penalty is capped at maximum."""
    cliche_results = {"has_cliches": False, "cliche_count": 0, "cliche_details": []}
    archetype_results = {"has_generic_archetype": False, "generic_elements": []}
    pattern_results = [{"type": f"pattern_{i}"} for i in range(10)]  # More than would trigger max penalty
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    # Should be capped at MAX_PATTERN_PENALTY (0.3), not 10 * 0.05 = 0.5
    expected_score = PERFECT_SCORE - MAX_PATTERN_PENALTY
    assert score == expected_score, \
        f"Expected score {expected_score} for max pattern penalty, got {score}"


def test_calculate_distinctiveness_score_never_negative():
    """Test that distinctiveness score never goes below 0.0."""
    cliche_results = {
        "has_cliches": True,
        "cliche_count": 20,  # Would exceed 1.0 if not capped
        "cliche_details": [{"in_dialogue": False}] * 20
    }
    archetype_results = {
        "has_generic_archetype": True,
        "generic_elements": ["chosen one"]
    }
    pattern_results = [{"type": f"pattern_{i}"} for i in range(20)]
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    assert score >= 0.0, f"Score should never be negative, got {score}"
    assert score <= PERFECT_SCORE, f"Score should never exceed {PERFECT_SCORE}, got {score}"


class TestGenerateSuggestions:
    """Test suite for _generate_suggestions private helper function."""
    
    def test_generate_suggestions_with_cliches(self):
        """Test _generate_suggestions with cliché details."""
        cliche_results = {
            "cliche_details": [
                {"suggestion": "Replace clichéd phrase 'dark and stormy night'"},
                {"suggestion": "Replace clichéd phrase 'once upon a time'"},
                {"suggestion": "Replace clichéd phrase 'little did they know'"},
                {"suggestion": "Replace clichéd phrase 'in that moment'"}  # Should be limited to 3
            ]
        }
        archetype_results = {"generic_elements": []}
        pattern_results = []
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 3, "Should limit to first 3 cliché suggestions"
        assert "dark and stormy night" in suggestions[0]
        assert "once upon a time" in suggestions[1]
        assert "little did they know" in suggestions[2]
    
    def test_generate_suggestions_with_archetypes(self):
        """Test _generate_suggestions with generic archetypes."""
        cliche_results = {"cliche_details": []}
        archetype_results = {
            "generic_elements": ["chosen one", "wise mentor", "damsel in distress", "evil overlord"]
        }
        pattern_results = []
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 1
        assert "chosen one" in suggestions[0]
        assert "wise mentor" in suggestions[0]
        assert "damsel in distress" in suggestions[0]
        assert "evil overlord" not in suggestions[0], "Should limit to first 3 archetypes"
    
    def test_generate_suggestions_with_patterns(self):
        """Test _generate_suggestions with generic patterns."""
        cliche_results = {"cliche_details": []}
        archetype_results = {"generic_elements": []}
        pattern_results = [
            {"suggestion": "Replace 'very' with a more specific descriptor"},
            {"suggestion": "Replace overused phrase 'it was then that'"},
            {"suggestion": "Replace stock phrase 'she knew'"},
            {"suggestion": "Replace vague intensifier 'really'"}  # Should be limited to 3
        ]
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 3, "Should limit to first 3 pattern suggestions"
        assert "very" in suggestions[0]
        assert "it was then that" in suggestions[1]
        assert "she knew" in suggestions[2]
    
    def test_generate_suggestions_combined(self):
        """Test _generate_suggestions with all types of results."""
        cliche_results = {
            "cliche_details": [
                {"suggestion": "Replace clichéd phrase 'dark and stormy night'"}
            ]
        }
        archetype_results = {
            "generic_elements": ["chosen one", "wise mentor"]
        }
        pattern_results = [
            {"suggestion": "Replace 'very' with a more specific descriptor"}
        ]
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 3
        assert any("dark and stormy night" in s for s in suggestions)
        assert any("chosen one" in s for s in suggestions)
        assert any("very" in s for s in suggestions)
    
    def test_generate_suggestions_empty_results(self):
        """Test _generate_suggestions with empty results."""
        cliche_results = {"cliche_details": []}
        archetype_results = {"generic_elements": []}
        pattern_results = []
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0
    
    def test_generate_suggestions_missing_keys(self):
        """Test _generate_suggestions handles missing dictionary keys gracefully."""
        cliche_results = {}  # Missing 'cliche_details'
        archetype_results = {}  # Missing 'generic_elements'
        pattern_results = []
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0
    
    def test_generate_suggestions_cliche_details_without_suggestion_key(self):
        """Test _generate_suggestions skips cliché details without 'suggestion' key."""
        cliche_results = {
            "cliche_details": [
                {"phrase": "dark and stormy night", "in_dialogue": False},  # No 'suggestion' key
                {"suggestion": "Replace clichéd phrase 'once upon a time'"}
            ]
        }
        archetype_results = {"generic_elements": []}
        pattern_results = []
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 1
        assert "once upon a time" in suggestions[0]
    
    def test_generate_suggestions_patterns_without_suggestion_key(self):
        """Test _generate_suggestions skips patterns without 'suggestion' key."""
        cliche_results = {"cliche_details": []}
        archetype_results = {"generic_elements": []}
        pattern_results = [
            {"type": "vague_intensifier", "pattern": "very"},  # No 'suggestion' key
            {"suggestion": "Replace 'really' with a more specific descriptor"}
        ]
        
        suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 1
        assert "really" in suggestions[0]


class TestDetectCliches:
    """Test suite for detect_cliches function."""
    
    def test_detect_cliches_with_cliche(self):
        """Test detect_cliches finds clichés in text."""
        text = "It was a dark and stormy night when the hero arrived."
        result = detect_cliches(text)
        
        assert result["has_cliches"] is True
        assert result["cliche_count"] > 0
        assert len(result["found_cliches"]) > 0
        assert "it was a dark and stormy night" in [c.lower() for c in result["found_cliches"]]
        assert len(result["cliche_details"]) > 0
    
    def test_detect_cliches_no_cliches(self):
        """Test detect_cliches with no clichés."""
        text = "A unique story about a lighthouse keeper who collects voices."
        result = detect_cliches(text)
        
        assert result["has_cliches"] is False
        assert result["cliche_count"] == 0
        assert len(result["found_cliches"]) == 0
        assert len(result["cliche_details"]) == 0
    
    def test_detect_cliches_empty_string(self):
        """Test detect_cliches with empty string."""
        result = detect_cliches("")
        
        assert result["has_cliches"] is False
        assert result["cliche_count"] == 0
        assert len(result["found_cliches"]) == 0
        assert len(result["cliche_details"]) == 0
    
    def test_detect_cliches_none(self):
        """Test detect_cliches with None."""
        result = detect_cliches(None)
        
        assert result["has_cliches"] is False
        assert result["cliche_count"] == 0
        assert len(result["found_cliches"]) == 0
        assert len(result["cliche_details"]) == 0
    
    def test_detect_cliches_multiple_cliches(self):
        """Test detect_cliches finds multiple clichés."""
        text = "Once upon a time, little did they know, it was then that everything changed."
        result = detect_cliches(text)
        
        assert result["has_cliches"] is True
        assert result["cliche_count"] >= 2
        assert len(result["found_cliches"]) >= 2
    
    def test_detect_cliches_case_insensitive(self):
        """Test detect_cliches is case insensitive."""
        text = "IT WAS A DARK AND STORMY NIGHT"
        result = detect_cliches(text)
        
        assert result["has_cliches"] is True
        assert result["cliche_count"] > 0
    
    def test_detect_cliches_word_boundaries(self):
        """Test detect_cliches respects word boundaries."""
        # "dark and stormy" should not match "darkandstormy"
        text = "It was a darkandstormy night"
        result = detect_cliches(text)
        
        # Should not match because of word boundaries
        assert "it was a dark and stormy night" not in [c.lower() for c in result.get("found_cliches", [])]


class TestDetectGenericArchetypes:
    """Test suite for detect_generic_archetypes function."""
    
    def test_detect_generic_archetypes_with_archetype(self):
        """Test detect_generic_archetypes finds generic archetypes."""
        character = {
            "name": "Hero",
            "description": "The chosen one who must save the world"
        }
        result = detect_generic_archetypes(character)
        
        assert result["has_generic_archetype"] is True
        assert len(result["generic_elements"]) > 0
        assert "chosen one" in [e.lower() for e in result["generic_elements"]]
    
    def test_detect_generic_archetypes_no_archetype(self):
        """Test detect_generic_archetypes with no generic archetypes."""
        character = {
            "name": "Mara",
            "description": "A quiet lighthouse keeper who collects lost voices in glass jars"
        }
        result = detect_generic_archetypes(character)
        
        assert result["has_generic_archetype"] is False
        assert len(result["generic_elements"]) == 0
    
    def test_detect_generic_archetypes_none(self):
        """Test detect_generic_archetypes with None."""
        result = detect_generic_archetypes(None)
        
        assert result["has_generic_archetype"] is False
        assert len(result["generic_elements"]) == 0
    
    def test_detect_generic_archetypes_empty_dict(self):
        """Test detect_generic_archetypes with empty dict."""
        result = detect_generic_archetypes({})
        
        assert result["has_generic_archetype"] is False
        assert len(result["generic_elements"]) == 0
    
    def test_detect_generic_archetypes_string_description(self):
        """Test detect_generic_archetypes with string description."""
        character = "The wise old mentor who guides the hero"
        result = detect_generic_archetypes(character)
        
        assert result["has_generic_archetype"] is True
        assert len(result["generic_elements"]) > 0
        assert "wise old mentor" in [e.lower() for e in result["generic_elements"]]
    
    def test_detect_generic_archetypes_multiple_archetypes(self):
        """Test detect_generic_archetypes finds multiple archetypes."""
        character = {
            "name": "Hero",
            "description": "The chosen one, a reluctant hero, destined to save the world"
        }
        result = detect_generic_archetypes(character)
        
        assert result["has_generic_archetype"] is True
        assert len(result["generic_elements"]) >= 2
    
    def test_detect_generic_archetypes_case_insensitive(self):
        """Test detect_generic_archetypes is case insensitive."""
        character = {
            "name": "Hero",
            "description": "THE CHOSEN ONE"
        }
        result = detect_generic_archetypes(character)
        
        assert result["has_generic_archetype"] is True
        assert len(result["generic_elements"]) > 0


class TestDetectGenericPatterns:
    """Test suite for detect_generic_patterns_from_text and _detect_generic_patterns functions."""
    
    def test_detect_generic_patterns_vague_intensifiers(self):
        """Test detect_generic_patterns_from_text finds vague intensifiers."""
        text = "She was very tired and really sad."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        vague_intensifiers = [p for p in result if p["type"] == "vague_intensifier"]
        assert len(vague_intensifiers) >= 2
        assert any(p["pattern"] == "very" for p in vague_intensifiers)
        assert any(p["pattern"] == "really" for p in vague_intensifiers)
    
    def test_detect_generic_patterns_overused_phrases(self):
        """Test detect_generic_patterns_from_text finds overused phrases."""
        text = "It was then that she knew. Little did they know what was coming."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        overused = [p for p in result if p["type"] == "overused_phrase"]
        assert len(overused) >= 2
        assert any("it was then that" in p["pattern"] for p in overused)
        assert any("little did they know" in p["pattern"] for p in overused)
    
    def test_detect_generic_patterns_stock_phrases(self):
        """Test detect_generic_patterns_from_text finds stock phrases."""
        text = "She knew something was wrong. He realized the truth. Suddenly, everything changed."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        stock = [p for p in result if p["type"] == "stock_phrase"]
        assert len(stock) >= 2
        assert any("she knew" in p["pattern"] for p in stock)
        assert any("he realized" in p["pattern"] for p in stock)
        assert any("suddenly" in p["pattern"] for p in stock)
    
    def test_detect_generic_patterns_no_patterns(self):
        """Test detect_generic_patterns_from_text with no generic patterns."""
        text = "A unique story about a lighthouse keeper who collects voices in glass jars."
        result = detect_generic_patterns_from_text(text)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_detect_generic_patterns_empty_string(self):
        """Test detect_generic_patterns_from_text with empty string."""
        result = detect_generic_patterns_from_text("")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_detect_generic_patterns_none(self):
        """Test detect_generic_patterns_from_text with None."""
        result = detect_generic_patterns_from_text(None)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_detect_generic_patterns_non_string(self):
        """Test detect_generic_patterns_from_text converts non-string to string."""
        result = detect_generic_patterns_from_text(123)
        
        assert isinstance(result, list)
        # Should not crash, but may or may not find patterns
    
    def test_detect_generic_patterns_all_types(self):
        """Test detect_generic_patterns_from_text finds all pattern types."""
        text = "She felt very sad. Her heart pounded. It was then that she knew."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        types = [p["type"] for p in result]
        assert "vague_intensifier" in types
        assert "overused_phrase" in types
        assert "stock_phrase" in types
    
    def test_detect_generic_patterns_suggestions(self):
        """Test detect_generic_patterns_from_text includes suggestions."""
        text = "She was very tired."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        for pattern in result:
            assert "suggestion" in pattern
            assert isinstance(pattern["suggestion"], str)
            assert len(pattern["suggestion"]) > 0
    
    def test_detect_generic_patterns_in_dialogue_flag(self):
        """Test detect_generic_patterns_from_text includes in_dialogue flag."""
        text = "She was very tired."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        for pattern in result:
            assert "in_dialogue" in pattern
            assert isinstance(pattern["in_dialogue"], bool)
    
    def test_detect_generic_patterns_private_alias(self):
        """Test _detect_generic_patterns (deprecated alias) works correctly."""
        text = "She was very tired. Her heart pounded."
        text_lower = text.lower()
        
        # Test the deprecated private function
        result = _detect_generic_patterns(text, text_lower)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should return same results as public function
        public_result = detect_generic_patterns_from_text(text)
        assert len(result) == len(public_result)
    
    def test_detect_generic_patterns_start_of_string(self):
        """Test detect_generic_patterns_from_text finds patterns at start of string."""
        text = "Very tired, she walked home."
        result = detect_generic_patterns_from_text(text)
        
        assert len(result) > 0
        assert any(p["pattern"] == "very" for p in result)
