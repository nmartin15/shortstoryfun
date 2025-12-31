"""
Tests for memorability scorer.
"""

import pytest
from src.shortstory.memorability_scorer import (
    MemorabilityScorer,
    get_memorability_scorer,
    DimensionScore,
)


def test_get_memorability_scorer_singleton():
    """Test that get_memorability_scorer returns a singleton."""
    scorer1 = get_memorability_scorer()
    scorer2 = get_memorability_scorer()
    assert scorer1 is scorer2


def test_score_story_empty_text():
    """Test scoring with empty text."""
    scorer = MemorabilityScorer()
    result = scorer.score_story("")
    
    assert "overall_score" in result
    assert "dimensions" in result
    assert "prioritized_suggestions" in result
    assert "summary" in result
    
    # Language precision should be low
    assert result["dimensions"]["language_precision"]["score"] == 0.0


def test_score_story_no_cliches():
    """Test scoring with distinctive text (no clichés)."""
    scorer = MemorabilityScorer()
    text = "A lighthouse keeper named Mara collects lost voices in glass jars. Each voice tells a story that was never spoken."
    
    result = scorer.score_story(text)
    
    assert result["overall_score"] > 0.5
    assert result["dimensions"]["language_precision"]["score"] > 0.7


def test_score_story_with_cliches():
    """Test scoring with clichéd text."""
    scorer = MemorabilityScorer()
    text = "It was a dark and stormy night. The hero arrived just in the nick of time."
    
    result = scorer.score_story(text)
    
    assert result["overall_score"] < 0.8
    assert result["dimensions"]["language_precision"]["score"] < 0.7
    
    # Should have issues
    language_issues = result["dimensions"]["language_precision"]["issues"]
    assert len(language_issues) > 0
    
    # Should have suggestions
    assert len(result["prioritized_suggestions"]) > 0


def test_score_language_precision():
    """Test language precision dimension scoring."""
    scorer = MemorabilityScorer()
    
    # Test with clichés
    text_with_cliches = "It was a dark and stormy night when all hell broke loose."
    score = scorer._score_language_precision(text_with_cliches)
    
    assert score.name == "Language Precision"
    assert 0.0 <= score.score <= 1.0
    assert len(score.issues) > 0
    
    # Test with distinctive text
    text_distinctive = "The lighthouse keeper's hands trembled as she placed the final jar on the shelf."
    score2 = scorer._score_language_precision(text_distinctive)
    
    assert score2.score > score.score
    assert len(score2.issues) == 0 or len(score2.issues) < len(score.issues)


def test_score_character_uniqueness_no_character():
    """Test character uniqueness scoring without character."""
    scorer = MemorabilityScorer()
    score = scorer._score_character_uniqueness("Some text", None)
    
    assert score.name == "Character Uniqueness"
    assert score.score == 0.5  # Neutral score
    assert len(score.issues) > 0
    assert any(issue["type"] == "missing_character" for issue in score.issues)


def test_score_character_uniqueness_generic_archetype():
    """Test character uniqueness with generic archetype."""
    scorer = MemorabilityScorer()
    character = "A wise old mentor who guides the chosen one."
    
    score = scorer._score_character_uniqueness("Some text", character)
    
    assert score.score < 0.7
    assert len(score.issues) > 0
    assert any(issue["type"] == "generic_archetype" for issue in score.issues)


def test_score_character_uniqueness_with_quirks():
    """Test character uniqueness with unique quirks."""
    scorer = MemorabilityScorer()
    character = {
        "name": "Mara",
        "description": "A lighthouse keeper",
        "quirks": ["Never speaks above a whisper", "Collects lost voices"],
        "contradictions": "Afraid of silence but works in isolation"
    }
    
    score = scorer._score_character_uniqueness("Some text", character)
    
    assert score.score > 0.5
    assert any("quirks" in strength.lower() for strength in score.strengths)


def test_score_voice_strength():
    """Test voice strength dimension scoring."""
    scorer = MemorabilityScorer()
    
    # Text with dialogue and specific details
    text_strong = '"I never understood why," she whispered, placing the blue glass jar on the oak shelf. The room smelled of salt and old paper.'
    
    score = scorer._score_voice_strength(text_strong, None, None)
    
    assert score.name == "Voice Strength"
    assert 0.0 <= score.score <= 1.0
    assert score.score > 0.5
    
    # Text without dialogue
    text_weak = "She walked to the room. It was nice. She felt good."
    score2 = scorer._score_voice_strength(text_weak, None, None)
    
    assert score2.score < score.score


def test_score_beat_originality():
    """Test beat originality dimension scoring."""
    scorer = MemorabilityScorer()
    
    # Text with predictable beats
    text_predictable = "The hero received the call to adventure. At first, he refused the call. Then he met the mentor who guided him."
    
    score = scorer._score_beat_originality(text_predictable, None)
    
    assert score.name == "Beat Originality"
    assert 0.0 <= score.score <= 1.0
    assert score.score < 1.0
    
    # Text without predictable beats
    text_original = "Mara found the voice in a seashell. It didn't ask for help. It asked to be forgotten."
    
    score2 = scorer._score_beat_originality(text_original, None)
    
    assert score2.score >= score.score


def test_generate_prioritized_suggestions():
    """Test suggestion generation and prioritization."""
    scorer = MemorabilityScorer()
    
    # Create dimensions with various issues
    from src.shortstory.memorability_scorer import DimensionScore
    
    dims = {
        "language_precision": DimensionScore(
            name="Language Precision",
            score=0.4,
            issues=[
                {"type": "narrative_cliche", "severity": "high", "message": "Found clichés"},
            ]
        ),
        "character_uniqueness": DimensionScore(
            name="Character Uniqueness",
            score=0.6,
            issues=[
                {"type": "missing_quirks", "severity": "medium", "message": "No quirks"},
            ]
        ),
    }
    
    suggestions = scorer._generate_prioritized_suggestions(dims)
    
    assert len(suggestions) > 0
    # High-severity issues should come first
    assert any("cliché" in s.lower() or "cliche" in s.lower() for s in suggestions[:3])


def test_issue_to_suggestion():
    """Test conversion of issues to actionable suggestions."""
    scorer = MemorabilityScorer()
    
    issue = {
        "type": "narrative_cliche",
        "severity": "high",
        "message": "Found clichés",
        "examples": ["dark and stormy night"],
    }
    
    dim_score = DimensionScore(
        name="Language Precision",
        score=0.5,
        issues=[issue]
    )
    
    suggestion = scorer._issue_to_suggestion("language_precision", dim_score, issue)
    
    assert suggestion is not None
    assert "replace" in suggestion.lower() or "cliché" in suggestion.lower() or "cliche" in suggestion.lower()


def test_get_status():
    """Test status label generation."""
    scorer = MemorabilityScorer()
    
    assert scorer._get_status(0.9) == "excellent"
    assert scorer._get_status(0.75) == "good"
    assert scorer._get_status(0.6) == "needs_improvement"
    assert scorer._get_status(0.3) == "poor"


def test_generate_summary():
    """Test summary generation."""
    scorer = MemorabilityScorer()
    
    dims = {
        "language_precision": DimensionScore(name="Language Precision", score=0.8),
        "character_uniqueness": DimensionScore(name="Character Uniqueness", score=0.7),
        "voice_strength": DimensionScore(name="Voice Strength", score=0.75),
        "beat_originality": DimensionScore(name="Beat Originality", score=0.8),
    }
    
    summary = scorer._generate_summary(0.76, dims)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "76" in summary or "0.76" in summary or "76%" in summary


def test_count_specific_details():
    """Test counting specific details in text."""
    scorer = MemorabilityScorer()
    
    text_with_details = "She placed the blue glass jar on the oak shelf. The room smelled of salt. Three voices whispered."
    count = scorer._count_specific_details(text_with_details)
    
    assert count >= 2  # Should find colors (blue), sensory words (smelled), numbers (Three)
    
    text_vague = "It was nice. She felt good. Things happened."
    count2 = scorer._count_specific_details(text_vague)
    
    assert count2 < count


def test_has_varied_sentence_length():
    """Test sentence length variation detection."""
    scorer = MemorabilityScorer()
    
    # Varied sentence lengths
    text_varied = "Short. This is a longer sentence with more words and complexity. Very short. Another longer sentence that provides more detail and context."
    assert scorer._has_varied_sentence_length(text_varied) is True
    
    # Monotonous sentence lengths
    text_monotonous = "This is a sentence. This is another sentence. This is yet another sentence. They are all similar."
    assert scorer._has_varied_sentence_length(text_monotonous) is False


def test_has_unique_phrases():
    """Test unique phrase detection."""
    scorer = MemorabilityScorer()
    
    text_specific = "She opened the door and placed the book on the table."
    assert scorer._has_unique_phrases(text_specific) is True
    
    text_generic = "It was good. Things happened. People felt things."
    assert scorer._has_unique_phrases(text_generic) is False


def test_score_story_with_character_and_outline():
    """Test full story scoring with character and outline."""
    scorer = MemorabilityScorer()
    
    text = "Mara collected voices in glass jars. Each voice told a story."
    character = {
        "name": "Mara",
        "description": "A lighthouse keeper",
        "quirks": ["Never speaks above a whisper"],
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "structure": ["setup", "complication", "resolution"],
    }
    
    result = scorer.score_story(text, character=character, outline=outline)
    
    assert "overall_score" in result
    assert "dimensions" in result
    assert len(result["dimensions"]) == 4
    
    # All dimensions should be scored
    for dim_name, dim_data in result["dimensions"].items():
        assert "score" in dim_data
        assert "status" in dim_data
        assert 0.0 <= dim_data["score"] <= 1.0


def test_dimension_score_dataclass():
    """Test DimensionScore dataclass initialization."""
    score = DimensionScore(
        name="Test Dimension",
        score=0.75,
        issues=[{"type": "test", "message": "Test issue"}],
        strengths=["Test strength"]
    )
    
    assert score.name == "Test Dimension"
    assert score.score == 0.75
    assert len(score.issues) == 1
    assert len(score.strengths) == 1


def test_dimension_score_defaults():
    """Test DimensionScore with default values."""
    score = DimensionScore(name="Test", score=0.5)
    
    assert score.issues == []
    assert score.strengths == []
    assert score.max_score == 1.0

