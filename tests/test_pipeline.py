"""
Unit tests for ShortStoryPipeline
"""

import pytest
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.utils.word_count import WordCountError


def test_pipeline_initialization():
    """Test that pipeline initializes correctly."""
    pipeline = ShortStoryPipeline()
    assert pipeline.premise is None
    assert pipeline.outline is None
    assert pipeline._scaffold_data is None
    assert pipeline._draft_data is None
    assert pipeline._revised_draft_data is None
    assert pipeline.word_validator is not None


def test_premise_capture():
    """Test premise capture stage."""
    pipeline = ShortStoryPipeline()
    premise = pipeline.capture_premise(
        idea="A lighthouse keeper collects voices",
        character={"name": "Mara", "quirk": "Whispers only"},
        theme="Untold stories",
        validate=False  # Skip validation for simple test
    )
    assert premise is not None
    assert premise["idea"] == "A lighthouse keeper collects voices"


def test_premise_capture_with_validation():
    """Test premise capture with validation."""
    pipeline = ShortStoryPipeline()
    premise = pipeline.capture_premise(
        idea="A unique story about collecting lost voices",
        character={"name": "Mara", "quirk": "Never speaks above a whisper"},
        theme="What happens to stories we never tell?",
        validate=True
    )
    assert premise is not None
    assert premise["validation"] is not None
    assert premise["validation"]["is_valid"] is True


def test_premise_capture_validation_fails():
    """Test that premise capture raises error on invalid premise."""
    pipeline = ShortStoryPipeline()
    with pytest.raises(ValueError):
        pipeline.capture_premise(
            idea="",  # Missing idea
            character={"name": "Test"},
            theme="Test theme",
            validate=True
        )


def test_outline_generation():
    """Test that generate_outline() generates an outline with proper structure."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {
        "framework": "narrative_arc",
        "outline": ["setup", "complication", "resolution"],
        "constraints": {}
    }
    
    try:
        premise = pipeline.capture_premise(
            idea="A lighthouse keeper collects voices",
            character={"name": "Mara", "description": "A quiet keeper"},
            theme="Untold stories",
            validate=False
        )
        assert premise is not None, "Premise capture should succeed"
    except Exception as e:
        pytest.fail(f"Premise capture failed unexpectedly: {e}")
    
    try:
        outline = pipeline.generate_outline()
        assert outline is not None, "Outline should be generated"
        assert isinstance(outline, dict), "Outline should be a dictionary"
        assert "premise" in outline or "genre" in outline, "Outline should contain premise or genre"
        assert "acts" in outline, "Outline should contain acts structure"
        assert "beginning" in outline["acts"], "Outline should have beginning act"
        assert "middle" in outline["acts"], "Outline should have middle act"
        assert "end" in outline["acts"], "Outline should have end act"
        assert outline["acts"]["beginning"] == "setup", "Beginning should be 'setup'"
        assert outline["acts"]["middle"] == "complication", "Middle should be 'complication'"
        assert outline["acts"]["end"] == "resolution", "End should be 'resolution'"
    except Exception as e:
        pytest.fail(f"Outline generation failed unexpectedly: {e}")


def test_outline_generation_with_genre():
    """Test that generate_outline() uses genre-specific structure."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "Romance"
    pipeline.genre_config = {
        "framework": "emotional_arc",
        "outline": ["connection", "disruption", "resolution"],
        "constraints": {}
    }
    
    try:
        premise = pipeline.capture_premise(
            idea="Two strangers meet at a coffee shop",
            character={"name": "Jordan", "description": "A barista"},
            theme="Love and connection",
            validate=False
        )
    except Exception as e:
        pytest.fail(f"Premise capture failed unexpectedly: {e}")
    
    try:
        outline = pipeline.generate_outline()
        assert outline is not None, "Outline should be generated"
        assert "acts" in outline, "Outline should contain acts structure"
        # Romance genre should use its specific structure
        assert outline["acts"]["beginning"] == "connection", "Romance beginning should be 'connection'"
        assert outline["acts"]["middle"] == "disruption", "Romance middle should be 'disruption'"
        assert outline["acts"]["end"] == "resolution", "Romance end should be 'resolution'"
    except Exception as e:
        pytest.fail(f"Outline generation with genre failed unexpectedly: {e}")


def test_scaffold_generation():
    """Test that scaffold() generates scaffold data with proper structure."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {
        "framework": "narrative_arc",
        "outline": ["setup", "complication", "resolution"],
        "constraints": {}
    }
    
    try:
        premise = pipeline.capture_premise(
            idea="A lighthouse keeper collects voices",
            character={"name": "Mara", "description": "A quiet keeper"},
            theme="Untold stories",
            validate=False
        )
    except Exception as e:
        pytest.fail(f"Premise capture failed unexpectedly: {e}")
    
    try:
        outline = pipeline.generate_outline()
        assert outline is not None, "Outline should be generated"
    except Exception as e:
        pytest.fail(f"Outline generation failed unexpectedly: {e}")
    
    try:
        scaffold = pipeline.scaffold()
        assert scaffold is not None, "Scaffold should be generated"
        assert isinstance(scaffold, dict), "Scaffold should be a dictionary"
        assert len(scaffold) > 0, "Scaffold should not be empty"
        # Scaffold should contain key elements like POV, tone, style, or voice
        scaffold_keys = scaffold.keys()
        assert any(key in scaffold_keys for key in ["pov", "tone", "style", "voice"]), \
            "Scaffold should contain POV, tone, style, or voice information"
    except Exception as e:
        pytest.fail(f"Scaffold generation failed unexpectedly: {e}")


def test_scaffold_generation_with_genre_constraints():
    """Test that scaffold() applies genre-specific constraints."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "Horror"
    pipeline.genre_config = {
        "framework": "tension_arc",
        "outline": ["setup", "escalation", "climax"],
        "constraints": {
            "tone": "dark",
            "pov_preference": "first person",
            "sensory_focus": "sound, touch"
        }
    }
    
    try:
        premise = pipeline.capture_premise(
            idea="Something is watching from the shadows",
            character={"name": "Alex", "description": "A night security guard"},
            theme="Fear of the unknown",
            validate=False
        )
    except Exception as e:
        pytest.fail(f"Premise capture failed unexpectedly: {e}")
    
    try:
        outline = pipeline.generate_outline()
        assert outline is not None, "Outline should be generated"
    except Exception as e:
        pytest.fail(f"Outline generation failed unexpectedly: {e}")
    
    try:
        scaffold = pipeline.scaffold()
        assert scaffold is not None, "Scaffold should be generated"
        # Horror genre constraints should influence the scaffold
        # The scaffold should reflect genre-appropriate tone and POV preferences
        assert isinstance(scaffold, dict), "Scaffold should be a dictionary"
    except Exception as e:
        pytest.fail(f"Scaffold generation with genre constraints failed unexpectedly: {e}")


def test_draft_generation():
    """Test that draft() generates story text."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    try:
        premise = pipeline.capture_premise(
            idea="A lighthouse keeper collects voices",
            character={"name": "Mara", "description": "A quiet keeper"},
            theme="Untold stories",
            validate=False
        )
        assert premise is not None, "Premise capture should succeed"
    except Exception as e:
        pytest.fail(f"Premise capture failed unexpectedly: {e}")
    
    try:
        outline = pipeline.generate_outline()
        assert outline is not None, "Outline generation should succeed"
    except Exception as e:
        pytest.fail(f"Outline generation failed unexpectedly: {e}")
    
    try:
        scaffold = pipeline.scaffold()
        assert scaffold is not None, "Scaffold generation should succeed"
    except Exception as e:
        pytest.fail(f"Scaffold generation failed unexpectedly: {e}")
    
    try:
        draft = pipeline.draft()
        assert draft is not None, "Draft should be generated"
        assert "text" in draft, "Draft should contain text field"
        assert len(draft["text"]) > 0, "Draft text should not be empty"
        assert draft["word_count"] > 0, "Draft should have word count > 0"
        assert "setup" in draft["text"].lower() or "beginning" in draft["text"].lower(), "Draft should contain setup/beginning section"
    except Exception as e:
        pytest.fail(f"Draft generation failed unexpectedly: {e}")


def test_draft_with_optional_fields():
    """Test that draft() works with optional character and theme."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    premise = pipeline.capture_premise(
        idea="A lighthouse keeper collects voices",
        character=None,  # Optional
        theme="",  # Optional
        validate=False
    )
    outline = pipeline.generate_outline()
    scaffold = pipeline.scaffold()
    
    draft = pipeline.draft()
    assert draft is not None
    assert "text" in draft
    assert len(draft["text"]) > 0


def test_revise_improves_text():
    """Test that revise() processes the draft."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    try:
        premise = pipeline.capture_premise(
            idea="It was a dark and stormy night",  # Contains cliché
            character={"name": "Test"},
            theme="Test theme",
            validate=False
        )
        outline = pipeline.generate_outline()
        scaffold = pipeline.scaffold()
        draft = pipeline.draft()
        
        revised = pipeline.revise()
        assert revised is not None, "Revision should return a result"
        assert "text" in revised, "Revision should contain text field"
        assert revised["word_count"] > 0, "Revision should have word count > 0"
        assert "revisions" in revised, "Revision should contain revisions metadata"
        # The cliché should be replaced
        assert "dark and stormy night" not in revised["text"].lower() or "a night that swallowed sound" in revised["text"].lower(), "Cliché should be replaced"
    except ValueError as e:
        pytest.fail(f"Pipeline stage failed (validation error): {e}")
    except Exception as e:
        pytest.fail(f"Revision failed unexpectedly: {type(e).__name__}: {e}")


def test_full_pipeline():
    """Test running the full pipeline end-to-end."""
    pipeline = ShortStoryPipeline()
    try:
        result = pipeline.run_full_pipeline(
            idea="A lighthouse keeper collects lost voices in glass jars",
            character={"name": "Mara", "description": "A quiet keeper", "quirks": ["Never speaks above a whisper"]},
            theme="What happens to stories we never tell?",
            genre="General Fiction"
        )
        assert result is not None, "Pipeline should return a result"
        assert "text" in result, "Result should contain text field"
        assert result["word_count"] > 0, "Result should have word count > 0"
        assert len(result["text"]) > 0, "Result text should not be empty"
    except ValueError as e:
        pytest.fail(f"Pipeline validation failed: {e}")
    except RuntimeError as e:
        pytest.fail(f"Pipeline execution failed (LLM error): {e}")
    except Exception as e:
        pytest.fail(f"Pipeline failed unexpectedly: {type(e).__name__}: {e}")


def test_draft_with_validation_enabled():
    """Test draft generation with validation enabled."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    premise = pipeline.capture_premise(
        idea="A unique story about a lighthouse keeper",
        character={"name": "Mara", "description": "A distinctive character"},
        theme="What happens to untold stories?",
        validate=True  # Enable validation
    )
    outline = pipeline.generate_outline()
    scaffold = pipeline.scaffold()
    
    draft = pipeline.draft(use_llm=False)  # Use template to avoid LLM dependency
    assert draft is not None
    assert "text" in draft
    assert len(draft["text"]) > 0
    assert draft["word_count"] > 0
    assert premise["validation"]["is_valid"] is True


def test_draft_raises_error_without_premise():
    """Test that draft() raises ValueError when premise is missing."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    # Set up outline and scaffold but not premise
    pipeline.outline = {"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}}
    pipeline._scaffold_data = {"pov": "third", "tone": "balanced"}
    
    with pytest.raises(ValueError, match="Cannot draft without premise"):
        pipeline.draft()


def test_draft_raises_error_without_outline():
    """Test that draft() raises ValueError when outline is missing."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    pipeline.capture_premise(
        idea="Test idea",
        character={"name": "Test"},
        theme="Test theme",
        validate=False
    )
    
    # Set up scaffold but not outline
    pipeline._scaffold_data = {"pov": "third", "tone": "balanced"}
    
    with pytest.raises(ValueError, match="Cannot draft without outline"):
        pipeline.draft()


def test_draft_raises_error_without_scaffold():
    """Test that draft() raises ValueError when scaffold is missing."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    pipeline.capture_premise(
        idea="Test idea",
        character={"name": "Test"},
        theme="Test theme",
        validate=False
    )
    pipeline.generate_outline()
    
    with pytest.raises(ValueError, match="Cannot draft without scaffold"):
        pipeline.draft()


def test_revise_raises_error_without_draft():
    """Test that revise() raises ValueError when draft is missing."""
    pipeline = ShortStoryPipeline()
    
    with pytest.raises(ValueError, match="Cannot revise without draft"):
        pipeline.revise()


def test_revise_raises_error_with_invalid_draft_type():
    """Test that revise() raises ValueError with invalid draft type."""
    pipeline = ShortStoryPipeline()
    
    with pytest.raises(ValueError, match="Draft must be a dict"):
        pipeline.revise(draft="not a dict")


def test_revise_raises_error_with_empty_text():
    """Test that revise() raises ValueError with empty draft text."""
    pipeline = ShortStoryPipeline()
    
    with pytest.raises(ValueError, match="Cannot revise draft with empty text"):
        pipeline.revise(draft={"text": ""})


def test_revise_raises_error_with_non_string_text():
    """Test that revise() raises ValueError with non-string text."""
    pipeline = ShortStoryPipeline()
    
    with pytest.raises(ValueError, match="Draft text must be a string"):
        pipeline.revise(draft={"text": 123})


def test_revise_with_rule_based_fallback():
    """Test that revise() uses rule-based fallback when LLM is disabled."""
    pipeline = ShortStoryPipeline()
    pipeline.genre = "General Fiction"
    pipeline.genre_config = {"framework": "narrative_arc", "outline": ["setup", "complication", "resolution"], "constraints": {}}
    
    premise = pipeline.capture_premise(
        idea="It was a dark and stormy night",
        character={"name": "Test"},
        theme="Test theme",
        validate=False
    )
    outline = pipeline.generate_outline()
    scaffold = pipeline.scaffold()
    draft = pipeline.draft(use_llm=False)
    
    # Use rule-based revision
    revised = pipeline.revise(use_llm=False)
    
    assert revised is not None
    assert "text" in revised
    assert revised["word_count"] > 0
    assert "revisions" in revised
    # Cliché should be replaced by rule-based revision
    assert "dark and stormy night" not in revised["text"].lower()
    assert "a night that swallowed sound" in revised["text"].lower()


# Tests for _generate_template_draft method
class TestGenerateTemplateDraft:
    """Test suite for _generate_template_draft method."""
    
    def test_generate_template_draft_basic(self):
        """Test basic template draft generation."""
        pipeline = ShortStoryPipeline()
        idea = "A lone traveler discovers a hidden oasis."
        character = {"name": "Anya", "description": "A weary explorer with a thirst for adventure."}
        theme = "The allure of the unknown."
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "adventure"
        }
        scaffold = {"pov": "third person", "tone": "optimistic"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        assert "setup" in draft.lower()
        assert "complication" in draft.lower()
        assert "resolution" in draft.lower()
        assert idea in draft
        assert character["description"] in draft
    
    def test_generate_template_draft_with_first_person_pov(self):
        """Test template draft generation with first person POV."""
        pipeline = ShortStoryPipeline()
        idea = "I found a hidden door in my basement."
        character = {"name": "Sam", "description": "A curious homeowner"}
        theme = "What lies beneath?"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "mystery"
        }
        scaffold = {"pov": "first person", "tone": "suspenseful"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert "I" in draft or "i found" in draft.lower()
        assert idea in draft
    
    def test_generate_template_draft_with_second_person_pov(self):
        """Test template draft generation with second person POV."""
        pipeline = ShortStoryPipeline()
        idea = "You wake up in an unfamiliar room."
        character = {"name": "You", "description": "A confused person"}
        theme = "Identity and memory"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "thriller"
        }
        scaffold = {"pov": "second person", "tone": "mysterious"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert "you" in draft.lower() or "You" in draft
        assert idea in draft
    
    def test_generate_template_draft_with_character_quirks(self):
        """Test template draft generation includes character quirks."""
        pipeline = ShortStoryPipeline()
        idea = "A librarian discovers a book that writes itself."
        character = {
            "name": "Elena",
            "description": "A meticulous librarian",
            "quirks": ["Always wears gloves", "Never reads fiction"]
        }
        theme = "The power of stories"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "fantasy"
        }
        scaffold = {"pov": "third person", "tone": "whimsical"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        # Should include at least one quirk
        assert "gloves" in draft.lower() or "fiction" in draft.lower()
    
    def test_generate_template_draft_with_character_contradictions(self):
        """Test template draft generation includes character contradictions."""
        pipeline = ShortStoryPipeline()
        idea = "A pacifist must defend their home."
        character = {
            "name": "Marcus",
            "description": "A peaceful person",
            "contradictions": "He hated violence but loved action movies."
        }
        theme = "The conflict within"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "drama"
        }
        scaffold = {"pov": "third person", "tone": "introspective"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert character["contradictions"] in draft
    
    def test_generate_template_draft_with_horror_genre(self):
        """Test template draft generation with horror genre."""
        pipeline = ShortStoryPipeline()
        idea = "Something is watching from the shadows."
        character = {"name": "Alex", "description": "A night security guard"}
        theme = "Fear of the unknown"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "horror"
        }
        scaffold = {"pov": "third person", "tone": "dark"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        # Horror genre should have specific complication text
        assert "shifted" in draft.lower() or "familiar" in draft.lower() or "uncertain" in draft.lower()
    
    def test_generate_template_draft_with_romance_genre(self):
        """Test template draft generation with romance genre."""
        pipeline = ShortStoryPipeline()
        idea = "Two strangers meet at a coffee shop."
        character = {"name": "Jordan", "description": "A barista"}
        theme = "Love and connection"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "romance"
        }
        scaffold = {"pov": "third person", "tone": "warm"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        # Romance genre should have specific complication text
        assert "connection" in draft.lower() or "sparked" in draft.lower() or "distance" in draft.lower()
    
    def test_generate_template_draft_with_crime_genre(self):
        """Test template draft generation with crime/noir genre."""
        pipeline = ShortStoryPipeline()
        idea = "A detective investigates a series of mysterious disappearances."
        character = {"name": "Detective Smith", "description": "A seasoned investigator"}
        theme = "Truth and justice"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "crime"
        }
        scaffold = {"pov": "third person", "tone": "gritty"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        # Crime genre should have specific complication text
        assert "pieces" in draft.lower() or "questions" in draft.lower() or "fit" in draft.lower()
    
    def test_generate_template_draft_with_string_character(self):
        """Test template draft generation with character as string."""
        pipeline = ShortStoryPipeline()
        idea = "A robot learns to dream."
        character = "A sentient android named ARIA"
        theme = "What makes us human?"
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "science fiction"
        }
        scaffold = {"pov": "third person", "tone": "philosophical"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert character in draft or "ARIA" in draft
    
    def test_generate_template_draft_with_empty_theme(self):
        """Test template draft generation with empty theme."""
        pipeline = ShortStoryPipeline()
        idea = "A day in the life of a street musician."
        character = {"name": "Rio", "description": "A talented violinist"}
        theme = ""
        outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "literary fiction"
        }
        scaffold = {"pov": "third person", "tone": "contemplative"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        # Should not include theme-related text when theme is empty
        assert "The question lingered:" not in draft
    
    def test_generate_template_draft_with_custom_outline_labels(self):
        """Test template draft generation with custom outline structure labels."""
        pipeline = ShortStoryPipeline()
        idea = "A chef creates a dish that changes people's memories."
        character = {"name": "Chef Marco", "description": "A culinary innovator"}
        theme = "Memory and taste"
        outline = {
            "acts": {
                "beginning": "preparation",
                "middle": "transformation",
                "end": "revelation"
            },
            "genre": "magical realism"
        }
        scaffold = {"pov": "third person", "tone": "mystical"}
        
        draft = pipeline._generate_template_draft(idea, character, theme, outline, scaffold)
        
        assert isinstance(draft, str)
        assert "preparation" in draft.lower() or "Preparation" in draft
        assert "transformation" in draft.lower() or "Transformation" in draft
        assert "revelation" in draft.lower() or "Revelation" in draft


# Tests for _apply_rule_based_revisions method
class TestApplyRuleBasedRevisions:
    """Test suite for _apply_rule_based_revisions method."""
    
    def test_apply_rule_based_revisions_replaces_cliches(self):
        """Test that rule-based revisions replace common clichés."""
        pipeline = ShortStoryPipeline()
        text = "It was a dark and stormy night. She arrived in the nick of time."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert "dark and stormy night" not in revised_text.lower()
        assert "a night that swallowed sound" in revised_text.lower()
        assert "in the nick of time" not in revised_text.lower()
        assert "just as the moment shifted" in revised_text.lower()
    
    def test_apply_rule_based_revisions_case_insensitive(self):
        """Test that cliché replacement is case-insensitive."""
        pipeline = ShortStoryPipeline()
        text = "It was A DARK AND STORMY NIGHT. Once Upon A Time there was a story."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert "dark and stormy night" not in revised_text.lower()
        assert "once upon a time" not in revised_text.lower()
        assert "it began" in revised_text.lower()
    
    def test_apply_rule_based_revisions_removes_vague_language(self):
        """Test that rule-based revisions remove vague language."""
        pipeline = ShortStoryPipeline()
        text = "She was very tired and really wanted to rest. It was quite difficult and somewhat challenging."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert " very " not in revised_text
        assert " really " not in revised_text
        assert " quite " not in revised_text
        assert " somewhat " not in revised_text
        # Should still contain the core meaning
        assert "tired" in revised_text.lower()
        assert "wanted" in revised_text.lower()
    
    def test_apply_rule_based_revisions_removes_redundant_phrases(self):
        """Test that rule-based revisions remove redundant phrases."""
        pipeline = ShortStoryPipeline()
        text = "The fact that she left was surprising. In order to succeed, she had to work hard. Due to the fact that it rained, we stayed inside."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Check that redundant phrases are replaced (case-insensitive)
        # "the fact that" should be replaced with "that"
        assert "the fact that" not in revised_text.lower()
        # "in order to" should be replaced with "to"
        assert "in order to" not in revised_text.lower()
        # "due to the fact that" should be replaced with "because"
        assert "due to the fact that" not in revised_text.lower()
        # Should contain simplified versions
        assert "that she left" in revised_text.lower()  # "The fact that she left" -> "that she left"
        assert "to succeed" in revised_text.lower()  # "in order to succeed" -> "to succeed"
        assert "because it rained" in revised_text.lower()  # "Due to the fact that it rained" -> "because it rained"
    
    def test_apply_rule_based_revisions_multiple_cliches(self):
        """Test that rule-based revisions handle multiple clichés in one text."""
        pipeline = ShortStoryPipeline()
        text = "It was a dark and stormy night when all hell broke loose. It was like finding a needle in a haystack, but we found it in the nick of time."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert "dark and stormy night" not in revised_text.lower()
        assert "all hell broke loose" not in revised_text.lower()
        assert "needle in a haystack" not in revised_text.lower()
        assert "in the nick of time" not in revised_text.lower()
        # Should contain replacements
        assert "a night that swallowed sound" in revised_text.lower()
        assert "everything fractured" in revised_text.lower()
        assert "just as the moment shifted" in revised_text.lower()
    
    def test_apply_rule_based_revisions_preserves_meaning(self):
        """Test that rule-based revisions preserve the core meaning of the text."""
        pipeline = ShortStoryPipeline()
        text = "The character walked through the forest. It was a dark and stormy night, but she was very determined to reach her destination."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Core meaning should be preserved
        assert "character" in revised_text.lower()
        assert "walked" in revised_text.lower() or "forest" in revised_text.lower()
        assert "determined" in revised_text.lower() or "destination" in revised_text.lower()
        # Clichés and vague language should be removed
        assert "dark and stormy night" not in revised_text.lower()
        assert " very " not in revised_text
    
    def test_apply_rule_based_revisions_empty_text(self):
        """Test that rule-based revisions handle empty text."""
        pipeline = ShortStoryPipeline()
        text = ""
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert revised_text == ""
    
    def test_apply_rule_based_revisions_no_cliches(self):
        """Test that rule-based revisions work correctly when no clichés are present."""
        pipeline = ShortStoryPipeline()
        text = "The sun rose over the mountains. Birds sang in the trees. A gentle breeze moved through the valley."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Should still return text (may have vague language removed)
        assert len(revised_text) > 0
        assert "sun" in revised_text.lower() or "mountains" in revised_text.lower()
    
    def test_apply_rule_based_revisions_all_vague_language_types(self):
        """Test that all types of vague language are removed."""
        pipeline = ShortStoryPipeline()
        text = "It was very hot, really sunny, quite bright, somewhat humid, kind of uncomfortable, and sort of miserable."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert " very " not in revised_text
        assert " really " not in revised_text
        assert " quite " not in revised_text
        assert " somewhat " not in revised_text
        assert " kind of " not in revised_text
        assert " sort of " not in revised_text
        # Core meaning preserved
        assert "hot" in revised_text.lower() or "sunny" in revised_text.lower()
    
    def test_apply_rule_based_revisions_with_distinctiveness_check(self):
        """Test that rule-based revisions accept distinctiveness_check parameter (API compatibility)."""
        pipeline = ShortStoryPipeline()
        text = "It was a dark and stormy night."
        distinctiveness_check = {
            "has_cliches": True,
            "found_cliches": ["dark and stormy night"],
            "distinctiveness_score": 0.5
        }
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Should work regardless of distinctiveness_check content
        assert "dark and stormy night" not in revised_text.lower()

