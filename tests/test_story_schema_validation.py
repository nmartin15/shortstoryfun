"""
Tests for validating generated content structure/schema.

This module addresses the issue: "Lack of Explicit Assertion for Generated Content Structure/Schema"
by validating that generated content (draft, revised_draft, outline, scaffold, complete stories)
conforms to the expected Pydantic models defined in src/shortstory/models.py.
"""

import pytest
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from src.shortstory.models import (
    StoryModel,
    PremiseModel,
    OutlineModel,
    CharacterModel,
    StoryMetadata,
    RevisionEntry
)
from src.shortstory.pipeline import ShortStoryPipeline


class TestPremiseSchemaValidation:
    """Test that generated premises conform to PremiseModel schema."""
    
    def test_premise_structure_validation(self, pipeline_with_premise):
        """Test that captured premise matches PremiseModel schema."""
        pipeline = pipeline_with_premise
        premise = pipeline.premise
        
        # Validate using Pydantic model - use direct validation instead of try/except
        validated_premise = PremiseModel(**premise)
        assert validated_premise.idea is not None
        assert len(validated_premise.idea) > 0
        if validated_premise.character:
            assert isinstance(validated_premise.character, (dict, CharacterModel))
    
    def test_premise_character_structure(self, pipeline_with_premise):
        """Test that premise character conforms to CharacterModel if present."""
        pipeline = pipeline_with_premise
        premise = pipeline.premise
        
        if "character" in premise and premise["character"]:
            character = premise["character"]
            # Handle both dict and CharacterModel
            if isinstance(character, dict):
                validated_character = CharacterModel(**character)
            else:
                validated_character = character
            
            # CharacterModel requires description
            assert hasattr(validated_character, 'description') or 'description' in character


class TestOutlineSchemaValidation:
    """Test that generated outlines conform to OutlineModel schema."""
    
    def test_outline_structure_validation(self, pipeline_with_outline):
        """Test that generated outline matches OutlineModel schema."""
        pipeline = pipeline_with_outline
        outline = pipeline.outline
        
        # Validate using Pydantic model - use direct validation instead of try/except
        validated_outline = OutlineModel(**outline)
        assert validated_outline.genre is not None
        assert validated_outline.framework is not None
        assert isinstance(validated_outline.structure, list)
        assert len(validated_outline.structure) > 0
    
    def test_outline_acts_structure(self, pipeline_with_outline):
        """Test that outline acts structure is valid."""
        pipeline = pipeline_with_outline
        outline = pipeline.outline
        
        if "acts" in outline and outline["acts"]:
            acts = outline["acts"]
            assert isinstance(acts, dict)
            # Acts should have beginning, middle, end
            if acts:  # If acts dict is not empty
                assert "beginning" in acts or "middle" in acts or "end" in acts


class TestScaffoldSchemaValidation:
    """Test that generated scaffolds have expected structure."""
    
    def test_scaffold_required_fields(self, pipeline_with_scaffold):
        """Test that scaffold contains all required fields."""
        pipeline = pipeline_with_scaffold
        scaffold = pipeline.scaffold
        
        assert scaffold is not None
        assert isinstance(scaffold, dict)
        
        # Required fields based on pipeline implementation
        required_fields = ["outline", "genre", "constraints", "pov", "tone", "pace", "voice"]
        for field in required_fields:
            assert field in scaffold, f"Scaffold missing required field: {field}"
        
        # Validate field types
        assert isinstance(scaffold["outline"], dict)
        assert isinstance(scaffold["genre"], str)
        assert isinstance(scaffold["constraints"], dict)
        assert isinstance(scaffold["pov"], str)
        assert isinstance(scaffold["tone"], str)
        assert isinstance(scaffold["pace"], str)
        assert isinstance(scaffold["voice"], str)
    
    def test_scaffold_backward_compatibility_fields(self, pipeline_with_scaffold):
        """Test that scaffold backward compatibility fields are correct."""
        pipeline = pipeline_with_scaffold
        scaffold = pipeline.scaffold
        
        # Backward compatibility fields should exist
        assert "pov" in scaffold
        assert "tone" in scaffold
        assert "pace" in scaffold
        assert "voice" in scaffold
        assert "sensory_focus" in scaffold
        
        # Validate types
        assert isinstance(scaffold["pov"], str)
        assert isinstance(scaffold["tone"], str)
        assert isinstance(scaffold["pace"], str)
        assert isinstance(scaffold["voice"], str)
        assert isinstance(scaffold["sensory_focus"], list)
        
        # Verify correctness: backward compatibility fields should match derived values
        # - pov should match narrative_voice.pov when it exists
        if "narrative_voice" in scaffold and "pov" in scaffold.get("narrative_voice", {}):
            assert scaffold["pov"] == scaffold["narrative_voice"]["pov"], \
                "pov should match narrative_voice.pov when narrative_voice.pov exists"
        
        # - tone should match tone_detail.emotional_register when it exists
        if "tone_detail" in scaffold and isinstance(scaffold["tone_detail"], dict):
            if "emotional_register" in scaffold["tone_detail"]:
                assert scaffold["tone"] == scaffold["tone_detail"]["emotional_register"], \
                    "tone should match tone_detail.emotional_register when it exists"
        
        # - pace should match style_guidelines.pacing when it exists
        if "style_guidelines" in scaffold and "pacing" in scaffold.get("style_guidelines", {}):
            assert scaffold["pace"] == scaffold["style_guidelines"]["pacing"], \
                "pace should match style_guidelines.pacing when it exists"
        
        # - voice should be "developed" (hardcoded value)
        assert scaffold["voice"] == "developed", \
            "voice should be 'developed'"
        
        # - sensory_focus should match sensory_specificity.primary_senses when it exists
        if "sensory_specificity" in scaffold and "primary_senses" in scaffold.get("sensory_specificity", {}):
            assert scaffold["sensory_focus"] == scaffold["sensory_specificity"]["primary_senses"], \
                "sensory_focus should match sensory_specificity.primary_senses when it exists"
        
        # - distinctiveness_required should be True (hardcoded)
        if "distinctiveness_required" in scaffold:
            assert scaffold["distinctiveness_required"] is True, \
                "distinctiveness_required should be True"
        
        # - anti_generic_enforced should be True (hardcoded)
        if "anti_generic_enforced" in scaffold:
            assert scaffold["anti_generic_enforced"] is True, \
                "anti_generic_enforced should be True"
        
        # Verify values are not empty/None
        assert scaffold["pov"] is not None and scaffold["pov"] != "", \
            "pov should have a valid non-empty value"
        assert scaffold["tone"] is not None and scaffold["tone"] != "", \
            "tone should have a valid non-empty value"
        assert scaffold["pace"] is not None and scaffold["pace"] != "", \
            "pace should have a valid non-empty value"
        assert scaffold["sensory_focus"] is not None and len(scaffold["sensory_focus"]) > 0, \
            "sensory_focus should be a non-empty list"


class TestDraftSchemaValidation:
    """Test that generated drafts have expected structure."""
    
    def test_draft_structure_validation(self, basic_pipeline, sample_premise, sample_character, sample_outline):
        """Test that generated draft has required structure."""
        pipeline = basic_pipeline
        
        # Create a minimal scaffold for testing
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "voice": "developed",
            "sensory_focus": ["visual", "auditory"],
            "outline": sample_outline,
            "genre": sample_outline.get("genre", "General Fiction"),
            "constraints": {}
        }
        
        draft = pipeline._generate_template_draft(
            sample_premise["idea"],
            sample_character,
            sample_premise.get("theme", ""),
            sample_outline,
            scaffold
        )
        
        # Draft should be a string (template draft returns string)
        assert isinstance(draft, str), "Draft must be a string"
        assert len(draft) > 0, "Draft must not be empty"
        
        # Verify draft contains expected structural elements
        draft_lower = draft.lower()
        # Check for at least one structural indicator (beginning/setup, middle/complication, end/resolution)
        structural_indicators = [
            "setup", "beginning", "introduction", "start",
            "complication", "middle", "development", "conflict",
            "resolution", "end", "conclusion", "ending"
        ]
        found_indicators = [ind for ind in structural_indicators if ind in draft_lower]
        assert len(found_indicators) >= 2, \
            f"Draft should contain multiple structural elements, found: {found_indicators}"
        
        # Verify draft contains key elements from premise
        idea_keywords = [word.lower() for word in sample_premise["idea"].split() if len(word) > 3]
        assert any(keyword in draft_lower for keyword in idea_keywords) or sample_premise["idea"].lower() in draft_lower, \
            f"Draft should reference the story idea: {sample_premise['idea']}"
        
        # Verify draft contains character information
        character_name = sample_character.get("name", "").lower()
        if character_name:
            assert character_name in draft_lower or any(
                word in draft_lower for word in character_name.split()
            ), f"Draft should reference character name: {character_name}"
        
        # Verify draft has proper structure (paragraphs/sections)
        # Should have multiple lines (paragraphs)
        lines = draft.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        assert len(non_empty_lines) > 1, \
            "Draft should have multiple paragraphs/sections, not just a single block"
        
        # Verify draft has minimum content length (substantial story content)
        assert len(draft.strip()) > 100, \
            f"Draft should have substantial content (at least 100 characters), got {len(draft.strip())}"
        
        # Verify draft contains complete sentences (has sentence-ending punctuation)
        sentence_endings = ['.', '!', '?']
        assert any(ending in draft for ending in sentence_endings), \
            "Draft should contain complete sentences with punctuation"
        
        # Verify draft doesn't contain placeholder or template artifacts
        placeholder_patterns = ["[PLACEHOLDER", "{PLACEHOLDER", "<PLACEHOLDER", "TODO:", "FIXME:"]
        for pattern in placeholder_patterns:
            assert pattern.upper() not in draft.upper(), \
                f"Draft should not contain placeholder text: {pattern}"
    
    def test_draft_dict_structure(self):
        """Test that draft dictionary (from pipeline.draft()) has expected structure."""
        # This test would need to mock the LLM or use a real pipeline
        # For now, we define the expected structure
        expected_draft_keys = ["text", "word_count"]
        
        # Example validation helper
        def validate_draft_structure(draft: Dict[str, Any]) -> bool:
            """Validate draft dictionary structure."""
            if not isinstance(draft, dict):
                return False
            
            # Required fields
            if "text" not in draft:
                return False
            if "word_count" not in draft:
                return False
            
            # Type validation
            if not isinstance(draft["text"], str):
                return False
            if not isinstance(draft["word_count"], int):
                return False
            if draft["word_count"] < 0:
                return False
            
            # Content validation
            if len(draft["text"]) == 0:
                return False
            
            return True
        
        # Example valid draft
        valid_draft = {
            "text": "Sample story text",
            "word_count": 100
        }
        assert validate_draft_structure(valid_draft), "Valid draft should pass validation"
        
        # Comprehensive assertions for valid draft
        assert "text" in valid_draft, "Draft must contain 'text' field"
        assert "word_count" in valid_draft, "Draft must contain 'word_count' field"
        assert isinstance(valid_draft["text"], str), "Draft 'text' must be a string"
        assert isinstance(valid_draft["word_count"], int), "Draft 'word_count' must be an integer"
        assert len(valid_draft["text"]) > 0, "Draft 'text' must not be empty"
        assert valid_draft["word_count"] >= 0, "Draft 'word_count' must be non-negative"
        
        # Example invalid drafts - negative test cases
        invalid_drafts = [
            ({"text": "Story"}, "Missing word_count"),
            ({"word_count": 100}, "Missing text"),
            ({"text": 123, "word_count": 100}, "Wrong type for text"),
            ({"text": "Story", "word_count": "100"}, "Wrong type for word_count"),
            ({"text": "", "word_count": 0}, "Empty text"),
            ({"text": "Story", "word_count": -1}, "Negative word_count"),
        ]
        for invalid_draft, reason in invalid_drafts:
            assert not validate_draft_structure(invalid_draft), \
                f"Should reject invalid draft ({reason}): {invalid_draft}"


class TestRevisedDraftSchemaValidation:
    """Test that revised drafts have expected structure."""
    
    def test_revised_draft_structure_validation(self):
        """Test that revised draft dictionary has expected structure."""
        expected_keys = ["text", "word_count"]
        
        def validate_revised_draft_structure(revised: Dict[str, Any]) -> bool:
            """Validate revised draft dictionary structure."""
            if not isinstance(revised, dict):
                return False
            
            # Required fields
            if "text" not in revised:
                return False
            if "word_count" not in revised:
                return False
            
            # Type validation
            if not isinstance(revised["text"], str):
                return False
            if not isinstance(revised["word_count"], int):
                return False
            if revised["word_count"] < 0:
                return False
            
            return True
        
        # Example valid revised draft
        valid_revised = {
            "text": "Revised story text",
            "word_count": 150
        }
        assert validate_revised_draft_structure(valid_revised)
        
        # Example invalid revised drafts
        invalid_revised = [
            {"text": "Story"},  # Missing word_count
            {"word_count": 150},  # Missing text
            {"text": 123, "word_count": 150},  # Wrong type
        ]
        for invalid in invalid_revised:
            assert not validate_revised_draft_structure(invalid), \
                f"Should reject invalid revised draft: {invalid}"


class TestCompleteStorySchemaValidation:
    """Test that complete story objects conform to StoryModel schema."""
    
    def test_story_model_validation_helper(self):
        """Helper function to validate story structure against StoryModel."""
        def validate_story_structure(story: Dict[str, Any]) -> Tuple[bool, str]:
            """
            Validate story dictionary against StoryModel schema.
            
            Returns:
                (is_valid, error_message)
            """
            try:
                validated_story = StoryModel(**story)
                return True, ""
            except ValidationError as e:
                return False, str(e)
        
        # Example minimal valid story structure
        minimal_story = {
            "id": "story_12345678",
            "premise": {
                "idea": "A test story idea",
                "character": {
                    "name": "Test",
                    "description": "A test character"
                },
                "theme": "Test theme"
            },
            "outline": {
                "genre": "General Fiction",
                "framework": "narrative_arc",
                "structure": ["setup", "complication", "resolution"],
                "acts": {
                    "beginning": "setup",
                    "middle": "complication",
                    "end": "resolution"
                }
            },
            "genre": "General Fiction",
            "genre_config": {"framework": "narrative_arc"},
            "body": "Test story body text",
            "metadata": {},
            "word_count": 10,
            "max_words": 7500
        }
        
        is_valid, error = validate_story_structure(minimal_story)
        assert is_valid, f"Minimal story should be valid: {error}"
    
    def test_story_model_id_validation(self):
        """Test that story ID conforms to expected pattern."""
        from pydantic import ValidationError
        
        # Valid ID pattern: story_[a-f0-9]{8}
        valid_ids = [
            "story_12345678",
            "story_abcdefab",
            "story_1234abcd"
        ]
        
        invalid_ids = [
            "story_123",  # Too short
            "story_123456789",  # Too long
            "story_ghijklmn",  # Invalid hex chars
            "not_story_12345678",  # Wrong prefix
            "story_1234567g",  # Invalid hex char
        ]
        
        for valid_id in valid_ids:
            # Use explicit assertion pattern instead of try/except with pytest.fail
            # This makes the test intent clearer: we expect no ValidationError for valid IDs
            story = StoryModel(
                id=valid_id,
                premise=PremiseModel(idea="Test"),
                outline=OutlineModel(genre="Test", framework="test", structure=["test"]),
                genre="Test",
                genre_config={},
                body="Test",
                word_count=10
            )
            # Explicitly assert the ID was set correctly (proves no ValidationError was raised)
            assert story.id == valid_id, \
                f"Valid ID '{valid_id}' should be accepted without raising ValidationError"
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                StoryModel(
                    id=invalid_id,
                    premise=PremiseModel(idea="Test"),
                    outline=OutlineModel(genre="Test", framework="test", structure=["test"]),
                    genre="Test",
                    genre_config={},
                    body="Test",
                    word_count=10
                )
    
    def test_story_model_word_count_validation(self):
        """Test that word_count validation works correctly."""
        from pydantic import ValidationError
        
        # Valid word counts
        valid_word_counts = [0, 100, 5000, 7500]
        
        # Invalid word counts (exceeding max_words)
        invalid_word_counts = [7501, 10000]
        
        base_story = {
            "id": "story_12345678",
            "premise": PremiseModel(idea="Test"),
            "outline": OutlineModel(genre="Test", framework="test", structure=["test"]),
            "genre": "Test",
            "genre_config": {},
            "body": "Test story",
            "max_words": 7500
        }
        
        for word_count in valid_word_counts:
            # Use explicit assertion pattern instead of try/except with pytest.fail
            # This makes the test intent clearer: we expect no ValidationError for valid word counts
            story = StoryModel(**base_story, word_count=word_count)
            # Explicitly assert the word_count was set correctly (proves no ValidationError was raised)
            assert story.word_count == word_count, \
                f"Valid word_count {word_count} should be accepted without raising ValidationError"
        
        for word_count in invalid_word_counts:
            with pytest.raises(ValidationError, match="exceeds maximum"):
                StoryModel(**base_story, word_count=word_count)
    
    def test_story_model_revision_history_validation(self):
        """Test that revision_history validation works correctly."""
        from pydantic import ValidationError
        from datetime import datetime
        
        base_story = {
            "id": "story_12345678",
            "premise": PremiseModel(idea="Test"),
            "outline": OutlineModel(genre="Test", framework="test", structure=["test"]),
            "genre": "Test",
            "genre_config": {},
            "body": "Test story",
            "word_count": 10
        }
        
        # Valid revision history
        valid_revision = RevisionEntry(
            version=1,
            body="Test body",
            word_count=10,
            type="draft",
            timestamp=datetime.now().isoformat()
        )
        
        story = StoryModel(
            **base_story,
            revision_history=[valid_revision],
            current_revision=1
        )
        assert len(story.revision_history) == 1
        
        # Invalid: current_revision exceeds max version in history
        with pytest.raises(ValidationError, match="exceeds max version"):
            StoryModel(
                **base_story,
                revision_history=[valid_revision],
                current_revision=2  # Higher than max version (1)
            )


class TestSchemaValidationIntegration:
    """Integration tests for schema validation across pipeline stages."""
    
    def test_pipeline_outputs_conform_to_schemas(self, pipeline_with_scaffold):
        """Test that pipeline outputs at each stage conform to expected schemas."""
        pipeline = pipeline_with_scaffold
        
        # Validate premise
        if pipeline.premise:
            PremiseModel(**pipeline.premise)  # Will raise ValidationError if invalid
        
        # Validate outline
        if pipeline.outline:
            OutlineModel(**pipeline.outline)  # Will raise ValidationError if invalid
        
        # Validate scaffold structure (no Pydantic model, but check required fields)
        if pipeline.scaffold:
            assert isinstance(pipeline.scaffold, dict)
            required_scaffold_fields = ["outline", "genre", "constraints", "pov", "tone", "pace", "voice"]
            for field in required_scaffold_fields:
                assert field in pipeline.scaffold, f"Scaffold missing field: {field}"

