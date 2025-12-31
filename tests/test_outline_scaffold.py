"""
Unit tests for outline generation and scaffolding.
"""

import pytest
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.genres import get_genre_config


class TestOutlineGeneration:
    """Test suite for generate_outline method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = ShortStoryPipeline()
        self.test_premise = {
            "idea": "A lighthouse keeper collects lost voices",
            "character": {"name": "Mara", "description": "A quiet keeper"},
            "theme": "Untold stories"
        }
    
    def test_generate_outline_basic(self):
        """Test basic outline generation."""
        self.pipeline.premise = self.test_premise
        outline = self.pipeline.generate_outline()
        
        assert outline is not None
        assert "premise" in outline
        assert "framework" in outline
        assert "structure" in outline
        assert "acts" in outline
        assert outline["premise"] == self.test_premise
    
    def test_generate_outline_default_structure(self):
        """Test outline with default structure when no genre specified."""
        self.pipeline.premise = self.test_premise
        self.pipeline.genre = None
        outline = self.pipeline.generate_outline()
        
        assert outline["framework"] == "narrative_arc"
        assert "setup" in outline["structure"]
        assert "complication" in outline["structure"]
        assert "resolution" in outline["structure"]
    
    def test_generate_outline_acts_structure(self):
        """Test that outline has proper acts structure."""
        self.pipeline.premise = self.test_premise
        outline = self.pipeline.generate_outline()
        
        acts = outline["acts"]
        assert "beginning" in acts
        assert "middle" in acts
        assert "end" in acts
        assert acts["beginning"] in outline["structure"]
        assert acts["middle"] in outline["structure"]
        assert acts["end"] in outline["structure"]
    
    def test_generate_outline_with_genre(self):
        """Test outline generation with genre specified."""
        self.pipeline.premise = self.test_premise
        self.pipeline.genre = "Horror"
        outline = self.pipeline.generate_outline(genre="Horror")
        
        genre_config = get_genre_config("Horror")
        expected_structure = genre_config.get("outline", [])
        expected_framework = genre_config.get("framework", "narrative_arc")
        
        assert outline["framework"] == expected_framework
        assert outline["structure"] == expected_structure
        assert outline["genre"] == "Horror"
    
    def test_generate_outline_with_different_genres(self):
        """Test outline generation with different genres."""
        genres_to_test = ["Horror", "Romance", "Literary", "General Fiction"]
        
        for genre in genres_to_test:
            self.pipeline.premise = self.test_premise
            self.pipeline.genre = genre
            outline = self.pipeline.generate_outline(genre=genre)
            
            genre_config = get_genre_config(genre)
            expected_framework = genre_config.get("framework", "narrative_arc")
            
            assert outline["framework"] == expected_framework
            assert outline["genre"] == genre
            assert len(outline["structure"]) > 0
    
    def test_generate_outline_uses_premise_parameter(self):
        """Test that outline can use premise parameter instead of self.premise."""
        custom_premise = {
            "idea": "A different story idea",
            "character": {"name": "Test"},
            "theme": "Test theme"
        }
        
        outline = self.pipeline.generate_outline(premise=custom_premise)
        
        assert outline["premise"] == custom_premise
    
    def test_generate_outline_uses_genre_parameter(self):
        """Test that outline can use genre parameter instead of self.genre."""
        self.pipeline.premise = self.test_premise
        self.pipeline.genre = None
        
        outline = self.pipeline.generate_outline(genre="Romance")
        
        genre_config = get_genre_config("Romance")
        expected_framework = genre_config.get("framework", "narrative_arc")
        
        assert outline["framework"] == expected_framework
        assert outline["genre"] == "Romance"
    
    def test_generate_outline_handles_missing_genre_config(self):
        """Test outline generation handles missing genre gracefully."""
        self.pipeline.premise = self.test_premise
        # Use a non-existent genre
        outline = self.pipeline.generate_outline(genre="NonExistentGenre")
        
        # Should fall back to default structure
        assert outline is not None
        assert "framework" in outline
        assert "structure" in outline
        assert len(outline["structure"]) > 0
    
    def test_generate_outline_structure_consistency(self):
        """Test that outline structure is consistent across calls."""
        self.pipeline.premise = self.test_premise
        self.pipeline.genre = "General Fiction"
        
        outline1 = self.pipeline.generate_outline()
        outline2 = self.pipeline.generate_outline()
        
        assert outline1["framework"] == outline2["framework"]
        assert outline1["structure"] == outline2["structure"]


class TestScaffolding:
    """Test suite for scaffold method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = ShortStoryPipeline()
        self.test_premise = {
            "idea": "A lighthouse keeper collects lost voices",
            "character": {"name": "Mara", "description": "A quiet keeper"},
            "theme": "Untold stories"
        }
        self.test_outline = {
            "premise": self.test_premise,
            "genre": "General Fiction",
            "framework": "narrative_arc",
            "structure": ["setup", "complication", "resolution"],
            "acts": {
                "beginning": "setup",
                "middle": "complication",
                "end": "resolution"
            }
        }
    
    def test_scaffold_basic(self):
        """Test basic scaffolding."""
        self.pipeline.outline = self.test_outline
        scaffold = self.pipeline.scaffold()
        
        assert scaffold is not None
        assert "outline" in scaffold
        assert "genre" in scaffold
        assert "constraints" in scaffold
        assert "pov" in scaffold
        assert "tone" in scaffold
        assert "pace" in scaffold
        assert "voice" in scaffold
        assert "sensory_focus" in scaffold
        assert scaffold["outline"] == self.test_outline
    
    def test_scaffold_distinctiveness_requirements(self):
        """Test that scaffold includes distinctiveness requirements."""
        self.pipeline.outline = self.test_outline
        scaffold = self.pipeline.scaffold()
        
        assert scaffold["distinctiveness_required"] is True
        assert scaffold["anti_generic_enforced"] is True
    
    def test_scaffold_default_values(self):
        """Test scaffold with default values when no genre specified."""
        self.pipeline.outline = self.test_outline
        self.pipeline.genre = None
        scaffold = self.pipeline.scaffold()
        
        assert scaffold["pov"] == "flexible"
        assert scaffold["tone"] == "balanced"
        assert scaffold["pace"] == "moderate"
        assert isinstance(scaffold["sensory_focus"], list)
    
    def test_scaffold_with_genre_constraints(self):
        """Test scaffold applies genre-specific constraints."""
        self.pipeline.outline = self.test_outline
        self.pipeline.genre = "Horror"
        scaffold = self.pipeline.scaffold(genre="Horror")
        
        genre_config = get_genre_config("Horror")
        constraints = genre_config.get("constraints", {})
        
        assert scaffold["genre"] == "Horror"
        assert scaffold["tone"] == constraints.get("tone", "balanced")
        assert scaffold["pace"] == constraints.get("pace", "moderate")
        assert scaffold["pov"] == constraints.get("pov_preference", "flexible")
        assert scaffold["sensory_focus"] == constraints.get("sensory_focus", ["balanced"])
    
    def test_scaffold_with_different_genres(self):
        """Test scaffold with different genres."""
        genres_to_test = ["Horror", "Romance", "Literary", "Crime / Noir"]
        
        for genre in genres_to_test:
            self.pipeline.outline = self.test_outline.copy()
            self.pipeline.outline["genre"] = genre
            self.pipeline.genre = genre
            scaffold = self.pipeline.scaffold(genre=genre)
            
            genre_config = get_genre_config(genre)
            constraints = genre_config.get("constraints", {})
            
            assert scaffold["genre"] == genre
            if "tone" in constraints:
                assert scaffold["tone"] == constraints["tone"]
            if "pace" in constraints:
                assert scaffold["pace"] == constraints["pace"]
    
    def test_scaffold_uses_outline_parameter(self):
        """Test that scaffold can use outline parameter instead of self.outline."""
        custom_outline = self.test_outline.copy()
        custom_outline["genre"] = "Romance"
        
        scaffold = self.pipeline.scaffold(outline=custom_outline)
        
        assert scaffold["outline"] == custom_outline
    
    def test_scaffold_uses_genre_parameter(self):
        """Test that scaffold can use genre parameter instead of self.genre."""
        self.pipeline.outline = self.test_outline
        self.pipeline.genre = None
        
        scaffold = self.pipeline.scaffold(genre="Horror")
        
        genre_config = get_genre_config("Horror")
        constraints = genre_config.get("constraints", {})
        
        assert scaffold["genre"] == "Horror"
        assert scaffold["tone"] == constraints.get("tone", "balanced")
    
    def test_scaffold_handles_missing_genre_config(self):
        """Test scaffold handles missing genre gracefully."""
        self.pipeline.outline = self.test_outline
        scaffold = self.pipeline.scaffold(genre="NonExistentGenre")
        
        # Should use default values
        assert scaffold is not None
        assert "pov" in scaffold
        assert "tone" in scaffold
        assert "pace" in scaffold
    
    def test_scaffold_constraints_structure(self):
        """Test that scaffold constraints are properly structured."""
        self.pipeline.outline = self.test_outline
        self.pipeline.genre = "Horror"
        scaffold = self.pipeline.scaffold()
        
        assert isinstance(scaffold["constraints"], dict)
        # Constraints should match genre config
        genre_config = get_genre_config("Horror")
        expected_constraints = genre_config.get("constraints", {})
        assert scaffold["constraints"] == expected_constraints
    
    def test_scaffold_consistency_with_outline_genre(self):
        """Test that scaffold genre matches outline genre."""
        self.pipeline.outline = self.test_outline
        self.pipeline.outline["genre"] = "Literary"
        self.pipeline.genre = "Literary"
        
        scaffold = self.pipeline.scaffold()
        
        assert scaffold["genre"] == "Literary"
        assert scaffold["outline"]["genre"] == "Literary"
    
    def test_scaffold_sensory_focus_list(self):
        """Test that sensory_focus is always a list."""
        genres_to_test = ["Horror", "Romance", "Literary", "General Fiction"]
        
        for genre in genres_to_test:
            self.pipeline.outline = self.test_outline.copy()
            self.pipeline.outline["genre"] = genre
            self.pipeline.genre = genre
            scaffold = self.pipeline.scaffold()
            
            assert isinstance(scaffold["sensory_focus"], list)
            assert len(scaffold["sensory_focus"]) > 0

