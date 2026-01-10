"""
Tests for story scaffolding functionality.
"""

import pytest


def test_scaffold_backward_compatibility(pipeline_with_outline):
    """Test that scaffold maintains backward compatibility fields with correct values."""
    pipeline = pipeline_with_outline
    
    idea = "A story with a clear tone and pacing."
    character = {"name": "Character", "description": "A person who is always hurried"}
    theme = "The rush of modern life"
    
    pipeline.capture_premise(idea, character, theme, validate=False)
    pipeline.generate_outline(use_llm=False)
    scaffold = pipeline.scaffold(use_llm=False)
    
    # Backward compatibility fields - check existence
    assert "pov" in scaffold
    assert "tone" in scaffold
    assert "pace" in scaffold
    assert "voice" in scaffold
    assert "sensory_focus" in scaffold
    assert "distinctiveness_required" in scaffold
    assert "anti_generic_enforced" in scaffold
    
    # Verify that backward compatibility fields have correct values derived from detailed scaffold
    # Based on pipeline.py lines 326-360:
    # - pov comes from metadata.pov which is derived from narrative_voice.pov (or constraints default)
    if "narrative_voice" in scaffold and "pov" in scaffold.get("narrative_voice", {}):
        assert scaffold["pov"] == scaffold["narrative_voice"]["pov"], \
            "pov should match narrative_voice.pov when narrative_voice.pov exists"
    # If narrative_voice doesn't exist, pov should still be valid (comes from constraints default)
    assert isinstance(scaffold["pov"], str) and len(scaffold["pov"]) > 0, \
        "pov must be a non-empty string"
    
    # - tone comes from metadata.tone which is derived from tone_detail.emotional_register (or constraints default)
    # tone_detail is set to detailed_scaffold.get("tone", {}) which might be a dict or might not exist
    if "tone_detail" in scaffold and isinstance(scaffold["tone_detail"], dict):
        if "emotional_register" in scaffold["tone_detail"]:
            assert scaffold["tone"] == scaffold["tone_detail"]["emotional_register"], \
                "tone should match tone_detail.emotional_register when it exists"
    # If tone_detail doesn't exist or doesn't have emotional_register, tone should still be valid (from constraints)
    assert isinstance(scaffold["tone"], str) and len(scaffold["tone"]) > 0, \
        "tone must be a non-empty string"
    
    # - pace comes from metadata.pace which is derived from style_guidelines.pacing (or constraints default)
    if "style_guidelines" in scaffold and "pacing" in scaffold.get("style_guidelines", {}):
        assert scaffold["pace"] == scaffold["style_guidelines"]["pacing"], \
            "pace should match style_guidelines.pacing when it exists"
    # If style_guidelines doesn't exist, pace should still be valid (from constraints)
    assert isinstance(scaffold["pace"], str) and len(scaffold["pace"]) > 0, \
        "pace must be a non-empty string"
    
    # - voice is hardcoded to "developed"
    assert scaffold["voice"] == "developed", \
        "voice should be 'developed'"
    
    # - sensory_focus comes from sensory_specificity.primary_senses (or constraints default)
    if "sensory_specificity" in scaffold and "primary_senses" in scaffold.get("sensory_specificity", {}):
        assert scaffold["sensory_focus"] == scaffold["sensory_specificity"]["primary_senses"], \
            "sensory_focus should match sensory_specificity.primary_senses when it exists"
    # If sensory_specificity doesn't exist, sensory_focus should still be valid (from constraints)
    assert isinstance(scaffold["sensory_focus"], list) and len(scaffold["sensory_focus"]) > 0, \
        "sensory_focus must be a non-empty list"
    
    # - distinctiveness_required is hardcoded to True
    assert scaffold["distinctiveness_required"] is True, \
        "distinctiveness_required should be True"
    
    # - anti_generic_enforced is hardcoded to True
    assert scaffold["anti_generic_enforced"] is True, \
        "anti_generic_enforced should be True"
    
    # Verify that backward compatibility fields are not empty or None
    assert scaffold["pov"] is not None and scaffold["pov"] != "", \
        "pov should have a valid value"
    assert scaffold["tone"] is not None and scaffold["tone"] != "", \
        "tone should have a valid value"
    assert scaffold["pace"] is not None and scaffold["pace"] != "", \
        "pace should have a valid value"
    assert scaffold["sensory_focus"] is not None, \
        "sensory_focus should have a valid value"
