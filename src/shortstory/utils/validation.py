"""
Distinctiveness and quality validation utilities.

See CONCEPTS.md for definitions of distinctiveness requirements.
"""

# Common clichéd phrases to flag
COMMON_CLICHES = [
    "it was a dark and stormy night",
    "once upon a time",
    "in the nick of time",
    "all hell broke loose",
    "calm before the storm",
    "needle in a haystack",
    "tip of the iceberg",
    "dead as a doornail",
    "raining cats and dogs",
    "piece of cake",
    "blessing in disguise",
    "beat around the bush",
    "break the ice",
    "hit the nail on the head",
    "let the cat out of the bag",
]

# Generic character archetypes to flag
GENERIC_ARCHETYPES = [
    "the chosen one",
    "the wise old mentor",
    "the damsel in distress",
    "the evil villain",
    "the comic relief",
    "the mysterious stranger",
    "the rebellious teenager",
    "the perfect hero",
]


def check_distinctiveness(text, character=None, idea=None):
    """
    Check for generic language, clichés, and stock elements.
    
    Args:
        text: Text to check (can be idea, description, dialogue, etc.)
        character: Character description (optional)
        idea: Story idea (optional)
    
    Returns:
        Dict with flags and suggestions:
        {
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": list,
            "has_generic_archetype": bool,
            "generic_elements": list,
            "distinctiveness_score": float,  # 0-1, higher = more distinctive
            "suggestions": list
        }
    """
    if not text:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    
    text_lower = text.lower()
    
    # Check for clichés
    found_cliches = []
    for cliche in COMMON_CLICHES:
        if cliche in text_lower:
            found_cliches.append(cliche)
    
    # Check for generic archetypes (if character provided)
    generic_elements = []
    if character:
        char_lower = str(character).lower()
        for archetype in GENERIC_ARCHETYPES:
            if archetype in char_lower:
                generic_elements.append(archetype)
    
    # Calculate distinctiveness score
    # Lower score = more generic
    cliche_penalty = len(found_cliches) * 0.2
    archetype_penalty = len(generic_elements) * 0.3
    distinctiveness_score = max(0.0, 1.0 - cliche_penalty - archetype_penalty)
    
    # Generate suggestions
    suggestions = []
    if found_cliches:
        suggestions.append(
            f"Found {len(found_cliches)} clichéd phrase(s). "
            "Replace with specific, vivid language."
        )
    if generic_elements:
        suggestions.append(
            f"Character shows generic archetype traits. "
            "Add unique quirks, contradictions, or specific details."
        )
    
    return {
        "has_cliches": len(found_cliches) > 0,
        "cliche_count": len(found_cliches),
        "found_cliches": found_cliches,
        "has_generic_archetype": len(generic_elements) > 0,
        "generic_elements": generic_elements,
        "distinctiveness_score": distinctiveness_score,
        "suggestions": suggestions,
    }


def validate_premise(idea, character, theme):
    """
    Validate premise for distinctiveness and completeness.
    
    Args:
        idea: Story idea
        character: Character description
        theme: Central theme
    
    Returns:
        Dict with validation results:
        {
            "is_valid": bool,
            "distinctiveness": dict,  # From check_distinctiveness
            "completeness": dict,
            "warnings": list,
            "errors": list
        }
    """
    errors = []
    warnings = []
    
    # Check completeness
    completeness = {
        "has_idea": bool(idea and str(idea).strip()),
        "has_character": bool(character),
        "has_theme": bool(theme and str(theme).strip()),
    }
    
    if not completeness["has_idea"]:
        errors.append("Story idea is required")
    if not completeness["has_character"]:
        errors.append("Character description is required")
    if not completeness["has_theme"]:
        errors.append("Theme is required")
    
    # Check distinctiveness
    idea_check = check_distinctiveness(idea) if idea else {}
    char_check = check_distinctiveness(None, character=character) if character else {}
    theme_check = check_distinctiveness(theme) if theme else {}
    
    # Combine distinctiveness scores
    scores = [
        idea_check.get("distinctiveness_score", 1.0),
        char_check.get("distinctiveness_score", 1.0),
        theme_check.get("distinctiveness_score", 1.0),
    ]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    # Generate warnings for low distinctiveness
    if avg_score < 0.7:
        warnings.append(
            f"Premise distinctiveness score is {avg_score:.2f}. "
            "Consider adding more specific details, unique quirks, or unexpected elements."
        )
    
    if idea_check.get("has_cliches"):
        warnings.extend(idea_check.get("suggestions", []))
    if char_check.get("has_generic_archetype"):
        warnings.extend(char_check.get("suggestions", []))
    
    distinctiveness = {
        "idea": idea_check,
        "character": char_check,
        "theme": theme_check,
        "average_score": avg_score,
    }
    
    return {
        "is_valid": len(errors) == 0,
        "distinctiveness": distinctiveness,
        "completeness": completeness,
        "warnings": warnings,
        "errors": errors,
    }

