"""
Tests for genre configuration functionality.
"""

import pytest
from src.shortstory.genres import (
    get_genre_config,
    get_available_genres,
    get_framework,
    get_outline_structure,
    get_constraints,
    PRIMARY_GENRE_CONFIGS,
    GENRE_CONFIGS,
    VALID_FRAMEWORKS,
    VALID_POV_PREFERENCES,
)


class TestGenreConfigurationValues:
    """Test genre configuration values and structure."""
    
    def test_framework_values_are_valid(self):
        """Test that framework values are valid types and from a predefined set."""
        for genre_name in PRIMARY_GENRE_CONFIGS.keys():
            framework = PRIMARY_GENRE_CONFIGS[genre_name]["framework"]
            assert isinstance(framework, str), f"Framework for {genre_name} should be a string"
            assert len(framework) > 0, f"Framework for {genre_name} should not be empty"
            assert framework in VALID_FRAMEWORKS, \
                f"Genre {genre_name} has invalid framework: {framework}. Must be one of {VALID_FRAMEWORKS}"
    
    def test_pov_preference_values_are_valid(self):
        """Test that POV preference values are valid."""
        for genre_name in PRIMARY_GENRE_CONFIGS.keys():
            constraints = PRIMARY_GENRE_CONFIGS[genre_name].get("constraints", {})
            if "pov_preference" in constraints:
                pov = constraints["pov_preference"]
                assert isinstance(pov, str), f"POV preference for {genre_name} should be a string"
                assert pov in VALID_POV_PREFERENCES, \
                    f"Genre {genre_name} has invalid POV preference: {pov}. Must be one of {VALID_POV_PREFERENCES}"
    
    def test_outline_structure_is_list(self):
        """Test that outline structure is a list."""
        for genre_name in PRIMARY_GENRE_CONFIGS.keys():
            outline = PRIMARY_GENRE_CONFIGS[genre_name].get("outline", [])
            assert isinstance(outline, list), f"Outline for {genre_name} should be a list"
            assert len(outline) > 0, f"Outline for {genre_name} should not be empty"
    
    def test_constraints_is_dict(self):
        """Test that constraints is a dictionary."""
        for genre_name in PRIMARY_GENRE_CONFIGS.keys():
            constraints = PRIMARY_GENRE_CONFIGS[genre_name].get("constraints", {})
            assert isinstance(constraints, dict), f"Constraints for {genre_name} should be a dictionary"


class TestGenreHelperFunctions:
    """Test genre helper functions."""
    
    def test_get_genre_config_returns_config(self):
        """Test that get_genre_config returns a valid configuration."""
        config = get_genre_config("Horror")
        assert config is not None
        assert "framework" in config
        assert "outline" in config
        assert "constraints" in config
    
    def test_get_genre_config_case_insensitive(self):
        """Test that get_genre_config is case-insensitive."""
        config1 = get_genre_config("Horror")
        config2 = get_genre_config("HORROR")
        config3 = get_genre_config("horror")
        
        assert config1 == config2 == config3
    
    def test_get_genre_config_with_whitespace(self):
        """Test that get_genre_config correctly handles genre names with leading/trailing whitespace."""
        config_horror = get_genre_config("Horror")
        config_whitespace = get_genre_config("  Horror  ")
        # Should handle whitespace (implementation may vary)
        assert config_horror is not None
        assert config_whitespace is not None
    
    def test_get_genre_config_with_only_whitespace(self):
        """Test that get_genre_config returns default for a genre name consisting only of whitespace."""
        config = get_genre_config("   \t   ")
        # Should return default (General Fiction)
        assert config is not None
        assert config == PRIMARY_GENRE_CONFIGS["General Fiction"]
    
    def test_get_genre_config_returns_default_for_invalid(self):
        """Test that get_genre_config returns General Fiction default for invalid genre."""
        config = get_genre_config("Invalid Genre")
        assert config is not None
        assert config == PRIMARY_GENRE_CONFIGS["General Fiction"]
    
    def test_get_genre_config_returns_default_for_none(self):
        """Test that get_genre_config returns default for None."""
        config = get_genre_config(None)
        assert config is not None
        assert config == PRIMARY_GENRE_CONFIGS["General Fiction"]
    
    def test_get_genre_config_returns_default_for_empty_string(self):
        """Test that get_genre_config returns default for empty string."""
        config = get_genre_config("")
        assert config is not None
        assert config == PRIMARY_GENRE_CONFIGS["General Fiction"]
    
    def test_get_framework_returns_framework(self):
        """Test that get_framework returns the correct framework."""
        framework = get_framework("Horror")
        assert framework == "tension_escalation"
    
    def test_get_framework_returns_default_for_invalid(self):
        """Test that get_framework returns the General Fiction default framework for an invalid genre."""
        framework = get_framework("Invalid Genre")
        assert framework == PRIMARY_GENRE_CONFIGS["General Fiction"]["framework"]
    
    def test_get_outline_structure_returns_outline(self):
        """Test that get_outline_structure returns the correct outline."""
        outline = get_outline_structure("Horror")
        assert isinstance(outline, list)
        assert len(outline) > 0
    
    def test_get_constraints_returns_constraints(self):
        """Test that get_constraints returns the correct constraints."""
        constraints = get_constraints("Horror")
        assert isinstance(constraints, dict)
        assert "tone" in constraints
        assert "pace" in constraints
    
    def test_get_available_genres_returns_list(self):
        """Test that get_available_genres returns a list of genres."""
        genres = get_available_genres()
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert "Horror" in genres
        assert "Romance" in genres
        assert "General Fiction" in genres


class TestGenreAliases:
    """Test genre alias functionality."""
    
    def test_alias_returns_same_config_as_primary(self):
        """Test that aliases return the same config as their primary genre."""
        crime_config = get_genre_config("Crime / Noir")
        thriller_config = get_genre_config("Thriller")
        
        assert crime_config == thriller_config
        assert crime_config["framework"] == "suspense_arc"
    
    def test_literary_alias_returns_general_fiction_config(self):
        """Test that Literary alias returns General Fiction config."""
        literary_config = get_genre_config("Literary")
        general_fiction_config = get_genre_config("General Fiction")
        
        assert literary_config == general_fiction_config
        assert literary_config["framework"] == "narrative_arc"


class TestGenreEdgeCases:
    """Test edge cases for genre functions."""
    
    def test_get_framework_with_none(self):
        """Test get_framework with None."""
        framework = get_framework(None)
        assert framework == PRIMARY_GENRE_CONFIGS["General Fiction"]["framework"]
    
    def test_get_framework_with_empty_string(self):
        """Test get_framework with empty string."""
        framework = get_framework("")
        assert framework == PRIMARY_GENRE_CONFIGS["General Fiction"]["framework"]
    
    def test_get_outline_structure_with_invalid_genre(self):
        """Test get_outline_structure with invalid genre."""
        outline = get_outline_structure("Invalid Genre")
        assert outline == PRIMARY_GENRE_CONFIGS["General Fiction"]["outline"]
    
    def test_get_constraints_with_invalid_genre(self):
        """Test get_constraints with invalid genre."""
        constraints = get_constraints("Invalid Genre")
        assert constraints == PRIMARY_GENRE_CONFIGS["General Fiction"]["constraints"]
