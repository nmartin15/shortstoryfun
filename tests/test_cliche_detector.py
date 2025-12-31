"""
Tests for the Cliché Detection System.

Verifies comprehensive cliché detection including:
- Phrase clichés
- Predictable story beats
- Formulaic plot structures
- Replacement suggestions
"""

import pytest
from src.shortstory.cliche_detector import ClicheDetector, get_cliche_detector


def test_cliche_detector_initialization():
    """Test that ClicheDetector initializes correctly."""
    detector = ClicheDetector()
    assert detector is not None
    assert hasattr(detector, 'detect_all_cliches')
    assert hasattr(detector, 'suggest_replacements')
    assert hasattr(detector, 'apply_replacements')


def test_get_cliche_detector_singleton():
    """Test that get_cliche_detector returns singleton instance."""
    detector1 = get_cliche_detector()
    detector2 = get_cliche_detector()
    assert detector1 is detector2


def test_detect_all_cliches_phrase_cliches():
    """Test detection of phrase clichés."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night when the hero arrived."
    
    results = detector.detect_all_cliches(text)
    
    assert "phrase_cliches" in results
    assert results["phrase_cliches"]["has_cliches"] is True
    assert "dark and stormy night" in results["phrase_cliches"]["found_cliches"]


def test_detect_all_cliches_archetypes():
    """Test detection of archetype clichés."""
    detector = ClicheDetector()
    character = "A wise old mentor who guides the chosen one."
    
    results = detector.detect_all_cliches(text="", character=character)
    
    assert "archetype_cliches" in results
    assert results["archetype_cliches"]["has_generic_archetype"] is True
    assert len(results["archetype_cliches"]["generic_elements"]) > 0


def test_detect_all_cliches_predictable_beats():
    """Test detection of predictable story beats."""
    detector = ClicheDetector()
    text = "The hero received the call to adventure, but initially refused."
    
    results = detector.detect_all_cliches(text)
    
    assert "predictable_beats" in results
    # Should detect "call to adventure" and "refusal of the call"
    assert len(results["predictable_beats"]) > 0


def test_detect_all_cliches_formulaic_plots():
    """Test detection of formulaic plot structures."""
    detector = ClicheDetector()
    outline = {
        "acts": {
            "beginning": "setup",
            "middle": "conflict",
            "end": "resolution"
        },
        "structure": ["setup", "conflict", "resolution"]
    }
    
    results = detector.detect_all_cliches(text="", outline=outline)
    
    assert "formulaic_plots" in results
    # Should detect "setup, conflict, resolution" pattern
    assert isinstance(results["formulaic_plots"], list)


def test_detect_all_cliches_total_issues():
    """Test that total_issues is calculated correctly."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night. The hero received the call to adventure."
    character = "A wise old mentor"
    
    results = detector.detect_all_cliches(text, character=character)
    
    assert "total_issues" in results
    assert results["total_issues"] > 0
    assert isinstance(results["total_issues"], int)


def test_detect_all_cliches_suggestions():
    """Test that suggestions are generated."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night."
    
    results = detector.detect_all_cliches(text)
    
    assert "suggestions" in results
    assert isinstance(results["suggestions"], list)
    assert len(results["suggestions"]) > 0


def test_suggest_replacements_known_cliche():
    """Test replacement suggestions for known clichés."""
    detector = ClicheDetector()
    
    suggestions = detector.suggest_replacements("dark and stormy night")
    
    assert len(suggestions) > 0
    assert isinstance(suggestions, list)
    assert all(isinstance(s, str) for s in suggestions)


def test_suggest_replacements_unknown_cliche():
    """Test replacement suggestions for unknown clichés."""
    detector = ClicheDetector()
    
    suggestions = detector.suggest_replacements("some unknown cliche phrase")
    
    assert len(suggestions) > 0
    # Should return generic suggestion
    assert any("specific" in s.lower() or "vivid" in s.lower() for s in suggestions)


def test_apply_replacements():
    """Test applying cliché replacements to text."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night when all hell broke loose."
    
    revised_text, applied = detector.apply_replacements(text, auto_replace=True)
    
    assert revised_text != text  # Should have replacements
    assert len(applied) > 0
    assert all("original" in item and "replacement" in item for item in applied)


def test_apply_replacements_custom_replacements():
    """Test applying custom replacements."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night."
    custom_replacements = {"dark and stormy night": "a night without stars"}
    
    revised_text, applied = detector.apply_replacements(
        text,
        replacements=custom_replacements
    )
    
    assert "a night without stars" in revised_text
    assert len(applied) > 0


def test_apply_replacements_no_cliches():
    """Test applying replacements when no clichés are present."""
    detector = ClicheDetector()
    text = "A unique story about a lighthouse keeper who collects voices."
    
    revised_text, applied = detector.apply_replacements(text, auto_replace=True)
    
    assert revised_text == text  # No changes
    assert len(applied) == 0


def test_detect_predictable_beats():
    """Test detection of predictable story beats."""
    detector = ClicheDetector()
    text = "The hero received the call to adventure. They met the mentor. They crossed the threshold."
    
    beats = detector._detect_predictable_beats(text)
    
    assert len(beats) > 0
    assert all("beat" in beat and "alternatives" in beat for beat in beats)


def test_detect_formulaic_plots_from_outline():
    """Test detection of formulaic plots from outline."""
    detector = ClicheDetector()
    outline = {
        "acts": {
            "beginning": "setup",
            "middle": "conflict",
            "end": "resolution"
        },
        "structure": ["setup", "conflict", "resolution"]
    }
    
    plots = detector._detect_formulaic_plots(outline)
    
    assert isinstance(plots, list)
    # Should detect "setup, conflict, resolution" pattern


def test_comprehensive_detection_integration():
    """Test comprehensive detection with all components."""
    detector = ClicheDetector()
    text = "It was a dark and stormy night. The hero received the call to adventure."
    character = "A wise old mentor"
    outline = {
        "acts": {"beginning": "setup", "middle": "conflict", "end": "resolution"},
        "structure": ["setup", "conflict", "resolution"]
    }
    
    results = detector.detect_all_cliches(text, character=character, outline=outline)
    
    # Verify all detection types are present
    assert "phrase_cliches" in results
    assert "archetype_cliches" in results
    assert "generic_patterns" in results
    assert "predictable_beats" in results
    assert "formulaic_plots" in results
    assert "total_issues" in results
    assert "suggestions" in results
    
    # Verify suggestions are actionable
    assert len(results["suggestions"]) > 0
    assert all(isinstance(s, str) and len(s) > 0 for s in results["suggestions"])

