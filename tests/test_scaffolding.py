"""
Tests for scaffolding generation functionality.
"""

import pytest
from src.shortstory.utils.llm import generate_scaffold_structure
from src.shortstory.pipeline import ShortStoryPipeline


def test_generate_scaffold_structure_template_fallback():
    """Test scaffold generation with template fallback (no LLM)."""
    premise = {
        "idea": "A lighthouse keeper collects lost voices in glass jars.",
        "character": {"name": "Mara", "description": "A lighthouse keeper"},
        "theme": "What happens to stories we never tell?"
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "beginning": {"hook": "Opening scene", "setup": "Setup details"},
        "middle": {"complication": "The situation deepens"},
        "end": {"resolution": "Resolution occurs"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False  # Force template fallback
    )
    
    assert "narrative_voice" in scaffold
    assert "character_voices" in scaffold
    assert "tone" in scaffold
    assert "conflicts" in scaffold
    assert "sensory_specificity" in scaffold
    assert "style_guidelines" in scaffold
    
    # Check narrative voice structure
    narrative_voice = scaffold["narrative_voice"]
    assert "pov" in narrative_voice
    assert "pov_rationale" in narrative_voice
    assert "prose_style" in narrative_voice
    assert "sentence_rhythm" in narrative_voice
    assert "language_register" in narrative_voice
    assert "voice_characteristics" in narrative_voice
    
    # Check conflicts structure
    conflicts = scaffold["conflicts"]
    assert "internal" in conflicts
    assert "external" in conflicts
    assert "primary_conflict" in conflicts
    assert "conflict_arc" in conflicts


def test_generate_scaffold_structure_with_genre():
    """Test scaffold generation with genre configuration."""
    premise = {
        "idea": "A detective investigates a crime that defies logic.",
        "character": {"name": "Detective", "description": "A seasoned investigator"}
    }
    outline = {
        "acts": {"beginning": "crime setup", "middle": "investigation", "end": "resolution"},
        "middle": {"complication": "The investigation deepens"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        genre="Crime / Noir",
        use_llm=False
    )
    
    assert scaffold is not None
    assert "narrative_voice" in scaffold
    assert "tone" in scaffold
    # Should reflect genre constraints
    tone = scaffold["tone"]
    assert "emotional_register" in tone


def test_generate_scaffold_structure_with_character_quirks():
    """Test scaffold generation incorporates character quirks into voice profiles."""
    premise = {
        "idea": "A story about a unique character.",
        "character": {
            "name": "Mara",
            "description": "A lighthouse keeper",
            "quirks": ["Never speaks above a whisper", "Collects lost voices"],
            "contradictions": "Afraid of silence but works in isolation"
        }
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "middle": {"complication": "Complication"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    assert "character_voices" in scaffold
    character_voices = scaffold["character_voices"]
    
    # Should have voice profile for Mara
    if "Mara" in character_voices:
        mara_voice = character_voices["Mara"]
        assert "voice_markers" in mara_voice
        assert "distinctive_traits" in mara_voice
        
        # Voice markers should reflect quirks
        voice_markers = mara_voice.get("voice_markers", [])
        assert len(voice_markers) > 0


def test_pipeline_scaffold():
    """Test pipeline scaffolding."""
    pipeline = ShortStoryPipeline()
    
    idea = "A lighthouse keeper collects lost voices in glass jars."
    character = {"name": "Mara", "description": "A lighthouse keeper", "quirks": ["Never speaks above a whisper"]}
    theme = "What happens to stories we never tell?"
    
    # Capture premise and generate outline first
    pipeline.capture_premise(idea, character, theme, validate=False)
    pipeline.generate_outline(use_llm=False)
    
    # Generate scaffold
    scaffold = pipeline.scaffold(use_llm=False)
    
    assert scaffold is not None
    assert "outline" in scaffold
    assert "genre" in scaffold
    assert "narrative_voice" in scaffold
    assert "character_voices" in scaffold
    assert "tone" in scaffold
    assert "conflicts" in scaffold
    assert "sensory_specificity" in scaffold
    assert "style_guidelines" in scaffold
    
    # Check that voice profiles are enhanced with character quirks
    character_voices = scaffold.get("character_voices", {})
    if "Mara" in character_voices:
        mara_voice = character_voices["Mara"]
        assert "voice_markers" in mara_voice


def test_pipeline_scaffold_requires_outline():
    """Test that scaffolding requires an outline."""
    pipeline = ShortStoryPipeline()
    
    pipeline.capture_premise("An idea", {"name": "Character"}, "Theme", validate=False)
    
    with pytest.raises(ValueError, match="Cannot scaffold without outline"):
        pipeline.scaffold()


def test_pipeline_scaffold_requires_premise():
    """Test that scaffolding requires a premise."""
    pipeline = ShortStoryPipeline()
    
    # Create a mock outline
    pipeline.outline = {"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}}
    
    with pytest.raises(ValueError, match="Cannot scaffold without premise"):
        pipeline.scaffold()


def test_scaffold_narrative_voice_structure():
    """Test that narrative voice has all required fields."""
    premise = {
        "idea": "A story about transformation.",
        "character": {"name": "Protagonist", "description": "A person who changes"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "middle": {"complication": "Complication"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    narrative_voice = scaffold["narrative_voice"]
    assert "pov" in narrative_voice
    assert "pov_rationale" in narrative_voice
    assert "prose_style" in narrative_voice
    assert "sentence_rhythm" in narrative_voice
    assert "language_register" in narrative_voice
    assert "voice_characteristics" in narrative_voice
    assert isinstance(narrative_voice["voice_characteristics"], list)


def test_scaffold_conflicts_structure():
    """Test that conflicts structure is properly formed."""
    premise = {
        "idea": "A story with conflict.",
        "character": {"name": "Character", "description": "A person"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "beginning": {"hook": "Opening"},
        "middle": {"complication": "The main complication"},
        "end": {"resolution": "Resolution"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    conflicts = scaffold["conflicts"]
    assert "internal" in conflicts
    assert "external" in conflicts
    assert "primary_conflict" in conflicts
    assert "conflict_arc" in conflicts
    
    assert isinstance(conflicts["internal"], list)
    assert isinstance(conflicts["external"], list)
    assert len(conflicts["internal"]) > 0
    assert len(conflicts["external"]) > 0


def test_scaffold_sensory_specificity():
    """Test that sensory specificity is properly structured."""
    premise = {
        "idea": "A story with sensory details.",
        "character": {"name": "Character", "description": "A person"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        genre="Horror",  # Horror emphasizes specific senses
        use_llm=False
    )
    
    sensory = scaffold["sensory_specificity"]
    assert "primary_senses" in sensory
    assert "sensory_details" in sensory
    
    assert isinstance(sensory["primary_senses"], list)
    assert len(sensory["primary_senses"]) > 0
    assert isinstance(sensory["sensory_details"], dict)


def test_scaffold_style_guidelines():
    """Test that style guidelines are properly structured."""
    premise = {
        "idea": "A story with style.",
        "character": {"name": "Character", "description": "A person"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    style = scaffold["style_guidelines"]
    assert "sentence_length" in style
    assert "dialogue_ratio" in style
    assert "description_density" in style
    assert "pacing" in style


def test_scaffold_tone_structure():
    """Test that tone structure is properly formed."""
    premise = {
        "idea": "A story with tone.",
        "character": {"name": "Character", "description": "A person"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    tone = scaffold["tone"]
    assert "emotional_register" in tone
    assert "mood" in tone
    assert "atmosphere" in tone
    assert "emotional_arc" in tone


def test_scaffold_backward_compatibility():
    """Test that scaffold maintains backward compatibility fields."""
    pipeline = ShortStoryPipeline()
    
    idea = "A story."
    character = {"name": "Character", "description": "A person"}
    
    pipeline.capture_premise(idea, character, None, validate=False)
    pipeline.generate_outline(use_llm=False)
    scaffold = pipeline.scaffold(use_llm=False)
    
    # Backward compatibility fields
    assert "pov" in scaffold
    assert "tone" in scaffold
    assert "pace" in scaffold
    assert "voice" in scaffold
    assert "sensory_focus" in scaffold
    assert "distinctiveness_required" in scaffold
    assert "anti_generic_enforced" in scaffold


def test_scaffold_with_voice_opportunities():
    """Test that scaffold uses voice opportunities from outline."""
    premise = {
        "idea": "A story with voice opportunities.",
        "character": {"name": "Character", "description": "A person"}
    }
    outline = {
        "acts": {"beginning": "setup", "middle": "complication", "end": "resolution"},
        "voice_opportunities": ["Dialogue scene", "Internal moment"]
    }
    
    scaffold = generate_scaffold_structure(
        premise=premise,
        outline=outline,
        use_llm=False
    )
    
    # Scaffold should be generated successfully
    assert scaffold is not None
    assert "narrative_voice" in scaffold

