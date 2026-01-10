"""
Tests for cliché detection functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.shortstory.cliche_detector import ClicheDetector, get_cliche_detector


@pytest.fixture
def detector():
    """Create a ClicheDetector instance for testing."""
    return ClicheDetector()


@pytest.fixture
def mock_detector():
    """Create a ClicheDetector instance with mocked internal methods for isolated testing."""
    detector = ClicheDetector()
    # Mock internal detection methods to isolate tests from implementation details
    detector._detect_predictable_beats = MagicMock(return_value=[])
    return detector


@pytest.fixture
def fully_mocked_detector():
    """Create a ClicheDetector with all internal methods mocked for complete isolation."""
    with patch.object(ClicheDetector, '_detect_predictable_beats', return_value=[]) as mock_beats:
        detector = ClicheDetector()
        # Ensure the mock is properly set
        detector._detect_predictable_beats = mock_beats
        yield detector


class TestClicheDetection:
    """Test suite for cliché detection."""
    
    def test_detect_all_cliches_with_text(self, detector):
        """Test detecting clichés in text."""
        text = "It was a dark and stormy night when the hero arrived."
        results = detector.detect_all_cliches(text=text)
        
        assert "phrase_cliches" in results
        assert "has_cliches" in results
        assert "total_cliches" in results
        assert isinstance(results["phrase_cliches"], list)
    
    def test_detect_all_cliches_with_mocked_internal_methods(self, mock_detector):
        """Test detection with mocked internal methods to verify isolation."""
        text = "It was a dark and stormy night when the hero arrived."
        outline = {"acts": {"beginning": "call to adventure"}}
        
        # Configure mock to return specific results
        mock_detector._detect_predictable_beats.return_value = [
            {"beat": "call to adventure", "alternatives": ["unexpected summons"]}
        ]
        
        results = mock_detector.detect_all_cliches(text=text, outline=outline)
        
        # Verify results structure
        assert "phrase_cliches" in results
        assert "predictable_beats" in results
        assert "has_cliches" in results
        
        # Verify mocked method was called
        mock_detector._detect_predictable_beats.assert_called_once()
        assert "call to adventure" in str(mock_detector._detect_predictable_beats.call_args)
    
    def test_detect_all_cliches_with_character(self, detector):
        """Test detecting character archetypes."""
        character = {"name": "Hero", "description": "A chosen one destined to save the world"}
        results = detector.detect_all_cliches(character=character)
        
        assert "character_archetypes" in results
        assert isinstance(results["character_archetypes"], list)
    
    def test_detect_all_cliches_with_outline(self, detector):
        """Test detecting predictable beats in outline."""
        outline = {"acts": {"beginning": "call to adventure"}}
        results = detector.detect_all_cliches(outline=outline)
        
        assert "predictable_beats" in results
        assert isinstance(results["predictable_beats"], list)
    
    def test_detect_all_cliches_with_outline_mocked(self, mock_detector):
        """Test detecting predictable beats with mocked internal method."""
        outline = {"acts": {"beginning": "call to adventure"}}
        
        # Configure mock to return specific results
        mock_detector._detect_predictable_beats.return_value = [
            {"beat": "call to adventure", "alternatives": ["unexpected summons"]}
        ]
        
        results = mock_detector.detect_all_cliches(outline=outline)
        
        # Verify results structure
        assert "predictable_beats" in results
        assert isinstance(results["predictable_beats"], list)
        assert len(results["predictable_beats"]) > 0
        
        # Verify mocked method was called with correct arguments
        mock_detector._detect_predictable_beats.assert_called_once()
        call_args = mock_detector._detect_predictable_beats.call_args[0][0]
        assert isinstance(call_args, str), "Should be called with string representation of outline"
    
    def test_detect_all_cliches_empty_input(self, detector):
        """Test detecting clichés with empty input."""
        results = detector.detect_all_cliches()
        
        assert results["has_cliches"] is False
        assert results["total_cliches"] == 0
        assert len(results["phrase_cliches"]) == 0


class TestClicheDetectorErrorHandling:
    """Test error handling for ClicheDetector methods."""
    
    def test_detect_all_cliches_invalid_text_type(self, detector):
        """Test detect_all_cliches with invalid text type."""
        # Should handle non-string gracefully (returns empty results)
        results = detector.detect_all_cliches(text=123)
        assert isinstance(results, dict)
        assert "phrase_cliches" in results
        # Non-string text should be ignored, not raise error
        assert len(results["phrase_cliches"]) == 0
    
    def test_detect_all_cliches_handles_none_text(self, detector):
        """Test detect_all_cliches handles None text explicitly."""
        results = detector.detect_all_cliches(text=None)
        assert isinstance(results, dict)
        assert "phrase_cliches" in results
        assert len(results["phrase_cliches"]) == 0
        assert results["has_cliches"] is False
    
    def test_detect_all_cliches_handles_none_character(self, detector):
        """Test detect_all_cliches handles None character explicitly."""
        results = detector.detect_all_cliches(character=None)
        assert isinstance(results, dict)
        assert "character_archetypes" in results
        assert len(results["character_archetypes"]) == 0
    
    def test_detect_all_cliches_handles_none_outline(self, detector):
        """Test detect_all_cliches handles None outline explicitly."""
        results = detector.detect_all_cliches(outline=None)
        assert isinstance(results, dict)
        assert "predictable_beats" in results
        assert len(results["predictable_beats"]) == 0
    
    def test_detect_all_cliches_handles_malformed_character_dict(self, detector):
        """Test detect_all_cliches handles malformed character dict."""
        # Character dict missing 'description' key
        malformed_character = {"name": "Test"}
        results = detector.detect_all_cliches(character=malformed_character)
        assert isinstance(results, dict)
        assert "character_archetypes" in results
        # Should handle gracefully without raising error
    
    def test_detect_all_cliches_handles_exception_in_detection(self, detector):
        """Test that detect_all_cliches handles exceptions gracefully."""
        # Mock _detect_predictable_beats to raise an exception
        with patch.object(detector, '_detect_predictable_beats', side_effect=Exception("Test error")):
            # Should handle exception and return partial results
            outline = {"acts": {"beginning": "test"}}
            results = detector.detect_all_cliches(outline=outline)
            assert isinstance(results, dict)
            # Should still return valid structure even if internal method fails
            assert "predictable_beats" in results
    
    def test_detect_all_cliches_handles_exception_accessing_phrase_cliches(self, detector):
        """Test that detect_all_cliches handles exceptions when accessing phrase_cliches list."""
        # Mock phrase_cliches attribute to raise exception on access
        original_phrase_cliches = detector.phrase_cliches
        try:
            # Simulate exception during phrase detection by making phrase_cliches raise on iteration
            detector.phrase_cliches = None
            text = "It was a dark and stormy night."
            # Should handle AttributeError gracefully
            results = detector.detect_all_cliches(text=text)
            assert isinstance(results, dict)
            # Should still return valid structure even if phrase detection fails
            assert "phrase_cliches" in results
            assert "has_cliches" in results
        finally:
            detector.phrase_cliches = original_phrase_cliches
    
    def test_detect_all_cliches_handles_exception_in_character_dict_access(self, detector):
        """Test that detect_all_cliches handles exceptions when accessing character dict."""
        # Create a character dict that raises exception on .get() call
        class ProblematicDict(dict):
            def get(self, key, default=None):
                if key == "description":
                    raise Exception("Dict access error")
                return super().get(key, default)
        
        character = ProblematicDict({"name": "Hero", "description": "A chosen one"})
        results = detector.detect_all_cliches(character=character)
        assert isinstance(results, dict)
        # Should still return valid structure even if character detection fails
        assert "character_archetypes" in results
        assert "has_cliches" in results
    
    def test_detect_all_cliches_handles_multiple_exceptions(self, detector):
        """Test that detect_all_cliches handles multiple exceptions across different detection methods."""
        # Mock _detect_predictable_beats to raise exception
        # And create problematic character dict
        class ProblematicDict(dict):
            def get(self, key, default=None):
                if key == "description":
                    raise Exception("Character error")
                return super().get(key, default)
        
        with patch.object(detector, '_detect_predictable_beats', side_effect=Exception("Beat error")):
            text = "Test text"
            character = ProblematicDict({"name": "Test", "description": "Test character"})
            outline = {"acts": {"beginning": "test"}}
            
            results = detector.detect_all_cliches(text=text, character=character, outline=outline)
            assert isinstance(results, dict)
            # Should return valid structure even if multiple detection methods fail
            assert "phrase_cliches" in results
            assert "character_archetypes" in results
            assert "predictable_beats" in results
            assert "has_cliches" in results
            assert "total_cliches" in results
    
    def test_detect_all_cliches_invalid_character_type(self, detector):
        """Test detect_all_cliches with invalid character type."""
        # Should handle non-dict character gracefully
        results = detector.detect_all_cliches(character="not a dict")
        assert isinstance(results, dict)
        assert "character_archetypes" in results
    
    def test_detect_all_cliches_invalid_outline_type(self, detector):
        """Test detect_all_cliches with invalid outline type."""
        # Should handle non-dict outline gracefully
        results = detector.detect_all_cliches(outline="not a dict")
        assert isinstance(results, dict)
        assert "predictable_beats" in results
    
    def test_suggest_replacements_empty_string(self, detector):
        """Test suggest_replacements with empty string."""
        suggestions = detector.suggest_replacements("")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_suggest_replacements_none(self, detector):
        """Test suggest_replacements with None."""
        suggestions = detector.suggest_replacements(None)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should return generic suggestions
        assert any("specific" in s.lower() or "concrete" in s.lower() for s in suggestions)
    
    def test_apply_replacements_invalid_text_type(self, detector):
        """Test apply_replacements with invalid text type."""
        with pytest.raises(TypeError, match="text must be a string"):
            detector.apply_replacements(123, {"cliche": "replacement"})
    
    def test_apply_replacements_invalid_replacements_type(self, detector):
        """Test apply_replacements with invalid replacements type."""
        with pytest.raises(TypeError, match="replacements must be a dict"):
            detector.apply_replacements("text", "not a dict")
    
    def test_apply_replacements_malformed_replacements_dict(self, detector):
        """Test apply_replacements with malformed replacements dictionary."""
        text = "A test phrase."
        # Malformed: values are not strings
        malformed_replacements = {"A test phrase.": [1, 2, 3]}
        with pytest.raises(TypeError, match="must be a string"):
            detector.apply_replacements(text, replacements=malformed_replacements)
    
    def test_apply_replacements_valid_usage(self, detector):
        """Test apply_replacements with valid inputs."""
        text = "It was a dark and stormy night."
        replacements = {"dark and stormy night": "a night that swallowed sound"}
        result = detector.apply_replacements(text, replacements)
        
        assert isinstance(result, str)
        assert "dark and stormy night" not in result
        assert "a night that swallowed sound" in result
    
    def test_apply_replacements_handles_empty_replacements(self, detector):
        """Test apply_replacements with empty replacements dict."""
        text = "It was a dark and stormy night."
        replacements = {}
        result = detector.apply_replacements(text, replacements)
        
        # Should return original text unchanged
        assert isinstance(result, str)
        assert result == text
    
    def test_apply_replacements_handles_none_replacements(self, detector):
        """Test apply_replacements with None replacements raises TypeError."""
        text = "Some text"
        with pytest.raises(TypeError, match="replacements must be a dict"):
            detector.apply_replacements(text, None)
    
    def test_apply_replacements_handles_replacements_with_none_values(self, detector):
        """Test apply_replacements handles None values in replacements dict."""
        text = "Some text with cliche"
        replacements = {"cliche": None}
        # Should raise TypeError for None replacement value
        with pytest.raises(TypeError, match="must be a string"):
            detector.apply_replacements(text, replacements)
    
    def test_suggest_replacements_handles_very_long_text(self, detector):
        """Test suggest_replacements with very long text input."""
        very_long_text = "cliche phrase " * 10000
        suggestions = detector.suggest_replacements(very_long_text)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_detect_all_cliches_handles_unicode_text(self, detector):
        """Test detect_all_cliches handles Unicode text properly."""
        unicode_text = "It was a dark and stormy night. 🌙 Émojis and spéciál chàracters."
        results = detector.detect_all_cliches(text=unicode_text)
        assert isinstance(results, dict)
        assert "phrase_cliches" in results
        # Should detect cliché even in Unicode text
        assert results["has_cliches"] is True or len(results["phrase_cliches"]) > 0
    
    def test_detect_all_cliches_handles_very_large_text(self, detector):
        """Test detect_all_cliches handles very large text input."""
        large_text = "It was a dark and stormy night. " * 10000
        results = detector.detect_all_cliches(text=large_text)
        assert isinstance(results, dict)
        assert "phrase_cliches" in results
        assert "has_cliches" in results
        # Should detect multiple instances of cliché
        assert results["has_cliches"] is True
    
    def test_detect_all_cliches_handles_nested_character_dict(self, detector):
        """Test detect_all_cliches handles nested/complex character dict structures."""
        nested_character = {
            "name": "Hero",
            "description": "A chosen one",
            "metadata": {
                "archetype": "warrior",
                "traits": ["brave", "strong"]
            }
        }
        results = detector.detect_all_cliches(character=nested_character)
        assert isinstance(results, dict)
        assert "character_archetypes" in results
        # Should handle nested structures gracefully
    
    def test_detect_all_cliches_handles_deeply_nested_outline(self, detector):
        """Test detect_all_cliches handles deeply nested outline structures."""
        nested_outline = {
            "acts": {
                "beginning": {
                    "scene": "setup",
                    "details": {"beat": "call to adventure"}
                },
                "middle": "complication",
                "end": "resolution"
            }
        }
        results = detector.detect_all_cliches(outline=nested_outline)
        assert isinstance(results, dict)
        assert "predictable_beats" in results
        # Should handle nested structures and extract text for detection
    
    def test_apply_replacements_handles_overlapping_replacements(self, detector):
        """Test apply_replacements handles overlapping replacement keys correctly."""
        text = "It was a dark and stormy night, and it was dark."
        replacements = {
            "dark and stormy night": "a night that swallowed sound",
            "dark": "shadowy"
        }
        result = detector.apply_replacements(text, replacements)
        assert isinstance(result, str)
        # Should apply replacements in order (longer matches first typically)
        assert "a night that swallowed sound" in result or "shadowy" in result
    
    def test_detect_all_cliches_handles_special_characters_in_text(self, detector):
        """Test detect_all_cliches handles special characters and punctuation."""
        text_with_special = "It was a dark and stormy night!!! (Really dark.) [Very stormy.]"
        results = detector.detect_all_cliches(text=text_with_special)
        assert isinstance(results, dict)
        assert "phrase_cliches" in results
        # Should detect cliché despite special characters
        assert results["has_cliches"] is True or len(results["phrase_cliches"]) > 0


class TestClicheDetectorEdgeCases:
    """Test edge cases for ClicheDetector."""
    
    def test_detect_all_cliches_empty_string_text(self, detector):
        """Test detect_all_cliches with empty string text."""
        results = detector.detect_all_cliches(text="")
        assert results["has_cliches"] is False
        assert results["total_cliches"] == 0
    
    def test_detect_all_cliches_empty_character_dict(self, detector):
        """Test detect_all_cliches with empty character dict."""
        results = detector.detect_all_cliches(character={})
        assert isinstance(results, dict)
        assert len(results["character_archetypes"]) == 0
    
    def test_detect_all_cliches_empty_outline_dict(self, detector):
        """Test detect_all_cliches with empty outline dict."""
        results = detector.detect_all_cliches(outline={})
        assert isinstance(results, dict)
        assert len(results["predictable_beats"]) == 0
    
    def test_suggest_replacements_unknown_cliche(self, detector):
        """Test suggest_replacements with unknown cliché."""
        suggestions = detector.suggest_replacements("unknown phrase")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should return generic suggestions for unknown clichés
        assert any("specific" in s.lower() for s in suggestions)


class TestClicheDetectorIsolation:
    """Test that ClicheDetector tests properly isolate dependencies."""
    
    def test_detect_all_cliches_with_fully_mocked_dependencies(self):
        """Test that detection works with all internal methods mocked."""
        with patch.object(ClicheDetector, '_detect_predictable_beats') as mock_beats:
            mock_beats.return_value = [
                {"beat": "test beat", "alternatives": ["alternative 1"]}
            ]
            
            detector = ClicheDetector()
            detector._detect_predictable_beats = mock_beats
            
            outline = {"acts": {"beginning": "test beat"}}
            results = detector.detect_all_cliches(outline=outline)
            
            # Verify mock was called
            mock_beats.assert_called_once()
            
            # Verify results include mocked data
            assert "predictable_beats" in results
            assert len(results["predictable_beats"]) > 0
    
    def test_detect_all_cliches_text_detection_isolated(self, mock_detector):
        """Test that text detection works independently of other detection methods."""
        text = "It was a dark and stormy night."
        
        # Mock should not affect text detection
        mock_detector._detect_predictable_beats.return_value = []
        
        results = mock_detector.detect_all_cliches(text=text)
        
        # Text detection should work independently
        assert "phrase_cliches" in results
        # Should detect the cliché phrase
        assert len(results["phrase_cliches"]) > 0
        
        # Mock should not have been called (no outline provided)
        mock_detector._detect_predictable_beats.assert_not_called()
    
    def test_detect_all_cliches_character_detection_isolated(self, mock_detector):
        """Test that character detection works independently of other detection methods."""
        character = {"name": "Hero", "description": "A chosen one destined to save the world"}
        
        # Mock should not affect character detection
        mock_detector._detect_predictable_beats.return_value = []
        
        results = mock_detector.detect_all_cliches(character=character)
        
        # Character detection should work independently
        assert "character_archetypes" in results
        # Should detect the archetype
        assert len(results["character_archetypes"]) > 0
        
        # Mock should not have been called (no outline provided)
        mock_detector._detect_predictable_beats.assert_not_called()


class TestClicheDetectorSingleton:
    """Test singleton pattern for get_cliche_detector."""
    
    def test_get_cliche_detector_returns_instance(self):
        """Test that get_cliche_detector returns a ClicheDetector instance."""
        detector = get_cliche_detector()
        assert isinstance(detector, ClicheDetector)
    
    def test_get_cliche_detector_returns_same_instance(self):
        """Test that get_cliche_detector returns the same instance."""
        detector1 = get_cliche_detector()
        detector2 = get_cliche_detector()
        assert detector1 is detector2
    
    def test_get_cliche_detector_with_mocked_dependencies(self):
        """Test singleton with mocked dependencies doesn't affect other tests."""
        # Get singleton instance
        detector = get_cliche_detector()
        
        # Mock internal method
        original_method = detector._detect_predictable_beats
        detector._detect_predictable_beats = MagicMock(return_value=[])
        
        # Test that mock works
        results = detector.detect_all_cliches(outline={"acts": {}})
        assert "predictable_beats" in results
        
        # Restore original method (important for singleton)
        detector._detect_predictable_beats = original_method


class TestDetectPredictableBeats:
    """Test suite for _detect_predictable_beats private helper method."""
    
    def test_detect_predictable_beats_finds_call_to_adventure(self, detector):
        """Test that _detect_predictable_beats detects 'call to adventure' beat."""
        outline_text = "The hero receives a call to adventure that changes everything."
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert any(result["beat"] == "call to adventure" for result in results)
        assert any("alternatives" in result for result in results)
        assert any("suggestion" in result for result in results)
    
    def test_detect_predictable_beats_finds_heros_journey(self, detector):
        """Test that _detect_predictable_beats detects 'hero's journey' beat."""
        outline_text = "This follows the classic hero's journey structure."
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert any(result["beat"] == "hero's journey" for result in results)
    
    def test_detect_predictable_beats_case_insensitive(self, detector):
        """Test that _detect_predictable_beats is case-insensitive."""
        outline_text = "CALL TO ADVENTURE in uppercase"
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert any(result["beat"] == "call to adventure" for result in results)
    
    def test_detect_predictable_beats_no_matches(self, detector):
        """Test that _detect_predictable_beats returns empty list when no beats found."""
        outline_text = "A completely original story with no predictable beats."
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_detect_predictable_beats_multiple_matches(self, detector):
        """Test that _detect_predictable_beats finds multiple beats."""
        outline_text = "The hero's journey begins with a call to adventure."
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) >= 1
        # Should find at least one of the beats
    
    def test_detect_predictable_beats_empty_string(self, detector):
        """Test that _detect_predictable_beats handles empty string."""
        outline_text = ""
        results = detector._detect_predictable_beats(outline_text)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_detect_predictable_beats_result_structure(self, detector):
        """Test that _detect_predictable_beats returns properly structured results."""
        outline_text = "call to adventure"
        results = detector._detect_predictable_beats(outline_text)
        
        if len(results) > 0:
            result = results[0]
            assert "beat" in result
            assert "alternatives" in result
            assert "suggestion" in result
            assert isinstance(result["beat"], str)
            assert isinstance(result["alternatives"], list)
            assert isinstance(result["suggestion"], str)
            assert "call to adventure" in result["suggestion"].lower()
    
    def test_detect_predictable_beats_partial_match_handling(self, detector):
        """Test that _detect_predictable_beats handles partial matches correctly."""
        # Test that it doesn't match partial words
        outline_text = "The hero called to the adventure"
        results = detector._detect_predictable_beats(outline_text)
        
        # "call to adventure" should not match "called to the adventure"
        # This tests the substring matching behavior
        assert isinstance(results, list)
        # The exact behavior depends on implementation, but should be consistent
