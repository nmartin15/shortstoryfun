"""
Tests for memorability scoring functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.shortstory.memorability_scorer import MemorabilityScorer, DimensionScore


@pytest.fixture
def scorer():
    """Create a MemorabilityScorer instance for testing."""
    return MemorabilityScorer()


class TestMemorabilityScorerDimensions:
    """Test individual dimension scoring methods."""
    
    def test_score_voice_strength_with_mocked_details(self, scorer):
        """Test voice strength dimension scoring with mocked detail counting."""
        # Mock the internal detail counting method
        with patch.object(scorer, '_count_specific_details', return_value=5) as mock_count_details, \
             patch.object(scorer, '_has_varied_sentence_length', return_value=True) as mock_varied_length, \
             patch.object(scorer, '_has_unique_phrases', return_value=True) as mock_unique_phrases:
            
            text_strong = "Some text that would normally have details."
            score = scorer._score_voice_strength(text_strong, None, None)
            
            assert isinstance(score, DimensionScore)
            assert score.name == "Voice Strength"
            assert score.score > 0.5  # Based on mocked values, score should be high
            mock_count_details.assert_called_once_with(text_strong)
            mock_varied_length.assert_called_once_with(text_strong)
            mock_unique_phrases.assert_called_once_with(text_strong)
    
    def test_score_voice_strength_with_scarce_details(self, scorer):
        """Test voice strength scoring when details are scarce."""
        with patch.object(scorer, '_count_specific_details', return_value=0), \
             patch.object(scorer, '_has_varied_sentence_length', return_value=False), \
             patch.object(scorer, '_has_unique_phrases', return_value=False):
            
            text_weak = "Very vague text."
            score = scorer._score_voice_strength(text_weak, None, None)
            
            assert isinstance(score, DimensionScore)
            assert score.score < 0.5
    
    def test_score_language_precision_with_mocked_detection(self, scorer):
        """Test language precision scoring with mocked cliché detection."""
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": True,
                "total_cliches": 2,
                "phrase_cliches": [{"phrase": "dark and stormy night"}],
                "character_archetypes": [],
                "predictable_beats": [],
                "plot_structures": []
            }
            
            text = "It was a dark and stormy night."
            score = scorer._score_language_precision(text, None, None)
            
            assert isinstance(score, DimensionScore)
            assert score.name == "Language Precision"
            assert score.score < 1.0  # Should be penalized for clichés
            mock_detect.assert_called_once()
    
    def test_score_character_uniqueness_with_mocked_detection(self, scorer):
        """Test character uniqueness scoring with mocked archetype detection."""
        character = {"name": "Hero", "description": "A chosen one destined to save the world"}
        
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": False,
                "total_cliches": 0,
                "phrase_cliches": [],
                "character_archetypes": [{"archetype": "chosen one"}],
                "predictable_beats": [],
                "plot_structures": []
            }
            
            score = scorer._score_character_uniqueness(None, character, None)
            
            assert isinstance(score, DimensionScore)
            assert score.name == "Character Uniqueness"
            assert score.score < 1.0  # Should be penalized for archetype
            mock_detect.assert_called_once()
    
    def test_score_beat_originality_with_mocked_detection(self, scorer):
        """Test beat originality scoring with mocked beat detection."""
        outline = {"acts": {"beginning": "call to adventure"}}
        
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": False,
                "total_cliches": 0,
                "phrase_cliches": [],
                "character_archetypes": [],
                "predictable_beats": [{"beat": "call to adventure"}],
                "plot_structures": []
            }
            
            score = scorer._score_beat_originality(None, None, outline)
            
            assert isinstance(score, DimensionScore)
            assert score.name == "Beat Originality"
            assert score.score < 1.0  # Should be penalized for predictable beat
            mock_detect.assert_called_once()


class TestMemorabilityScorerIntegration:
    """Test full story scoring integration."""
    
    def test_score_story_returns_complete_results(self, scorer):
        """Test that score_story returns complete scoring results."""
        text = "A unique story about a lighthouse keeper."
        character = {"name": "Mara", "description": "A quiet keeper"}
        outline = {"acts": {"beginning": "setup"}}
        
        # Mock all internal detection methods
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": False,
                "total_cliches": 0,
                "phrase_cliches": [],
                "character_archetypes": [],
                "predictable_beats": [],
                "plot_structures": []
            }
            
            with patch.object(scorer, '_count_specific_details', return_value=5), \
                 patch.object(scorer, '_has_varied_sentence_length', return_value=True), \
                 patch.object(scorer, '_has_unique_phrases', return_value=True):
                
                result = scorer.score_story(text, character, outline)
                
                assert "overall_score" in result
                assert "dimensions" in result
                assert isinstance(result["overall_score"], float)
                assert 0.0 <= result["overall_score"] <= 1.0
                assert "language_precision" in result["dimensions"]
                assert "character_uniqueness" in result["dimensions"]
                assert "voice_strength" in result["dimensions"]
                assert "beat_originality" in result["dimensions"]
    
    def test_score_story_with_empty_text(self, scorer):
        """Test score_story with empty text."""
        # Mock cliche_detector to isolate test from external dependency
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": False,
                "total_cliches": 0,
                "phrase_cliches": [],
                "character_archetypes": [],
                "predictable_beats": [],
                "plot_structures": []
            }
            
            result = scorer.score_story("", None, None)
            
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
            # Empty text should have low scores
            assert result["overall_score"] < 0.5
            # Verify detector was called (even with empty text)
            mock_detect.assert_called()
    
    def test_score_story_handles_none_inputs(self, scorer):
        """Test that score_story handles None inputs gracefully."""
        # Mock cliche_detector to isolate test from external dependency
        with patch.object(scorer.cliche_detector, 'detect_all_cliches') as mock_detect:
            mock_detect.return_value = {
                "has_cliches": False,
                "total_cliches": 0,
                "phrase_cliches": [],
                "character_archetypes": [],
                "predictable_beats": [],
                "plot_structures": []
            }
            
            result = scorer.score_story("Some text", None, None, None)
            
            assert "overall_score" in result
            assert "dimensions" in result
            assert isinstance(result["overall_score"], float)
            # Verify detector was called
            mock_detect.assert_called()


class TestMemorabilityScorerErrorHandling:
    """Test error handling in MemorabilityScorer."""
    
    def test_score_story_handles_detection_errors(self, scorer):
        """Test that score_story handles errors in cliché detection gracefully."""
        with patch.object(scorer.cliche_detector, 'detect_all_cliches', side_effect=Exception("Detection error")):
            # Should not crash, but may return lower scores
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
    
    def test_score_story_handles_none_cliche_detector(self, scorer):
        """Test that score_story handles None cliche_detector gracefully."""
        original_detector = scorer.cliche_detector
        scorer.cliche_detector = None
        try:
            # Should handle None detector without crashing
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
        finally:
            scorer.cliche_detector = original_detector
    
    def test_score_story_handles_detection_returning_none(self, scorer):
        """Test that score_story handles cliche_detector returning None."""
        with patch.object(scorer.cliche_detector, 'detect_all_cliches', return_value=None):
            # Should handle None return value gracefully
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
    
    def test_score_story_handles_incomplete_detection_results(self, scorer):
        """Test that score_story handles incomplete detection results."""
        incomplete_results = {
            "has_cliches": True,
            # Missing other expected fields
        }
        with patch.object(scorer.cliche_detector, 'detect_all_cliches', return_value=incomplete_results):
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
    
    def test_score_voice_strength_handles_none_text(self, scorer):
        """Test that _score_voice_strength handles None text."""
        with patch.object(scorer, '_count_specific_details', return_value=0):
            score = scorer._score_voice_strength(None, None, None)
            assert isinstance(score, DimensionScore)
            assert score.score >= 0.0
    
    def test_score_story_handles_exception_in_dimension_scoring(self, scorer):
        """Test that score_story handles exceptions in dimension scoring methods."""
        # Mock a dimension scoring method to raise an exception
        with patch.object(scorer, '_score_voice_strength', side_effect=Exception("Scoring error")):
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert "dimensions" in result
            assert isinstance(result["overall_score"], float)
            # Should still return valid results even if one dimension fails
    
    def test_score_story_handles_exception_in_multiple_dimensions(self, scorer):
        """Test that score_story handles exceptions in multiple dimension scoring methods."""
        # Mock multiple dimension scoring methods to raise exceptions
        with patch.object(scorer, '_score_voice_strength', side_effect=Exception("Voice error")), \
             patch.object(scorer, '_score_language_precision', side_effect=Exception("Language error")), \
             patch.object(scorer, '_score_character_uniqueness', side_effect=Exception("Character error")):
            
            result = scorer.score_story("Some text", {"name": "Test"}, {"acts": {}})
            assert "overall_score" in result
            assert "dimensions" in result
            assert isinstance(result["overall_score"], float)
            # Should still return valid results even if multiple dimensions fail
    
    def test_score_story_handles_detection_returning_invalid_structure(self, scorer):
        """Test that score_story handles cliche_detector returning invalid structure."""
        invalid_results = "not a dict"  # Wrong type
        with patch.object(scorer.cliche_detector, 'detect_all_cliches', return_value=invalid_results):
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
    
    def test_score_story_handles_detection_raising_exception_during_call(self, scorer):
        """Test that score_story handles cliche_detector raising exception during call."""
        with patch.object(scorer.cliche_detector, 'detect_all_cliches', side_effect=RuntimeError("Runtime error")):
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert isinstance(result["overall_score"], float)
    
    def test_score_story_handles_none_dimension_scores(self, scorer):
        """Test that score_story handles None dimension scores gracefully."""
        with patch.object(scorer, '_score_voice_strength', return_value=None), \
             patch.object(scorer, '_score_language_precision', return_value=None):
            
            result = scorer.score_story("Some text", None, None)
            assert "overall_score" in result
            assert "dimensions" in result
            assert isinstance(result["overall_score"], float)
            # Should handle None scores without crashing