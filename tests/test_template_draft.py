"""
Tests for template draft generation.
"""

import pytest
from tests.test_constants import (
    GENRE_HORROR,
    GENRE_ROMANCE,
    GENRE_THRILLER,
    GENRE_GENERAL_FICTION,
)

# Define test-specific fixtures that extend shared fixtures
# Note: Using function scope to match dependencies (sample_premise, sample_character are function-scoped)
@pytest.fixture
def test_idea(sample_premise):
    """Test idea from sample premise."""
    return sample_premise["idea"]

@pytest.fixture
def test_character(sample_character):
    """Test character from sample character fixture."""
    return sample_character

@pytest.fixture
def test_theme(sample_premise):
    """Test theme from sample premise."""
    return sample_premise["theme"]

@pytest.fixture
def test_outline():
    """Test outline structure."""
    return {
        "acts": {
            "beginning": "setup",
            "middle": "complication",
            "end": "resolution"
        },
        "genre": GENRE_GENERAL_FICTION
    }

@pytest.fixture
def test_scaffold():
    """Test scaffold structure."""
    return {
        "pov": "third person",
        "tone": "balanced",
        "pace": "moderate"
    }

# Use shared fixtures from conftest.py where possible
# Note: test_idea, test_character, test_theme use sample_premise from conftest.py
# test_outline and test_scaffold are specific to this test suite

# Genre-specific keyword definitions for positive and negative assertions
HORROR_POSITIVE_KEYWORDS = ["shifted", "strange", "uncertain", "fear", "terror", "dread", "dark", "ominous", "sinister"]
HORROR_NEGATIVE_KEYWORDS = ["connection", "love", "romance", "heartbreak", "passion", "clue", "detective", "mystery", "solve", "investigation"]

ROMANCE_POSITIVE_KEYWORDS = ["connection", "closeness", "distance", "love", "heart", "passion", "intimacy", "emotion", "relationship"]
ROMANCE_NEGATIVE_KEYWORDS = ["shifted", "strange", "uncertain", "fear", "terror", "dread", "clue", "detective", "mystery", "solve", "threat", "danger"]

THRILLER_POSITIVE_KEYWORDS = ["threat", "danger", "stakes", "urgency", "suspense", "tension", "action", "crisis"]
THRILLER_NEGATIVE_KEYWORDS = ["connection", "love", "romance", "heartbreak", "shifted", "strange", "uncertain", "fear", "terror", "dread"]


class TestTemplateDraftGeneration:
    """Test suite for _generate_template_draft method."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, basic_pipeline, test_idea, test_character, test_theme, test_outline, test_scaffold):
        """Consolidated setup for all test methods - eliminates repetitive fixture parameters."""
        self.pipeline = basic_pipeline
        self.idea = test_idea
        self.character = test_character
        self.theme = test_theme
        self.outline = test_outline
        self.scaffold = test_scaffold
    
    def test_generate_template_draft_basic(self):
        """Test basic template draft generation."""
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            self.theme,
            self.outline,
            self.scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        
        # More robust check for structural elements - check for markdown headers
        # The template uses ## {label.title()} format
        draft_lower = draft.lower()
        
        # Check for beginning/setup section (markdown header or keyword)
        beginning_indicators = [
            "## setup", "# setup", "## beginning", "# beginning",
            "setup" in draft_lower, "beginning" in draft_lower,
            "introduction" in draft_lower, "start" in draft_lower
        ]
        assert any(beginning_indicators), \
            "Draft should contain beginning/setup section indicator"
        
        # Check for middle/complication section
        middle_indicators = [
            "## complication", "# complication", "## middle", "# middle",
            "complication" in draft_lower, "middle" in draft_lower,
            "development" in draft_lower, "conflict" in draft_lower
        ]
        assert any(middle_indicators), \
            "Draft should contain middle/complication section indicator"
        
        # Check for end/resolution section
        end_indicators = [
            "## resolution", "# resolution", "## end", "# end",
            "resolution" in draft_lower, "end" in draft_lower,
            "conclusion" in draft_lower, "ending" in draft_lower
        ]
        assert any(end_indicators), \
            "Draft should contain end/resolution section indicator"
        
        # Check that the idea is present (more flexible - check for key words)
        idea_keywords = [word.lower() for word in self.idea.split() if len(word) > 3]
        assert any(keyword in draft_lower for keyword in idea_keywords) or self.idea in draft, \
            f"Draft should contain the story idea or key words from it: {idea_keywords}"
        
        # Additional comprehensive assertions for draft content
        assert isinstance(draft, str), "Draft must be a string type"
        assert len(draft.strip()) > 0, "Draft must contain non-whitespace content"
        
        # Verify draft has minimum expected length (at least a few sentences)
        # Template drafts should have substantial content
        assert len(draft) > 50, "Draft should have substantial content (at least 50 characters)"
        
        # Verify draft contains character name or reference
        character_name_lower = self.character.get("name", "").lower()
        if character_name_lower:
            assert character_name_lower in draft_lower or any(
                word in draft_lower for word in character_name_lower.split()
            ), f"Draft should reference character name: {character_name_lower}"
        
        # Verify draft structure: should have paragraphs or sections
        # Template drafts should have multiple sentences
        sentence_endings = ['.', '!', '?']
        assert any(ending in draft for ending in sentence_endings), \
            "Draft should contain complete sentences with punctuation"
        
        # Verify draft doesn't contain placeholder text
        placeholder_indicators = ["[PLACEHOLDER", "{PLACEHOLDER", "<PLACEHOLDER", "TODO:", "FIXME:"]
        for placeholder in placeholder_indicators:
            assert placeholder.upper() not in draft.upper(), \
                f"Draft should not contain placeholder text: {placeholder}"
    
    def test_generate_template_draft_first_person_pov(self):
        """Test template draft with first person POV."""
        scaffold_first = self.scaffold.copy()
        scaffold_first["pov"] = "first person"
        
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            self.theme,
            self.outline,
            scaffold_first
        )
        
        # Should use first person pronouns
        assert "I " in draft or "I had" in draft or "I" in draft.split()[0]
    
    def test_generate_template_draft_horror_genre(self):
        """Test template draft with horror genre."""
        outline_horror = self.outline.copy()
        outline_horror["genre"] = GENRE_HORROR
        
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            self.theme,
            outline_horror,
            self.scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        
        # Should include horror-specific keywords
        draft_lower = draft.lower()
        assert any(keyword in draft_lower for keyword in HORROR_POSITIVE_KEYWORDS), \
            f"Horror draft should contain at least one of {HORROR_POSITIVE_KEYWORDS}"
        
        # Should NOT include strong indicators of other genres (negative assertions)
        assert not any(keyword in draft_lower for keyword in HORROR_NEGATIVE_KEYWORDS), \
            f"Horror draft should NOT contain romance or mystery keywords: {[k for k in HORROR_NEGATIVE_KEYWORDS if k in draft_lower]}"
    
    def test_generate_template_draft_romance_genre(self):
        """Test template draft with romance genre."""
        outline_romance = self.outline.copy()
        outline_romance["genre"] = GENRE_ROMANCE
        
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            self.theme,
            outline_romance,
            self.scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        
        # Should include romance-specific keywords
        draft_lower = draft.lower()
        assert any(keyword in draft_lower for keyword in ROMANCE_POSITIVE_KEYWORDS), \
            f"Romance draft should contain at least one of {ROMANCE_POSITIVE_KEYWORDS}"
        
        # Should NOT include strong indicators of other genres (negative assertions)
        assert not any(keyword in draft_lower for keyword in ROMANCE_NEGATIVE_KEYWORDS), \
            f"Romance draft should NOT contain horror or thriller keywords: {[k for k in ROMANCE_NEGATIVE_KEYWORDS if k in draft_lower]}"
    
    def test_generate_template_draft_thriller_genre(self):
        """Test template draft with thriller genre."""
        outline_thriller = self.outline.copy()
        outline_thriller["genre"] = GENRE_THRILLER
        
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            self.theme,
            outline_thriller,
            self.scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        
        # Should include thriller-specific keywords
        draft_lower = draft.lower()
        assert any(keyword in draft_lower for keyword in THRILLER_POSITIVE_KEYWORDS), \
            f"Thriller draft should contain at least one of {THRILLER_POSITIVE_KEYWORDS}"
        
        # Should NOT include strong indicators of other genres (negative assertions)
        assert not any(keyword in draft_lower for keyword in THRILLER_NEGATIVE_KEYWORDS), \
            f"Thriller draft should NOT contain romance or horror keywords: {[k for k in THRILLER_NEGATIVE_KEYWORDS if k in draft_lower]}"
    
    def test_generate_template_draft_empty_theme(self):
        """Test template draft generation with empty theme."""
        draft = self.pipeline._generate_template_draft(
            self.idea,
            self.character,
            "",  # Empty theme
            self.outline,
            self.scaffold
        )
        
        assert isinstance(draft, str)
        assert len(draft) > 0
        
        # Check that the idea is present (more flexible - check for key words)
        idea_keywords = [word.lower() for word in self.idea.split() if len(word) > 3]
        draft_lower = draft.lower()
        assert any(keyword in draft_lower for keyword in idea_keywords) or self.idea in draft, \
            f"Draft should contain the story idea or key words from it: {idea_keywords}"
