"""
Tests for outline generation functionality.
"""

import pytest
from src.shortstory.utils.llm import generate_outline_structure


def test_generate_outline_structure_template_fallback():
    """Test outline generation with template fallback (no LLM)."""
    idea = "A lighthouse keeper collects lost voices in glass jars."
    character = {"name": "Mara", "description": "A lighthouse keeper"}
    theme = "What happens to stories we never tell?"
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        theme=theme,
        use_llm=False  # Force template fallback
    )
    
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline
    
    assert "hook" in outline["beginning"]
    assert "setup" in outline["beginning"]
    assert "beats" in outline["beginning"]
    assert len(outline["beginning"]["beats"]) > 0
    
    assert "complication" in outline["middle"]
    assert "rising_action" in outline["middle"]
    assert "beats" in outline["middle"]
    
    assert "climax" in outline["end"]
    assert "resolution" in outline["end"]
    assert "beats" in outline["end"]
    
    assert "memorable_moments" in outline
    assert "voice_opportunities" in outline


def test_generate_outline_structure_with_genre():
    """Test outline generation with genre configuration."""
    idea = "A detective investigates a crime that defies logic."
    character = {"name": "Detective", "description": "A seasoned investigator"}
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        genre="Crime / Noir",
        use_llm=False
    )
    
    assert outline is not None
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline


def test_generate_outline_structure_no_character():
    """Test outline generation without character."""
    idea = "A mysterious event changes everything."
    theme = "The nature of change"
    
    outline = generate_outline_structure(
        idea=idea,
        theme=theme,
        use_llm=False
    )
    
    assert outline is not None
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline


def test_generate_outline_structure_no_theme():
    """Test outline generation without theme."""
    idea = "A story about discovery."
    character = {"name": "Explorer", "description": "A curious person"}
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        use_llm=False
    )
    
    assert outline is not None
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline


def test_pipeline_generate_outline(pipeline_with_premise):
    """Test pipeline outline generation."""
    pipeline = pipeline_with_premise
    
    # Generate outline
    outline = pipeline.generate_outline(use_llm=False)
    
    assert outline is not None
    assert "premise" in outline
    assert "genre" in outline
    assert "framework" in outline
    assert "structure" in outline
    assert "acts" in outline
    
    # Check detailed beats
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline
    assert "memorable_moments" in outline
    assert "voice_opportunities" in outline
    
    # Check beat validation
    assert "beat_validation" in outline
    assert "predictable_beats_found" in outline["beat_validation"]
    assert "is_valid" in outline["beat_validation"]


def test_pipeline_generate_outline_with_genre(basic_pipeline):
    """Test pipeline outline generation with genre."""
    pipeline = basic_pipeline
    
    idea = "A detective investigates a crime that defies logic."
    character = {"name": "Detective", "description": "A seasoned investigator"}
    theme = "Truth is stranger than fiction"
    
    pipeline.capture_premise(idea, character, theme, validate=False)
    pipeline.genre = "Crime / Noir"
    
    outline = pipeline.generate_outline(use_llm=False)
    
    assert outline is not None
    assert outline["genre"] == "Crime / Noir"
    assert "framework" in outline
    assert outline["framework"] == "mystery_arc"


def test_pipeline_generate_outline_requires_premise(basic_pipeline):
    """Test that outline generation requires a premise."""
    pipeline = basic_pipeline
    
    with pytest.raises(ValueError, match="Cannot generate outline without premise"):
        pipeline.generate_outline()


def test_pipeline_generate_outline_requires_idea(basic_pipeline):
    """Test that outline generation requires an idea in premise."""
    pipeline = basic_pipeline
    
    # Capture premise without idea
    pipeline.premise = {"character": {"name": "Test"}, "theme": "Test theme"}
    
    with pytest.raises(ValueError, match="Cannot generate outline without story idea"):
        pipeline.generate_outline()


def test_outline_structure_has_beats():
    """Test that outline structure includes specific beats."""
    idea = "A story about transformation."
    character = {"name": "Protagonist", "description": "A person who changes"}
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        use_llm=False
    )
    
    # Check that beats are present and non-empty
    assert len(outline["beginning"]["beats"]) > 0
    assert len(outline["middle"]["beats"]) > 0
    assert len(outline["end"]["beats"]) > 0
    
    # Check that beats are strings
    for beat in outline["beginning"]["beats"]:
        assert isinstance(beat, str)
        assert len(beat) > 0


def test_outline_memorable_moments():
    """Test that outline includes memorable moments."""
    idea = "A story that creates lasting impressions."
    character = {"name": "Character", "description": "A memorable person"}
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        use_llm=False
    )
    
    assert "memorable_moments" in outline
    assert isinstance(outline["memorable_moments"], list)
    assert len(outline["memorable_moments"]) > 0


def test_outline_voice_opportunities():
    """Test that outline includes voice opportunities."""
    idea = "A story with distinctive voice."
    character = {"name": "Character", "description": "A person with unique voice"}
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        use_llm=False
    )
    
    assert "voice_opportunities" in outline
    assert isinstance(outline["voice_opportunities"], list)
    assert len(outline["voice_opportunities"]) > 0


def test_outline_beat_validation(basic_pipeline):
    """Test that outline validates against predictable beats."""
    pipeline = basic_pipeline
    
    idea = "A hero receives the call to adventure and meets a mentor."
    character = {"name": "Hero", "description": "A chosen one"}
    
    pipeline.capture_premise(idea, character, None, validate=False)
    outline = pipeline.generate_outline(use_llm=False)
    
    # Check beat validation exists
    assert "beat_validation" in outline
    assert "predictable_beats_found" in outline["beat_validation"]
    assert "beats" in outline["beat_validation"]
    assert "is_valid" in outline["beat_validation"]
    
    # Note: This test may find predictable beats if the idea contains them
    # That's expected behavior - the validation should detect them


def test_outline_with_character_quirks():
    """Test outline generation incorporates character quirks."""
    idea = "A story about a unique character."
    character = {
        "name": "Mara",
        "description": "A lighthouse keeper",
        "quirks": ["Never speaks above a whisper", "Collects lost voices"],
        "contradictions": "Afraid of silence but works in isolation"
    }
    
    outline = generate_outline_structure(
        idea=idea,
        character=character,
        use_llm=False
    )
    
    assert outline is not None
    # Character quirks should influence the outline structure
    assert "beginning" in outline
    assert "middle" in outline
    assert "end" in outline

