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

import functools
from typing import Dict, Any, List, Optional

# Primary genre configurations (single source of truth)
PRIMARY_GENRE_CONFIGS: Dict[str, Dict[str, Any]] = {
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

# Map alternative/legacy names to primary genre names
GENRE_ALIASES: Dict[str, str] = {
    "Crime / Noir": "Thriller",  # Noir is similar to Thriller
    "Speculative": "General Fiction",  # Speculative is a broad category
    "Literary": "General Fiction",  # Literary is a style, not a distinct genre structure
}

# Combine primary configs with aliases for backward compatibility
GENRE_CONFIGS: Dict[str, Dict[str, Any]] = {**PRIMARY_GENRE_CONFIGS}
for alias, primary_name in GENRE_ALIASES.items():
    if primary_name in PRIMARY_GENRE_CONFIGS:
        GENRE_CONFIGS[alias] = PRIMARY_GENRE_CONFIGS[primary_name]

# Valid framework types (derived from actual genre configs)
VALID_FRAMEWORKS = {
    "tension_escalation",
    "emotional_arc",
    "suspense_arc",
    "narrative_arc",
    "mystery_arc",  # Used by Crime / Noir alias
}

# Valid POV preference values
VALID_POV_PREFERENCES = {
    "first_or_limited",
    "first_or_third",
    "third_limited",
    "flexible",
    "third",
}


@functools.lru_cache(maxsize=32)
def get_genre_config(genre_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific genre.
    
    This function is cached to avoid redundant lookups. Since genre configs
    are static and loaded from memory, caching provides minimal overhead
    but ensures consistent performance under load.
    
    Supports both primary genre names and aliases. Aliases reference
    primary configurations to maintain a single source of truth.
    
    Args:
        genre_name: Name of the genre (case-insensitive)
    
    Returns:
        Dict with framework, outline, and constraints, or None if not found
    """
    # Handle None or empty string
    if not genre_name:
        return PRIMARY_GENRE_CONFIGS.get("General Fiction")
    
    # Case-insensitive lookup in primary configs first
    for key, value in PRIMARY_GENRE_CONFIGS.items():
        if key.lower() == genre_name.lower():
            return value
    
    # Check aliases
    for alias, primary_name in GENRE_ALIASES.items():
        if alias.lower() == genre_name.lower():
            return PRIMARY_GENRE_CONFIGS.get(primary_name)
    
    # Default to General Fiction if not found
    return PRIMARY_GENRE_CONFIGS.get("General Fiction")


def get_available_genres() -> List[str]:
    """
    Get list of available genre names.
    
    Returns:
        List of genre names (strings)
    """
    return list(GENRE_CONFIGS.keys())


def get_framework(genre_name: str) -> Optional[str]:
    """
    Get framework type for a genre.
    
    Args:
        genre_name: Name of the genre (case-insensitive)
    
    Returns:
        Framework type as a string, or None if genre not found
    """
    config = get_genre_config(genre_name)
    return config.get("framework") if config else None


def get_outline_structure(genre_name: str) -> Optional[List[str]]:
    """
    Get outline structure for a genre.
    
    Args:
        genre_name: Name of the genre (case-insensitive)
    
    Returns:
        Outline structure as a list, or None if genre not found
    """
    config = get_genre_config(genre_name)
    return config.get("outline") if config else None


def get_constraints(genre_name: str) -> Optional[Dict[str, Any]]:
    """
    Get constraints for a genre.
    
    Args:
        genre_name: Name of the genre (case-insensitive)
    
    Returns:
        Constraints as a dictionary, or None if genre not found
    """
    config = get_genre_config(genre_name)
    return config.get("constraints") if config else None

