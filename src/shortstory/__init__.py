"""
Short Story Pipeline

A modular pipeline for short story creation that prioritizes
distinctive voice, memorable characters, and non-generic language.
"""

from .genres import (
    GENRE_CONFIGS,
    get_genre_config,
    get_available_genres,
    get_framework,
    get_outline_structure,
    get_constraints,
)

__version__ = "0.1.0"

__all__ = [
    "GENRE_CONFIGS",
    "get_genre_config",
    "get_available_genres",
    "get_framework",
    "get_outline_structure",
    "get_constraints",
]

