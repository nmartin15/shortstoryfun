"""
Tests for character voice analyzer functionality.
"""

import pytest
from src.shortstory.voice_analyzer import (
    CharacterVoiceAnalyzer,
    DialogueExtractor,
    SpeechPatternAnalyzer,
    VoiceConsistencyTracker,
    analyze_character_voices,
)


@pytest.fixture
def analyzer():
    """Create a CharacterVoiceAnalyzer instance for testing."""
    return CharacterVoiceAnalyzer()


@pytest.fixture
def sample_story_with_dialogue():
    """Sample story text with dialogue."""
    return '''
    "Hello, how are you?" Alice asked.
    "I am fine, thank you." Bob replied.
    "What are you doing?" Alice questioned.
    "Nothing much." Bob mumbled.
    '''


@pytest.fixture
def sample_story_with_attributed_dialogue():
    """Sample story with explicitly attributed dialogue."""
    return '''
    Alice said: "The magnificent, extraordinary, exceptional individual demonstrated remarkable capabilities."
    Bob said: "I dunno. Gonna go now. Yeah."
    '''


class TestDialogueExtraction:
    """Test dialogue extraction functionality."""
    
    def test_extract_dialogue_basic(self, analyzer):
        """Test basic dialogue extraction."""
        text = '"Hello," she said. "How are you?"'
        dialogues = analyzer.dialogue_extractor.extract_dialogue(text)
        
        assert isinstance(dialogues, list)
        assert len(dialogues) >= 2
        assert all("text" in d for d in dialogues)
        assert all("speaker" in d for d in dialogues)
    
    def test_extract_dialogue_with_attribution(self, analyzer):
        """Test dialogue extraction with explicit attribution."""
        text = 'Alice said: "Hello there." Bob replied: "Hi."'
        dialogues = analyzer.dialogue_extractor.extract_dialogue(text)
        
        assert len(dialogues) >= 2
        # Check that speakers are identified
        speakers = [d.get("speaker") for d in dialogues]
        assert any(speaker and speaker != "Unknown" for speaker in speakers)
    
    def test_extract_dialogue_no_dialogue(self, analyzer):
        """Test extraction when no dialogue is present."""
        text = "This is a story without any dialogue at all."
        dialogues = analyzer.dialogue_extractor.extract_dialogue(text)
        
        assert isinstance(dialogues, list)
        assert len(dialogues) == 0


class TestCharacterVoiceAnalysis:
    """Test character voice analysis."""
    
    def test_analyze_story_basic(self, analyzer, sample_story_with_dialogue):
        """Test basic story analysis."""
        result = analyzer.analyze_story(sample_story_with_dialogue)
        
        assert "characters" in result
        assert "overall" in result
        assert "total_dialogue_instances" in result["overall"]
        assert result["overall"]["total_dialogue_instances"] >= 4
    
    def test_analyze_story_multiple_characters_with_unknown_speaker(self, analyzer):
        """Test analysis of story with multiple characters where speaker identification is ambiguous."""
        story = '''
        "Hello, how are you?" she asked.
        "I am fine, thank you." he replied.
        "What are you doing?" the first voice questioned.
        "Nothing much." the second voice mumbled.
        '''
        
        result = analyzer.analyze_story(story)
        
        assert result["overall"]["total_dialogue_instances"] >= 4
        # Assert that an 'Unknown' character is present and has aggregated data
        assert "Unknown" in result["characters"] or any(
            char_name in result["characters"] 
            for char_name in ["Unknown", "she", "he", "first voice", "second voice"]
        )
    
    def test_analyze_character_distinctiveness_with_known_speakers(self, analyzer, sample_story_with_attributed_dialogue):
        """Test that different characters are identified as distinct with explicit speaker attribution."""
        result = analyzer.analyze_story(sample_story_with_attributed_dialogue)
        
        # Should identify Alice and Bob
        character_names = list(result["characters"].keys())
        assert len(character_names) >= 2
        
        # Check that voice differentiation score is calculated
        assert "voice_differentiation_score" in result["overall"]
        assert result["overall"]["voice_differentiation_score"] >= 0.0
    
    def test_analyze_story_empty_text(self, analyzer):
        """Test analysis with empty text."""
        result = analyzer.analyze_story("")
        
        assert "characters" in result
        assert "overall" in result
        assert result["overall"]["total_dialogue_instances"] == 0
        assert result["overall"]["characters_with_dialogue"] == 0
    
    def test_analyze_story_none_text(self, analyzer):
        """Test analysis with None text."""
        result = analyzer.analyze_story(None)
        
        assert "characters" in result
        assert "overall" in result
        assert result["overall"]["total_dialogue_instances"] == 0
    
    def test_analyze_story_no_dialogue(self, analyzer):
        """Test analysis of story without dialogue."""
        text = "This is a story without any dialogue. It has narrative but no spoken words."
        result = analyzer.analyze_story(text)
        
        assert result["overall"]["total_dialogue_instances"] == 0
        assert result["overall"]["characters_with_dialogue"] == 0
        assert len(result["characters"]) == 0
        assert "suggestions" in result["overall"]
        assert len(result["overall"]["suggestions"]) > 0


class TestVoiceConsistency:
    """Test voice consistency tracking."""
    
    def test_consistency_tracking(self, analyzer):
        """Test that consistency is tracked for character voices."""
        story = '''
        Alice said: "I am very happy today."
        Alice said: "I am very happy today."
        Alice said: "I am very happy today."
        '''
        
        result = analyzer.analyze_story(story)
        
        # Should have Alice with multiple dialogue instances
        if "Alice" in result["characters"]:
            alice_data = result["characters"]["Alice"]
            assert "consistency" in alice_data
            assert "dialogue_count" in alice_data
            assert alice_data["dialogue_count"] >= 3


class TestConvenienceFunction:
    """Test convenience function for voice analysis."""
    
    def test_analyze_character_voices_function(self, sample_story_with_dialogue):
        """Test the analyze_character_voices convenience function."""
        result = analyze_character_voices(sample_story_with_dialogue)
        
        assert "characters" in result
        assert "overall" in result
        assert "total_dialogue_instances" in result["overall"]
    
    def test_analyze_character_voices_with_character_info(self, sample_story_with_dialogue):
        """Test analyze_character_voices with character info."""
        character_info = {
            "name": "Alice",
            "quirks": ["Speaks in questions"],
            "description": "A curious character"
        }
        
        result = analyze_character_voices(sample_story_with_dialogue, character_info)
        
        assert "characters" in result
        assert "overall" in result


class TestSpeechPatternAnalysis:
    """Test speech pattern analysis."""
    
    def test_analyze_dialogue_patterns(self, analyzer):
        """Test analysis of dialogue patterns."""
        dialogue_text = "This is a test dialogue with multiple words and sentences."
        pattern_analyzer = SpeechPatternAnalyzer()
        
        analysis = pattern_analyzer.analyze_dialogue(dialogue_text)
        
        assert "vocabulary" in analysis
        assert "sentence_structure" in analysis
        assert "rhythm" in analysis
        assert "vocabulary_richness" in analysis.get("vocabulary", {})


class TestErrorHandling:
    """Test error handling in voice analyzer."""
    
    def test_analyze_story_handles_invalid_input(self, analyzer):
        """Test that analyze_story handles invalid input gracefully."""
        # Test with non-string input
        result = analyzer.analyze_story(123)
        assert "characters" in result
        assert "overall" in result
    
    def test_analyze_story_handles_very_long_text(self, analyzer):
        """Test that analyze_story handles very long text."""
        long_text = "This is a test. " * 1000
        result = analyzer.analyze_story(long_text)
        
        assert "characters" in result
        assert "overall" in result
