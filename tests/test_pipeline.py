"""
Tests for pipeline functionality.
"""

import pytest


class TestRuleBasedRevisions:
    """Test suite for _apply_rule_based_revisions method."""
    
    def test_apply_rule_based_revisions_overlapping_phrases(self, basic_pipeline):
        """Test that rule-based revisions handle overlapping or nested phrases correctly."""
        pipeline = basic_pipeline
        # Test overlapping phrases: "due to the fact that" contains "the fact that"
        # The longer phrase should be matched first
        text = "It was due to the fact that she succeeded. In order to achieve the fact that she won."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # "due to the fact that" should be replaced with "because" (longer match first)
        assert "due to the fact that" not in revised_text.lower()
        assert "because" in revised_text.lower()
        # "the fact that" should also be replaced with "that" where it appears alone
        assert "the fact that" not in revised_text.lower()
        # "in order to" should be replaced with "to"
        assert "in order to" not in revised_text.lower()
        assert "to achieve that she won" in revised_text.lower() or "to achieve that" in revised_text.lower()
    
    def test_apply_rule_based_revisions_idempotence(self, basic_pipeline):
        """Test applying revisions multiple times yields the same result (idempotence)."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night. She was very tired."
        distinctiveness_check = {}
        
        first_pass = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        second_pass = pipeline._apply_rule_based_revisions(first_pass, distinctiveness_check)
        
        assert first_pass == second_pass, \
            "Applying revisions twice should yield the same result (idempotence). " \
            f"First pass: '{first_pass}', Second pass: '{second_pass}'"
    
    def test_apply_rule_based_revisions_empty_string(self, basic_pipeline):
        """Test that rule-based revisions handle empty strings correctly."""
        pipeline = basic_pipeline
        text = ""
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert revised_text == ""
    
    def test_apply_rule_based_revisions_no_cliches(self, basic_pipeline):
        """Test that rule-based revisions handle text with no clichés correctly."""
        pipeline = basic_pipeline
        text = "The lighthouse keeper collected voices in glass jars. Each voice told a unique story."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert len(revised_text) > 0
        # Text should remain unchanged if no clichés or vague language
        assert "lighthouse keeper" in revised_text
        assert "collected voices" in revised_text
    
    def test_apply_rule_based_revisions_multiple_cliches(self, basic_pipeline):
        """Test that rule-based revisions handle multiple clichés in one text."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night. Once upon a time, she found a needle in a haystack."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # All clichés should be replaced
        assert "dark and stormy night" not in revised_text.lower()
        assert "once upon a time" not in revised_text.lower()
        assert "needle in a haystack" not in revised_text.lower()
        # Check for replacements
        assert "a night that swallowed sound" in revised_text.lower() or "night" in revised_text.lower()
        assert "it began" in revised_text.lower() or "began" in revised_text.lower()
    
    def test_apply_rule_based_revisions_vague_language(self, basic_pipeline):
        """Test that rule-based revisions remove vague language."""
        pipeline = basic_pipeline
        text = "She was very tired and really wanted to rest. It was quite difficult and somewhat challenging."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Vague intensifiers should be removed
        assert " very " not in revised_text
        assert " really " not in revised_text
        assert " quite " not in revised_text
        assert " somewhat " not in revised_text
        # But the rest of the text should remain
        assert "tired" in revised_text.lower()
        assert "wanted" in revised_text.lower()
    
    def test_apply_rule_based_revisions_case_insensitive(self, basic_pipeline):
        """Test that rule-based revisions are case-insensitive."""
        pipeline = basic_pipeline
        text = "It was a DARK AND STORMY NIGHT. She was VERY tired."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Should handle uppercase clichés and vague language
        assert "DARK AND STORMY NIGHT" not in revised_text
        assert "dark and stormy night" not in revised_text.lower()
        assert " VERY " not in revised_text
        assert " very " not in revised_text
    
    def test_apply_rule_based_revisions_distinctiveness_check_unchanged(self, basic_pipeline):
        """Test that distinctiveness_check parameter is not modified (currently unused)."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night."
        distinctiveness_check = {"initial_score": 0.8, "cliches_found": []}
        original_check = distinctiveness_check.copy()
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # distinctiveness_check should remain unchanged (currently not modified by the method)
        assert distinctiveness_check == original_check, \
            "distinctiveness_check should not be modified by _apply_rule_based_revisions"
    
    def test_apply_rule_based_revisions_long_text(self, basic_pipeline):
        """Test that rule-based revisions handle long texts efficiently."""
        pipeline = basic_pipeline
        # Create a long text with multiple clichés
        base_text = "It was a dark and stormy night. She was very tired. "
        text = base_text * 100  # ~5000 characters
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert len(revised_text) > 0
        # All instances should be replaced
        assert "dark and stormy night" not in revised_text.lower(), \
            "All instances of 'dark and stormy night' should be replaced"
        assert " very " not in revised_text, \
            "All instances of ' very ' should be removed"
        # Should have been processed (text should be different)
        assert revised_text != text, \
            "Revised text should be different from original text"
    
    def test_apply_rule_based_revisions_replacement_order(self, basic_pipeline):
        """Test that replacement order doesn't create or undo other patterns."""
        pipeline = basic_pipeline
        # Test that one replacement doesn't create another cliché
        text = "It was due to the fact that she was very tired."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # "due to the fact that" should be replaced with "because"
        assert "due to the fact that" not in revised_text.lower()
        assert "because" in revised_text.lower()
        # "very" should be removed
        assert " very " not in revised_text
        # Replacement shouldn't create new clichés
        assert "because she was tired" in revised_text.lower() or "because she tired" in revised_text.lower()
    
    def test_apply_rule_based_revisions_preserves_punctuation(self, basic_pipeline):
        """Test that rule-based revisions preserve punctuation correctly."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night! She was very tired. Really?"
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Punctuation should be preserved
        assert "!" in revised_text or "?" in revised_text or "." in revised_text
        # Clichés should still be replaced
        assert "dark and stormy night" not in revised_text.lower()
        assert " very " not in revised_text
        assert " really " not in revised_text
    
    def test_apply_rule_based_revisions_handles_unicode(self, basic_pipeline):
        """Test that rule-based revisions handle Unicode characters correctly."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night. She was très tired."
        distinctiveness_check = {}
        
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        # Unicode characters should be preserved
        assert "très" in revised_text or "tres" in revised_text.lower()
        # Clichés should still be replaced
        assert "dark and stormy night" not in revised_text.lower()
    
    def test_apply_rule_based_revisions_handles_none_distinctiveness_check(self, basic_pipeline):
        """Test that rule-based revisions handle None distinctiveness_check."""
        pipeline = basic_pipeline
        text = "It was a dark and stormy night."
        distinctiveness_check = None
        
        # Should handle None gracefully
        revised_text = pipeline._apply_rule_based_revisions(text, distinctiveness_check)
        
        assert isinstance(revised_text, str)
        assert "dark and stormy night" not in revised_text.lower()


class TestPrivateHelperFunctions:
    """Test private helper functions in ShortStoryPipeline."""
    
    def test_get_genre_config_with_valid_genre(self, basic_pipeline):
        """Test _get_genre_config with valid genre."""
        pipeline = basic_pipeline
        config = pipeline._get_genre_config("Horror")
        
        assert isinstance(config, dict)
        assert "framework" in config
        assert "outline" in config
        assert "constraints" in config
    
    def test_get_genre_config_with_none(self, basic_pipeline):
        """Test _get_genre_config with None genre."""
        pipeline = basic_pipeline
        config = pipeline._get_genre_config(None)
        
        # Should return empty dict when genre is None
        assert isinstance(config, dict)
        assert config == {}
    
    def test_get_genre_config_with_empty_string(self, basic_pipeline):
        """Test _get_genre_config with empty string."""
        pipeline = basic_pipeline
        config = pipeline._get_genre_config("")
        
        # Should return empty dict when genre is empty
        assert isinstance(config, dict)
        assert config == {}
    
    def test_get_genre_config_with_invalid_genre(self, basic_pipeline):
        """Test _get_genre_config with invalid genre."""
        pipeline = basic_pipeline
        # get_genre_config returns default for invalid, but _get_genre_config may return empty dict
        config = pipeline._get_genre_config("Invalid Genre 12345")
        
        # Should return empty dict if get_genre_config returns None, or the default config
        assert isinstance(config, dict)
        # Either empty dict or default config (both are valid)
        if config:
            assert "framework" in config
    
    def test_get_genre_config_returns_never_none(self, basic_pipeline):
        """Test that _get_genre_config never returns None."""
        pipeline = basic_pipeline
        test_cases = ["Horror", "Romance", None, "", "Invalid Genre", "  "]
        
        for genre in test_cases:
            config = pipeline._get_genre_config(genre)
            assert config is not None, f"_get_genre_config should never return None for genre: {genre}"
            assert isinstance(config, dict), f"_get_genre_config should return dict for genre: {genre}"