"""
Story templates and examples library.

Provides pre-built story templates and examples that users can load
and modify as starting points for their own stories.
"""

from typing import Dict, List, Optional


# Template library organized by genre
STORY_TEMPLATES: Dict[str, List[Dict[str, any]]] = {
    "Literary": [
        {
            "name": "The Lighthouse Keeper",
            "idea": "A lighthouse keeper who collects lost voices in glass jars",
            "character": {
                "name": "Mara",
                "description": "A lighthouse keeper with an unusual collection",
                "quirks": ["Never speaks above a whisper", "Counts everything in threes"],
                "contradictions": "Fiercely protective but terrified of connection"
            },
            "theme": "What happens to the stories we never tell?",
            "description": "A contemplative story about memory, loss, and the stories we preserve"
        },
        {
            "name": "The Last Bookstore",
            "idea": "A bookstore that only sells books that have never been read",
            "character": {
                "name": "Elias",
                "description": "An elderly bookseller who can sense unread stories",
                "quirks": ["Speaks in literary quotes", "Never opens a book"],
                "contradictions": "Loves stories but fears finishing them"
            },
            "theme": "What is the value of an unread story?",
            "description": "A meditation on potential, possibility, and the stories that remain untold"
        }
    ],
    "Horror": [
        {
            "name": "The Reflection",
            "idea": "A mirror that shows you not your reflection, but the person you're becoming",
            "character": {
                "name": "Dr. Chen",
                "description": "A psychologist studying the mirror's effects",
                "quirks": ["Never looks directly at mirrors", "Takes notes in reverse"],
                "contradictions": "Studies fear but is terrified of self-knowledge"
            },
            "theme": "What happens when we see ourselves too clearly?",
            "description": "A psychological horror about self-perception and transformation"
        },
        {
            "name": "The Collection",
            "idea": "A museum curator who discovers the exhibits are watching back",
            "character": {
                "name": "Victoria",
                "description": "A meticulous curator with perfect memory",
                "quirks": ["Arranges everything in perfect symmetry", "Never turns her back on exhibits"],
                "contradictions": "Seeks order but is drawn to chaos"
            },
            "theme": "What do we preserve, and what preserves us?",
            "description": "A slow-burn horror about observation, preservation, and being watched"
        }
    ],
    "Science Fiction": [
        {
            "name": "The Last Transmission",
            "idea": "An astronaut receives messages from Earth that stopped broadcasting 50 years ago",
            "character": {
                "name": "Commander Reyes",
                "description": "A mission specialist on a deep space journey",
                "quirks": ["Speaks in mission protocols", "Counts time in light-years"],
                "contradictions": "Longs for home but chose to leave it"
            },
            "theme": "What remains when connection is lost?",
            "description": "A story about isolation, memory, and the persistence of human connection"
        },
        {
            "name": "The Memory Archive",
            "idea": "A future where memories can be stored and traded, but some are too dangerous to keep",
            "character": {
                "name": "Alex",
                "description": "A memory archivist who has forgotten their own past",
                "quirks": ["Remembers everything except themselves", "Speaks in fragments"],
                "contradictions": "Preserves memories but has none of their own"
            },
            "theme": "What makes us who we are?",
            "description": "A philosophical sci-fi about identity, memory, and what we choose to forget"
        }
    ],
    "Mystery": [
        {
            "name": "The Disappearing Words",
            "idea": "A detective investigates crimes where the only evidence is what's missing from books",
            "character": {
                "name": "Detective Morgan",
                "description": "A book-loving detective with photographic memory",
                "quirks": ["Quotes literature at crime scenes", "Reads everything backwards"],
                "contradictions": "Solves mysteries but can't solve their own"
            },
            "theme": "What do absences tell us?",
            "description": "A literary mystery about what's not there, and why it matters"
        }
    ],
    "Romance": [
        {
            "name": "The Time Between",
            "idea": "Two people who can only meet in the spaces between seconds",
            "character": {
                "name": "Luna",
                "description": "A physicist who discovered the temporal gaps",
                "quirks": ["Speaks in precise measurements", "Never finishes sentences"],
                "contradictions": "Understands time but can't make it last"
            },
            "theme": "What happens in the moments we can't measure?",
            "description": "A romantic story about connection, timing, and the spaces between"
        }
    ],
    "General Fiction": [
        {
            "name": "The Garden of Lost Things",
            "idea": "A gardener who tends plants that grow from forgotten objects",
            "character": {
                "name": "Sam",
                "description": "A quiet gardener with green fingers and a broken heart",
                "quirks": ["Names every plant", "Talks to the garden"],
                "contradictions": "Grows things but can't grow past loss"
            },
            "theme": "What grows from what we've lost?",
            "description": "A gentle story about grief, growth, and finding beauty in loss"
        }
    ]
}


def get_templates_for_genre(genre: str) -> List[Dict[str, any]]:
    """
    Get all templates for a specific genre.
    
    Args:
        genre: Genre name
        
    Returns:
        List of template dictionaries
    """
    return STORY_TEMPLATES.get(genre, [])


def get_all_templates() -> Dict[str, List[Dict[str, any]]]:
    """
    Get all templates organized by genre.
    
    Returns:
        Dictionary mapping genre names to lists of templates
    """
    return STORY_TEMPLATES


def get_template(genre: str, template_name: str) -> Optional[Dict[str, any]]:
    """
    Get a specific template by genre and name.
    
    Args:
        genre: Genre name
        template_name: Name of the template
        
    Returns:
        Template dictionary or None if not found
    """
    templates = get_templates_for_genre(genre)
    for template in templates:
        if template.get("name") == template_name:
            return template
    return None


def get_available_template_genres() -> List[str]:
    """
    Get list of genres that have templates available.
    
    Returns:
        List of genre names
    """
    return list(STORY_TEMPLATES.keys())

