"""
Negative test cases for edge cases and error conditions.

This module addresses the issue: "Lack of assertions for negative cases"
by testing invalid inputs, missing fields, and error conditions across
the pipeline stages.
"""

import pytest
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.utils.errors import ValidationError


class TestPremiseNegativeCases:
    """Negative test cases for premise capture."""
    
    def test_capture_premise_empty_idea(self, basic_pipeline):
        """Test that empty idea raises ValidationError."""
        pipeline = basic_pipeline
        
        # Verify pipeline state before error
        original_premise = pipeline.premise
        
        with pytest.raises(ValidationError, match="idea") as exc_info:
            pipeline.capture_premise(
                idea="",
                character={"name": "Test", "description": "A test character"},
                theme="Test theme"
            )
        
        # Verify error message contains relevant information
        error_message = str(exc_info.value).lower()
        assert "idea" in error_message or "empty" in error_message or "required" in error_message, \
            "Error message should mention idea or empty/required"
        
        # Verify pipeline state is unchanged after error
        assert pipeline.premise == original_premise, \
            "Pipeline premise should remain unchanged after validation error"
    
    def test_capture_premise_whitespace_only_idea(self, basic_pipeline):
        """Test that whitespace-only idea raises ValidationError."""
        pipeline = basic_pipeline
        
        with pytest.raises(ValidationError, match="idea"):
            pipeline.capture_premise(
                idea="   \n\t  ",
                character={"name": "Test", "description": "A test character"},
                theme="Test theme"
            )
    
    def test_capture_premise_missing_character_description(self, basic_pipeline):
        """Test that character without description raises ValidationError."""
        pipeline = basic_pipeline
        
        with pytest.raises(ValidationError, match="description"):
            pipeline.capture_premise(
                idea="A test story idea",
                character={"name": "Test"},  # Missing description
                theme="Test theme"
            )
    
    def test_capture_premise_invalid_character_type(self, basic_pipeline):
        """Test that invalid character type raises ValidationError."""
        pipeline = basic_pipeline
        
        # Verify pipeline state before error
        original_premise = pipeline.premise
        
        with pytest.raises((ValidationError, TypeError, ValueError)) as exc_info:
            pipeline.capture_premise(
                idea="A test story idea",
                character="not a dict",  # Invalid type
                theme="Test theme"
            )
        
        # Verify specific error type and message content
        error_type = type(exc_info.value).__name__
        error_message = str(exc_info.value).lower()
        assert error_type in ["ValidationError", "TypeError", "ValueError"], \
            f"Should raise ValidationError, TypeError, or ValueError, got {error_type}"
        assert "character" in error_message or "dict" in error_message or "type" in error_message, \
            "Error message should mention character, dict, or type"
        
        # Verify pipeline state is unchanged after error
        assert pipeline.premise == original_premise, \
            "Pipeline premise should remain unchanged after validation error"


class TestOutlineNegativeCases:
    """Negative test cases for outline generation."""
    
    def test_generate_outline_without_premise(self, basic_pipeline):
        """Test that outline generation without premise raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = None
        
        with pytest.raises(ValueError, match="Cannot generate outline without premise"):
            pipeline.generate_outline()
    
    def test_generate_outline_invalid_premise_structure(self, basic_pipeline):
        """Test that invalid premise structure raises error."""
        pipeline = basic_pipeline
        pipeline.premise = {"invalid": "structure"}  # Missing required fields
        
        # Should either raise ValidationError or handle gracefully
        with pytest.raises((ValidationError, ValueError, KeyError)):
            pipeline.generate_outline()


class TestScaffoldNegativeCases:
    """Negative test cases for scaffold generation."""
    
    def test_scaffold_without_outline(self, basic_pipeline, sample_premise):
        """Test that scaffold generation without outline raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.outline = None
        
        with pytest.raises(ValueError, match="Cannot scaffold without outline"):
            pipeline.scaffold()
    
    def test_scaffold_without_premise(self, basic_pipeline, sample_outline):
        """Test that scaffold generation without premise raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = None
        pipeline.outline = sample_outline
        
        with pytest.raises(ValueError, match="Cannot scaffold without premise"):
            pipeline.scaffold()
    
    def test_scaffold_invalid_outline_structure(self, basic_pipeline, sample_premise):
        """Test that invalid outline structure raises error."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.outline = {"invalid": "structure"}  # Missing required fields
        
        # Should either raise ValidationError or handle gracefully
        with pytest.raises((ValidationError, ValueError, KeyError)):
            pipeline.scaffold()


class TestDraftNegativeCases:
    """Negative test cases for draft generation."""
    
    def test_draft_without_scaffold(self, basic_pipeline, sample_premise, sample_outline):
        """Test that draft generation without scaffold raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.outline = sample_outline
        pipeline._scaffold_data = None
        
        with pytest.raises(ValueError, match="Cannot draft without scaffold"):
            pipeline.draft()
    
    def test_draft_without_outline(self, basic_pipeline, sample_premise):
        """Test that draft generation without outline raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.outline = None
        
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "outline": None,
            "genre": "General Fiction",
            "constraints": {}
        }
        
        with pytest.raises(ValueError, match="Cannot draft without outline"):
            pipeline.draft(scaffold=scaffold)
    
    def test_draft_without_premise(self, basic_pipeline, sample_outline):
        """Test that draft generation without premise raises ValueError."""
        pipeline = basic_pipeline
        pipeline.premise = None
        pipeline.outline = sample_outline
        
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "outline": sample_outline,
            "genre": "General Fiction",
            "constraints": {}
        }
        
        with pytest.raises(ValueError, match="Cannot draft without premise"):
            pipeline.draft(scaffold=scaffold)
    
    def test_template_draft_invalid_character(self, basic_pipeline, sample_premise, sample_outline):
        """Test that template draft with invalid character raises error."""
        pipeline = basic_pipeline
        
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "outline": sample_outline,
            "genre": "General Fiction",
            "constraints": {}
        }
        
        # Invalid character (not a dict)
        with pytest.raises((TypeError, ValueError, AttributeError)):
            pipeline._generate_template_draft(
                sample_premise["idea"],
                "not a character dict",  # Invalid type
                sample_premise.get("theme", ""),
                sample_outline,
                scaffold
            )
    
    def test_template_draft_empty_idea(self, basic_pipeline, sample_character, sample_outline):
        """Test that template draft with empty idea raises error."""
        pipeline = basic_pipeline
        
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "outline": sample_outline,
            "genre": "General Fiction",
            "constraints": {}
        }
        
        with pytest.raises((ValueError, AssertionError)):
            pipeline._generate_template_draft(
                "",  # Empty idea
                sample_character,
                "Test theme",
                sample_outline,
                scaffold
            )
    
    def test_template_draft_invalid_outline(self, basic_pipeline, sample_premise, sample_character):
        """Test that template draft with invalid outline raises error."""
        pipeline = basic_pipeline
        
        scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate",
            "outline": None,  # Invalid outline
            "genre": "General Fiction",
            "constraints": {}
        }
        
        with pytest.raises((TypeError, ValueError, AttributeError)):
            pipeline._generate_template_draft(
                sample_premise["idea"],
                sample_character,
                sample_premise.get("theme", ""),
                None,  # Invalid outline
                scaffold
            )


class TestRevisionNegativeCases:
    """Negative test cases for revision."""
    
    def test_revise_without_draft(self, basic_pipeline):
        """Test that revision without draft raises ValueError."""
        pipeline = basic_pipeline
        
        with pytest.raises(ValueError, match="Cannot revise without draft"):
            pipeline.revise()
    
    def test_revise_invalid_draft_structure(self, basic_pipeline):
        """Test that revision with invalid draft structure raises error."""
        pipeline = basic_pipeline
        pipeline._draft_data = {"invalid": "structure"}  # Missing required fields
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            pipeline.revise()
    
    def test_revise_draft_missing_text(self, basic_pipeline):
        """Test that revision with draft missing text field raises error."""
        pipeline = basic_pipeline
        pipeline._draft_data = {"word_count": 100}  # Missing text field
        
        # Verify draft data state before error
        original_draft_data = pipeline._draft_data.copy()
        
        with pytest.raises((ValueError, KeyError)) as exc_info:
            pipeline.revise()
        
        # Verify error message mentions text or required field
        error_message = str(exc_info.value).lower()
        assert "text" in error_message or "required" in error_message or "missing" in error_message, \
            "Error message should mention text, required, or missing field"
        
        # Verify draft data is unchanged after error
        assert pipeline._draft_data == original_draft_data, \
            "Draft data should remain unchanged after error"


class TestPipelineStateNegativeCases:
    """Negative test cases for pipeline state validation."""
    
    def test_pipeline_invalid_genre(self, basic_pipeline, sample_premise):
        """Test that pipeline handles invalid genre gracefully."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.genre = "NonExistentGenre123"
        
        # Should either fallback to default or raise ValidationError
        outline = pipeline.generate_outline()
        assert outline is not None, "Should handle invalid genre gracefully"
        # Should use default genre or the invalid genre name
        assert "genre" in outline
    
    def test_pipeline_missing_genre_config(self, basic_pipeline, sample_premise):
        """Test that pipeline handles missing genre config gracefully."""
        pipeline = basic_pipeline
        pipeline.premise = sample_premise
        pipeline.genre = "General Fiction"
        pipeline.genre_config = None
        
        # Should either use default config or raise error
        # Use explicit assertion pattern instead of try/except that obscures intent
        from src.shortstory.utils.errors import ValidationError
        
        # Test both possible behaviors explicitly
        outline_result = None
        error_raised = None
        
        try:
            outline_result = pipeline.generate_outline()
        except (ValueError, AttributeError, ValidationError) as e:
            error_raised = type(e).__name__
        
        # Explicitly assert one of the expected behaviors occurred
        assert outline_result is not None or error_raised is not None, \
            "Pipeline should either generate outline with default config or raise appropriate error"
        
        # If outline was generated, verify it's valid
        if outline_result is not None:
            assert isinstance(outline_result, dict), "Generated outline should be a dict"
            assert "genre" in outline_result or "acts" in outline_result, \
                "Generated outline should have expected structure"
    
    def test_capture_premise_none_character(self, basic_pipeline):
        """Test that None character raises appropriate error."""
        pipeline = basic_pipeline
        
        with pytest.raises((ValidationError, TypeError, ValueError)) as exc_info:
            pipeline.capture_premise(
                idea="A test story idea",
                character=None,  # None character
                theme="Test theme"
            )
        
        # Verify error is raised with appropriate message
        error_message = str(exc_info.value).lower()
        assert "character" in error_message or "none" in error_message or "required" in error_message, \
            "Error message should mention character, none, or required"
    
    def test_capture_premise_character_missing_name(self, basic_pipeline):
        """Test that character missing name field raises ValidationError."""
        pipeline = basic_pipeline
        
        with pytest.raises(ValidationError, match="name|character") as exc_info:
            pipeline.capture_premise(
                idea="A test story idea",
                character={"description": "A character without a name"},  # Missing name
                theme="Test theme"
            )
        
        # Verify error message mentions name or character
        error_message = str(exc_info.value).lower()
        assert "name" in error_message or "character" in error_message, \
            "Error message should mention name or character"
    
    def test_generate_outline_with_empty_premise_fields(self, basic_pipeline):
        """Test that outline generation with empty premise fields raises error."""
        pipeline = basic_pipeline
        pipeline.premise = {
            "idea": "",  # Empty idea
            "character": {"name": "Test", "description": "A test character"},
            "theme": "Test theme"
        }
        
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            pipeline.generate_outline()
        
        # Verify error message mentions premise or required field
        error_message = str(exc_info.value).lower()
        assert "premise" in error_message or "idea" in error_message or "required" in error_message, \
            "Error message should mention premise, idea, or required field"
    
    def test_revise_with_empty_draft_text(self, basic_pipeline):
        """Test that revision with empty draft text raises error."""
        pipeline = basic_pipeline
        pipeline._draft_data = {"text": "", "word_count": 0}  # Empty text
        
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            pipeline.revise()
        
        # Verify error message mentions text or empty
        error_message = str(exc_info.value).lower()
        assert "text" in error_message or "empty" in error_message or "required" in error_message, \
            "Error message should mention text, empty, or required"
    
    def test_revise_with_invalid_word_count(self, basic_pipeline):
        """Test that revision with invalid word_count type raises error."""
        pipeline = basic_pipeline
        pipeline._draft_data = {
            "text": "Some story text",
            "word_count": "not a number"  # Invalid type
        }
        
        with pytest.raises((TypeError, ValueError)) as exc_info:
            pipeline.revise()
        
        # Verify error is raised
        error_message = str(exc_info.value).lower()
        assert "word_count" in error_message or "type" in error_message or "number" in error_message, \
            "Error message should mention word_count, type, or number"

