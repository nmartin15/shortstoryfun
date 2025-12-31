"""
Unit tests for template draft generation and rule-based revisions.
"""

import pytest
from src.shortstory.pipeline import ShortStoryPipeline


class TestTemplateDraftGeneration:
    """Test suite for _generate_template_draft method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = ShortStoryPipeline()
        self.test_idea = "A lighthouse keeper collects lost voices in glass jars"
        self.test_character = {
            "name": "Mara",
            "description": "A quiet keeper who never speaks above a whisper",
            "quirks": ["Counts everything in threes", "Never looks directly at mirrors"],
            "contradictions": "Fiercely protective but terrified of connection"
        }
        self.test_theme = "What happens to stories we never tell?"
        self.test_outline = {
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            },
            "genre": "General Fiction"
        }
        self.test_scaffold = {
            "pov": "third person",
            "tone": "balanced",
            "pace": "moderate"
        }
    
    def test_generate_template_draft_basic(self):
        """Test basic template draft generation."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        assert "setup" in draft.lower() or "beginning" in draft.lower()
        assert "complication" in draft.lower() or "middle" in draft.lower()
        assert "resolution" in draft.lower() or "end" in draft.lower()
        assert self.test_idea in draft
    
    def test_generate_template_draft_with_character_name(self):
        """Test template draft includes character name."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        assert "Mara" in draft or "mara" in draft.lower()
    
    def test_generate_template_draft_with_character_quirks(self):
        """Test template draft includes character quirks."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        # Should include at least one quirk
        quirks_present = any(
            quirk.lower() in draft.lower() 
            for quirk in self.test_character["quirks"]
        )
        assert quirks_present
    
    def test_generate_template_draft_with_theme(self):
        """Test template draft includes theme."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        assert self.test_theme in draft or "question" in draft.lower()
    
    def test_generate_template_draft_with_contradictions(self):
        """Test template draft includes character contradictions."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        # Should include contradictions in middle section
        assert "contradiction" in draft.lower() or "protective" in draft.lower() or "terrified" in draft.lower()
    
    def test_generate_template_draft_first_person_pov(self):
        """Test template draft with first person POV."""
        scaffold_first = self.test_scaffold.copy()
        scaffold_first["pov"] = "first person"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            scaffold_first
        )
        
        # Should use first person pronouns
        assert "I " in draft or "I had" in draft or "I" in draft.split()[0]
    
    def test_generate_template_draft_second_person_pov(self):
        """Test template draft with second person POV."""
        scaffold_second = self.test_scaffold.copy()
        scaffold_second["pov"] = "second person"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            scaffold_second
        )
        
        # Should use second person pronouns
        assert "you" in draft.lower() or "your" in draft.lower()
    
    def test_generate_template_draft_third_person_pov(self):
        """Test template draft with third person POV."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        # Should use character name or third person pronouns
        assert "Mara" in draft or "they" in draft.lower() or "their" in draft.lower()
    
    def test_generate_template_draft_horror_genre(self):
        """Test template draft with horror genre."""
        outline_horror = self.test_outline.copy()
        outline_horror["genre"] = "Horror"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            outline_horror,
            self.test_scaffold
        )
        
        # Should include horror-specific complication
        assert "shifted" in draft.lower() or "strange" in draft.lower() or "uncertain" in draft.lower()
    
    def test_generate_template_draft_romance_genre(self):
        """Test template draft with romance genre."""
        outline_romance = self.test_outline.copy()
        outline_romance["genre"] = "Romance"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            outline_romance,
            self.test_scaffold
        )
        
        # Should include romance-specific complication
        assert "connection" in draft.lower() or "closeness" in draft.lower() or "distance" in draft.lower()
    
    def test_generate_template_draft_crime_genre(self):
        """Test template draft with crime/noir genre."""
        outline_crime = self.test_outline.copy()
        outline_crime["genre"] = "Crime"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            outline_crime,
            self.test_scaffold
        )
        
        # Should include crime-specific complication
        assert "pieces" in draft.lower() or "questions" in draft.lower() or "fit" in draft.lower()
    
    def test_generate_template_draft_character_as_string(self):
        """Test template draft with character as string instead of dict."""
        character_str = "A mysterious lighthouse keeper"
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            character_str,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        assert character_str in draft or "character" in draft.lower()
    
    def test_generate_template_draft_character_as_none(self):
        """Test template draft with character as None."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            None,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        assert self.test_idea in draft
    
    def test_generate_template_draft_empty_theme(self):
        """Test template draft with empty theme."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            "",
            self.test_outline,
            self.test_scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        # Should not include theme-specific text
        assert "question" not in draft.lower() or "theme" not in draft.lower()
    
    def test_generate_template_draft_custom_outline_labels(self):
        """Test template draft with custom outline act labels."""
        custom_outline = {
            "acts": {
                "beginning": "introduction",
                "middle": "conflict",
                "end": "conclusion"
            },
            "genre": "General Fiction"
        }
        
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            custom_outline,
            self.test_scaffold
        )
        
        # Should use custom labels
        assert "introduction" in draft.lower() or "Introduction" in draft
        assert "conflict" in draft.lower() or "Conflict" in draft
        assert "conclusion" in draft.lower() or "Conclusion" in draft
    
    def test_generate_template_draft_structure(self):
        """Test that template draft has proper structure with sections."""
        draft = self.pipeline._generate_template_draft(
            self.test_idea,
            self.test_character,
            self.test_theme,
            self.test_outline,
            self.test_scaffold
        )
        
        # Should have markdown headers for sections
        assert "##" in draft or "#" in draft
        # Should have multiple sections
        lines = draft.split('\n')
        header_count = sum(1 for line in lines if line.strip().startswith('#'))
        assert header_count >= 2  # At least beginning and middle sections


class TestRuleBasedRevisions:
    """Test suite for _apply_rule_based_revisions method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = ShortStoryPipeline()
        self.distinctiveness_check = {}
    
    def test_apply_rule_based_revisions_basic(self):
        """Test basic rule-based revision."""
        text = "It was a dark and stormy night. She was very tired."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        assert isinstance(revised, str)
        assert len(revised) > 0
        # Cliché should be replaced
        assert "dark and stormy night" not in revised.lower()
        assert "a night that swallowed sound" in revised.lower()
        # Vague language should be removed
        assert " very " not in revised or " very tired" not in revised
    
    def test_apply_rule_based_revisions_cliche_replacement(self):
        """Test that clichés are replaced."""
        cliche_tests = [
            ("It was a dark and stormy night", "a night that swallowed sound"),
            ("Once upon a time", "it began"),
            ("In the nick of time", "just as the moment shifted"),
            ("All hell broke loose", "everything fractured"),
            ("Calm before the storm", "the pause before change"),
            ("Needle in a haystack", "something nearly impossible to find"),
            ("Tip of the iceberg", "only the surface"),
            ("Dead as a doornail", "completely still"),
            ("Raining cats and dogs", "rain that pounded"),
            ("Piece of cake", "effortless"),
        ]
        
        for original, replacement in cliche_tests:
            revised = self.pipeline._apply_rule_based_revisions(
                f"The story began: {original}.", 
                self.distinctiveness_check
            )
            assert original.lower() not in revised.lower()
            assert replacement.lower() in revised.lower()
    
    def test_apply_rule_based_revisions_case_insensitive(self):
        """Test that cliché replacement is case-insensitive."""
        text = "IT WAS A DARK AND STORMY NIGHT when everything changed."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        assert "DARK AND STORMY NIGHT" not in revised
        assert "dark and stormy night" not in revised.lower()
        assert "a night that swallowed sound" in revised.lower()
    
    def test_apply_rule_based_revisions_vague_language(self):
        """Test that vague language is removed."""
        vague_tests = [
            ("very", " "),
            ("really", " "),
            ("quite", " "),
            ("somewhat", " "),
            ("kind of", " "),
            ("sort of", " "),
        ]
        
        for vague_word, replacement in vague_tests:
            text = f"She was {vague_word} tired and {vague_word} sad."
            revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
            # Should remove the vague word (with spaces around it)
            assert f" {vague_word} " not in revised.lower()
    
    def test_apply_rule_based_revisions_redundant_phrases(self):
        """Test that redundant phrases are removed."""
        redundant_tests = [
            ("the fact that", "that"),
            ("in order to", "to"),
            ("due to the fact that", "because"),
        ]
        
        for phrase, replacement in redundant_tests:
            text = f"I know {phrase} you are right. We need {phrase} succeed."
            revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
            assert phrase not in revised.lower()
            # Should have replacement or just removed
            assert replacement in revised.lower() or phrase.replace(phrase, "") in revised
    
    def test_apply_rule_based_revisions_multiple_cliches(self):
        """Test revision with multiple clichés."""
        text = "It was a dark and stormy night. In the nick of time, she arrived. It was a piece of cake."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        assert "dark and stormy night" not in revised.lower()
        assert "in the nick of time" not in revised.lower()
        assert "piece of cake" not in revised.lower()
        assert "a night that swallowed sound" in revised.lower()
        assert "just as the moment shifted" in revised.lower()
        assert "effortless" in revised.lower()
    
    def test_apply_rule_based_revisions_preserves_meaning(self):
        """Test that revision preserves overall meaning."""
        text = "The hero arrived in the nick of time to save the day."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        # Should still contain key concepts
        assert "hero" in revised.lower() or "arrived" in revised.lower()
        assert "save" in revised.lower() or "day" in revised.lower()
    
    def test_apply_rule_based_revisions_empty_text(self):
        """Test revision with empty text."""
        revised = self.pipeline._apply_rule_based_revisions("", self.distinctiveness_check)
        assert revised == ""
    
    def test_apply_rule_based_revisions_no_cliches(self):
        """Test revision with text containing no clichés."""
        text = "A unique story about a lighthouse keeper who collects voices."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        # Should return similar text (may have vague language removed)
        assert "lighthouse" in revised.lower()
        assert "keeper" in revised.lower()
    
    def test_apply_rule_based_revisions_word_boundaries(self):
        """Test that replacements respect word boundaries."""
        # "darkness" should not match "dark and stormy night"
        text = "The darkness was overwhelming, but it wasn't a dark and stormy night."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        # "darkness" should remain
        assert "darkness" in revised.lower()
        # But "dark and stormy night" should be replaced
        assert "dark and stormy night" not in revised.lower()
    
    def test_apply_rule_based_revisions_long_text(self):
        """Test revision with longer text."""
        text = " ".join([
            "It was a dark and stormy night.",
            "She was very tired and really sad.",
            "In the nick of time, help arrived.",
            "The fact that she survived was amazing.",
            "It was a piece of cake to fix."
        ] * 10)  # Repeat to make it longer
        
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        # All clichés should be replaced
        assert "dark and stormy night" not in revised.lower()
        assert "in the nick of time" not in revised.lower()
        assert "piece of cake" not in revised.lower()
        # Vague language should be removed
        assert " very " not in revised or revised.count(" very ") < text.count(" very ")
    
    def test_apply_rule_based_revisions_preserves_structure(self):
        """Test that revision preserves text structure (paragraphs, etc.)."""
        text = "First paragraph.\n\nSecond paragraph with a dark and stormy night.\n\nThird paragraph."
        revised = self.pipeline._apply_rule_based_revisions(text, self.distinctiveness_check)
        
        # Should preserve paragraph breaks
        assert "\n\n" in revised
        # Should have similar structure
        paragraphs = revised.split("\n\n")
        assert len(paragraphs) >= 2

