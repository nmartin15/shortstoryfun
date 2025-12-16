"""
Genre configurations for short story pipeline.

Each genre defines framework, outline structure, and constraints
that drive the scaffolding and drafting stages.

IMPORTANT: Genres provide STRUCTURE, not FORMULAS.
- Genres guide framework and pacing, but stories must still be DISTINCTIVE
- Genre constraints (tone, pace) are starting points, not rigid rules
- All stories must pass distinctiveness validation regardless of genre
- "Every word must earn its place" applies to ALL genres

See CONCEPTS.md for core principles of distinctiveness and memorability.
"""

GENRE_CONFIGS = {
    "Horror": {
        "framework": "tension_escalation",
        "outline": ["setup", "rising dread", "twist ending"],
        "constraints": {
            "tone": "dark",
            "pace": "fast",
            "pov_preference": "first_or_limited",
            "sensory_focus": ["sound", "touch", "atmosphere"]
        }
    },
    "Romance": {
        "framework": "emotional_arc",
        "outline": ["connection", "disruption", "resolution"],
        "constraints": {
            "tone": "warm",
            "pace": "moderate",
            "pov_preference": "first_or_third",
            "sensory_focus": ["sight", "emotion", "intimacy"]
        }
    },
    "Crime / Noir": {
        "framework": "mystery_arc",
        "outline": ["crime setup", "investigation", "resolution/failure"],
        "constraints": {
            "tone": "gritty",
            "voice": "detached",
            "pov_preference": "first_or_limited",
            "sensory_focus": ["sight", "detail", "atmosphere"]
        }
    },
    "Speculative": {
        "framework": "world_building_arc",
        "outline": ["world setup", "conflict", "resolution/implication"],
        "constraints": {
            "tone": "imaginative",
            "pace": "compressed",
            "pov_preference": "third",
            "sensory_focus": ["sight", "world_detail", "concept"]
        }
    },
    "Literary": {
        "framework": "character_arc",
        "outline": ["character introduction", "internal conflict", "transformation"],
        "constraints": {
            "tone": "nuanced",
            "pace": "deliberate",
            "pov_preference": "third_limited",
            "sensory_focus": ["detail", "emotion", "subtext"]
        }
    },
    "Thriller": {
        "framework": "suspense_arc",
        "outline": ["inciting threat", "escalating stakes", "climax"],
        "constraints": {
            "tone": "urgent",
            "pace": "fast",
            "pov_preference": "third_limited",
            "sensory_focus": ["action", "tension", "urgency"]
        }
    },
    "General Fiction": {
        "framework": "narrative_arc",
        "outline": ["setup", "complication", "resolution"],
        "constraints": {
            "tone": "balanced",
            "pace": "moderate",
            "pov_preference": "flexible",
            "sensory_focus": ["balanced"]
        }
    }
}


def get_genre_config(genre_name):
    """
    Get configuration for a specific genre.
    
    Args:
        genre_name: Name of the genre (case-insensitive)
    
    Returns:
        Dict with framework, outline, and constraints, or None if not found
    """
    # Case-insensitive lookup
    for key, value in GENRE_CONFIGS.items():
        if key.lower() == genre_name.lower():
            return value
    
    # Default to General Fiction if not found
    return GENRE_CONFIGS.get("General Fiction")


def get_available_genres():
    """
    Get list of available genre names.
    
    Returns:
        List of genre names
    """
    return list(GENRE_CONFIGS.keys())


def get_framework(genre_name):
    """Get framework type for a genre."""
    config = get_genre_config(genre_name)
    return config.get("framework") if config else None


def get_outline_structure(genre_name):
    """Get outline structure for a genre."""
    config = get_genre_config(genre_name)
    return config.get("outline") if config else None


def get_constraints(genre_name):
    """Get constraints for a genre."""
    config = get_genre_config(genre_name)
    return config.get("constraints") if config else None

