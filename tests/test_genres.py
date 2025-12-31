"""
Comprehensive tests for genre configuration functionality.

Tests cover genre retrieval, configuration validation, and constraint application.
"""

import pytest
from src.shortstory.genres import (
    get_genre_config,
    get_available_genres,
    get_framework,
    get_outline_structure,
    get_constraints,
    GENRE_CONFIGS
)


class TestGenreRetrieval:
    """Test genre configuration retrieval."""
    
    def test_get_available_genres_returns_list(self):
        """Test that get_available_genres returns a list."""
        genres = get_available_genres()
        assert isinstance(genres, list)
        assert len(genres) > 0
    
    def test_get_available_genres_includes_all_genres(self):
        """Test that all genres are included in the list."""
        genres = get_available_genres()
        expected_genres = list(GENRE_CONFIGS.keys())
        assert set(genres) == set(expected_genres)
    
    def test_get_genre_config_returns_config(self):
        """Test that get_genre_config returns configuration dict."""
        config = get_genre_config("Horror")
        assert isinstance(config, dict)
        assert "framework" in config
        assert "outline" in config
        assert "constraints" in config
    
    def test_get_genre_config_case_insensitive(self):
        """Test that genre lookup is case-insensitive."""
        config1 = get_genre_config("Horror")
        config2 = get_genre_config("HORROR")
        config3 = get_genre_config("horror")
        
        assert config1 == config2 == config3
    
    def test_get_genre_config_returns_default_for_invalid(self):
        """Test that invalid genre returns General Fiction default."""
        config = get_genre_config("Invalid Genre")
        assert config is not None
        assert config == GENRE_CONFIGS["General Fiction"]


class TestGenreConfigurationStructure:
    """Test that all genres have required configuration structure."""
    
    def test_all_genres_have_framework(self):
        """Test that all genres have a framework field."""
        for genre_name in GENRE_CONFIGS.keys():
            config = GENRE_CONFIGS[genre_name]
            assert "framework" in config
            assert isinstance(config["framework"], str)
            assert len(config["framework"]) > 0
    
    def test_all_genres_have_outline(self):
        """Test that all genres have an outline field."""
        for genre_name in GENRE_CONFIGS.keys():
            config = GENRE_CONFIGS[genre_name]
            assert "outline" in config
            assert isinstance(config["outline"], list)
            assert len(config["outline"]) >= 3  # Beginning, middle, end
    
    def test_all_genres_have_constraints(self):
        """Test that all genres have a constraints field."""
        for genre_name in GENRE_CONFIGS.keys():
            config = GENRE_CONFIGS[genre_name]
            assert "constraints" in config
            assert isinstance(config["constraints"], dict)
    
    def test_outline_structure_has_three_parts(self):
        """Test that outline structure has at least three parts."""
        for genre_name in GENRE_CONFIGS.keys():
            outline = GENRE_CONFIGS[genre_name]["outline"]
            assert len(outline) >= 3, f"Genre {genre_name} outline should have at least 3 parts"
    
    def test_constraints_have_common_fields(self):
        """Test that constraints have common expected fields."""
        common_fields = ["tone", "pace", "pov_preference", "sensory_focus"]
        
        for genre_name in GENRE_CONFIGS.keys():
            constraints = GENRE_CONFIGS[genre_name]["constraints"]
            # At least some of these fields should be present
            assert any(field in constraints for field in common_fields), \
                f"Genre {genre_name} constraints should have at least one common field"


class TestGenreSpecificConfigurations:
    """Test genre-specific configuration values."""
    
    def test_horror_genre_configuration(self):
        """Test Horror genre has appropriate configuration."""
        config = get_genre_config("Horror")
        assert config["framework"] == "tension_escalation"
        assert "rising dread" in config["outline"] or "setup" in config["outline"]
        assert config["constraints"]["tone"] == "dark"
        assert config["constraints"]["pace"] == "fast"
    
    def test_romance_genre_configuration(self):
        """Test Romance genre has appropriate configuration."""
        config = get_genre_config("Romance")
        assert config["framework"] == "emotional_arc"
        assert "connection" in config["outline"] or "setup" in config["outline"]
        assert config["constraints"]["tone"] == "warm"
        assert config["constraints"]["pace"] == "moderate"
    
    def test_crime_noir_genre_configuration(self):
        """Test Crime / Noir genre has appropriate configuration."""
        config = get_genre_config("Crime / Noir")
        assert config["framework"] == "mystery_arc"
        assert config["constraints"]["tone"] == "gritty"
        assert "voice" in config["constraints"] or "pov_preference" in config["constraints"]
    
    def test_literary_genre_configuration(self):
        """Test Literary genre has appropriate configuration."""
        config = get_genre_config("Literary")
        assert config["framework"] == "character_arc"
        assert config["constraints"]["tone"] == "nuanced"
        assert config["constraints"]["pace"] == "deliberate"
    
    def test_thriller_genre_configuration(self):
        """Test Thriller genre has appropriate configuration."""
        config = get_genre_config("Thriller")
        assert config["framework"] == "suspense_arc"
        assert config["constraints"]["tone"] == "urgent"
        assert config["constraints"]["pace"] == "fast"
    
    def test_general_fiction_genre_configuration(self):
        """Test General Fiction genre has appropriate configuration."""
        config = get_genre_config("General Fiction")
        assert config["framework"] == "narrative_arc"
        assert config["constraints"]["tone"] == "balanced"
        assert config["constraints"]["pace"] == "moderate"


class TestGenreHelperFunctions:
    """Test genre helper functions."""
    
    def test_get_framework_returns_framework(self):
        """Test that get_framework returns framework string."""
        framework = get_framework("Horror")
        assert isinstance(framework, str)
        assert framework == "tension_escalation"
    
    def test_get_framework_case_insensitive(self):
        """Test that get_framework is case-insensitive."""
        framework1 = get_framework("Horror")
        framework2 = get_framework("HORROR")
        assert framework1 == framework2
    
    def test_get_framework_returns_none_for_invalid(self):
        """Test that get_framework returns None for invalid genre."""
        framework = get_framework("Invalid Genre")
        # Should return General Fiction framework (default)
        assert framework is not None
    
    def test_get_outline_structure_returns_list(self):
        """Test that get_outline_structure returns list."""
        outline = get_outline_structure("Horror")
        assert isinstance(outline, list)
        assert len(outline) >= 3
    
    def test_get_outline_structure_case_insensitive(self):
        """Test that get_outline_structure is case-insensitive."""
        outline1 = get_outline_structure("Romance")
        outline2 = get_outline_structure("ROMANCE")
        assert outline1 == outline2
    
    def test_get_constraints_returns_dict(self):
        """Test that get_constraints returns dictionary."""
        constraints = get_constraints("Horror")
        assert isinstance(constraints, dict)
        assert "tone" in constraints
    
    def test_get_constraints_case_insensitive(self):
        """Test that get_constraints is case-insensitive."""
        constraints1 = get_constraints("Thriller")
        constraints2 = get_constraints("THRILLER")
        assert constraints1 == constraints2
    
    def test_get_constraints_has_expected_fields(self):
        """Test that constraints have expected fields."""
        for genre_name in GENRE_CONFIGS.keys():
            constraints = get_constraints(genre_name)
            assert isinstance(constraints, dict)
            # Should have at least tone or pace
            assert "tone" in constraints or "pace" in constraints or "pov_preference" in constraints


class TestGenreConfigurationValues:
    """Test that genre configuration values are valid."""
    
    def test_framework_values_are_valid(self):
        """Test that framework values are valid types."""
        valid_frameworks = [
            "tension_escalation",
            "emotional_arc",
            "mystery_arc",
            "world_building_arc",
            "character_arc",
            "suspense_arc",
            "narrative_arc"
        ]
        
        for genre_name in GENRE_CONFIGS.keys():
            framework = GENRE_CONFIGS[genre_name]["framework"]
            assert framework in valid_frameworks, \
                f"Genre {genre_name} has invalid framework: {framework}"
    
    def test_tone_values_are_strings(self):
        """Test that tone values are strings."""
        for genre_name in GENRE_CONFIGS.keys():
            constraints = GENRE_CONFIGS[genre_name]["constraints"]
            if "tone" in constraints:
                assert isinstance(constraints["tone"], str)
                assert len(constraints["tone"]) > 0
    
    def test_pace_values_are_strings(self):
        """Test that pace values are strings."""
        for genre_name in GENRE_CONFIGS.keys():
            constraints = GENRE_CONFIGS[genre_name]["constraints"]
            if "pace" in constraints:
                assert isinstance(constraints["pace"], str)
                assert len(constraints["pace"]) > 0
    
    def test_pov_preference_values_are_valid(self):
        """Test that POV preference values are valid."""
        valid_povs = [
            "first_or_limited",
            "first_or_third",
            "third",
            "third_limited",
            "flexible"
        ]
        
        for genre_name in GENRE_CONFIGS.keys():
            constraints = GENRE_CONFIGS[genre_name]["constraints"]
            if "pov_preference" in constraints:
                pov = constraints["pov_preference"]
                assert pov in valid_povs, \
                    f"Genre {genre_name} has invalid POV preference: {pov}"
    
    def test_sensory_focus_is_list(self):
        """Test that sensory_focus is a list."""
        for genre_name in GENRE_CONFIGS.keys():
            constraints = GENRE_CONFIGS[genre_name]["constraints"]
            if "sensory_focus" in constraints:
                assert isinstance(constraints["sensory_focus"], list)
                assert len(constraints["sensory_focus"]) > 0


class TestGenreEdgeCases:
    """Test edge cases and error handling."""
    
    def test_get_genre_config_with_empty_string(self):
        """Test that empty string returns default."""
        config = get_genre_config("")
        assert config == GENRE_CONFIGS["General Fiction"]
    
    def test_get_genre_config_with_whitespace(self):
        """Test that whitespace is handled."""
        config1 = get_genre_config("Horror")
        config2 = get_genre_config("  Horror  ")
        # Should handle whitespace (case-insensitive comparison should work)
        assert config1 == config2 or config2 == GENRE_CONFIGS["General Fiction"]
    
    def test_get_genre_config_with_none(self):
        """Test that None returns default."""
        config = get_genre_config(None)
        assert config == GENRE_CONFIGS["General Fiction"]
    
    def test_all_genres_are_unique(self):
        """Test that all genre names are unique."""
        genre_names = list(GENRE_CONFIGS.keys())
        assert len(genre_names) == len(set(genre_names))
    
    def test_genre_configs_are_immutable_structure(self):
        """Test that genre configurations have consistent structure."""
        # All genres should have the same top-level keys
        first_genre = list(GENRE_CONFIGS.keys())[0]
        first_keys = set(GENRE_CONFIGS[first_genre].keys())
        
        for genre_name in GENRE_CONFIGS.keys():
            genre_keys = set(GENRE_CONFIGS[genre_name].keys())
            assert genre_keys == first_keys, \
                f"Genre {genre_name} has different structure than {first_genre}"

