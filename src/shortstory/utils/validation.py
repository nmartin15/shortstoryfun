"""
Validation utilities for story content.

Provides functions for validating story distinctiveness, premises, and character voices.
"""

from typing import Dict, List, Optional, Pattern
import logging
import re

logger = logging.getLogger(__name__)

# Distinctiveness scoring constants
# These define the penalty structure for calculating distinctiveness scores
MAX_CLICHE_PENALTY = 0.4  # Maximum penalty for clichés (40% of score)
PER_CLICHE_PENALTY = 0.1  # Penalty per cliché detected
ARCHETYPE_PENALTY = 0.3  # Penalty for generic archetypes (30% of score)
MAX_PATTERN_PENALTY = 0.3  # Maximum penalty for generic patterns (30% of score)
PER_PATTERN_PENALTY = 0.05  # Penalty per generic pattern detected

# Pattern detection constants
# These define the patterns to detect for generic language
VAGUE_INTENSIFIERS = ['very', 'really', 'quite', 'rather', 'pretty', 'somewhat']
OVERUSED_PHRASES = [
    'it was then that', 'little did they know', 'in that moment',
    'her heart pounded', 'his eyes widened', 'time seemed to stand still'
]
STOCK_PHRASES = [
    'she knew', 'he realized', 'it dawned on', 'suddenly',
    'without warning', 'out of nowhere'
]

# Generic archetype constants
# These define the archetypes to detect in character descriptions
GENERIC_ARCHETYPES = [
    "chosen one",
    "destined hero",
    "reluctant hero",
    "wise old mentor",
    "damsel in distress",
    "evil overlord",
    "tragic hero",
    "noble warrior"
]


def _generate_suggestions(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict]
) -> List[str]:
    """
    Generate context-aware suggestions from detection results.
    
    Args:
        cliche_results: A dictionary containing the results from `detect_cliches()`.
                        Expected to have keys like 'found_cliches' and 'cliche_details'.
        archetype_results: A dictionary containing the results from `detect_generic_archetypes()`.
                           Expected to have keys like 'generic_elements'.
        pattern_results: A list of dictionaries, where each dictionary represents
                         a detected generic language pattern, typically from `detect_generic_patterns_from_text()`.
                         Each dict is expected to have keys like 'type', 'in_dialogue', and 'suggestion'.
    
    Returns:
        list[str]: List of suggestion messages generated based on the detection results.
    """
    suggestions = []
    
    # Add cliché suggestions
    cliche_details = cliche_results.get("cliche_details", [])
    for detail in cliche_details[:3]:  # Limit to first 3
        if "suggestion" in detail:
            suggestions.append(detail["suggestion"])
    
    # Add archetype suggestions
    generic_elements = archetype_results.get("generic_elements", [])
    if generic_elements:
        suggestions.append(
            f"Consider adding unique traits to move beyond generic archetypes: {', '.join(generic_elements[:3])}"
        )
    
    # Add pattern suggestions
    for pattern in pattern_results[:3]:  # Limit to first 3
        if "suggestion" in pattern:
            suggestions.append(pattern["suggestion"])
    
    return suggestions


def _detect_vague_intensifiers(text_lower: str) -> List[Dict]:
    """
    Detect vague intensifiers in text (e.g., "very", "really", "quite").
    
    Args:
        text_lower: Lowercased text to analyze
        
    Returns:
        List of detected vague intensifier pattern dictionaries
    """
    patterns = []
    for intensifier in VAGUE_INTENSIFIERS:
        if f' {intensifier} ' in text_lower or text_lower.startswith(intensifier + ' '):
            patterns.append({
                'type': 'vague_intensifier',
                'pattern': intensifier,
                'in_dialogue': False,  # Would need dialogue detection to determine
                'suggestion': f'Replace "{intensifier}" with a more specific descriptor'
            })
    return patterns


def _detect_overused_phrases(text_lower: str) -> List[Dict]:
    """
    Detect overused phrases in text.
    
    Args:
        text_lower: Lowercased text to analyze
        
    Returns:
        List of detected overused phrase pattern dictionaries
    """
    patterns = []
    for phrase in OVERUSED_PHRASES:
        if phrase in text_lower:
            patterns.append({
                'type': 'overused_phrase',
                'pattern': phrase,
                'in_dialogue': False,
                'suggestion': f'Replace overused phrase "{phrase}" with something more original'
            })
    return patterns


def _detect_stock_phrases(text_lower: str) -> List[Dict]:
    """
    Detect stock phrases in text.
    
    Args:
        text_lower: Lowercased text to analyze
        
    Returns:
        List of detected stock phrase pattern dictionaries
    """
    patterns = []
    for phrase in STOCK_PHRASES:
        if phrase in text_lower:
            patterns.append({
                'type': 'stock_phrase',
                'pattern': phrase,
                'in_dialogue': False,
                'suggestion': f'Replace stock phrase "{phrase}" with more specific language'
            })
    return patterns


def detect_generic_patterns_from_text(text: str) -> List[Dict]:
    """
    Detect generic language patterns in the given text.
    
    This is a public orchestrator function that coordinates detection of different
    generic language pattern types. It delegates to specialized detection functions:
    - _detect_vague_intensifiers() for vague intensifier detection
    - _detect_overused_phrases() for overused phrase detection
    - _detect_stock_phrases() for stock phrase detection
    
    Args:
        text: Text to analyze for generic patterns
        
    Returns:
        List of dictionaries, each representing a detected pattern with keys:
        - 'type': Pattern type (e.g., 'vague_intensifier', 'overused_phrase', 'stock_phrase')
        - 'in_dialogue': Boolean indicating if pattern is in dialogue
        - 'suggestion': Suggested improvement
    """
    if not text:
        return []
    if not isinstance(text, str):
        text = str(text)
    
    text_lower = text.lower()
    patterns = []
    
    # Delegate to specialized detection functions
    patterns.extend(_detect_vague_intensifiers(text_lower))
    patterns.extend(_detect_overused_phrases(text_lower))
    patterns.extend(_detect_stock_phrases(text_lower))
    
    return patterns


# Backward compatibility: Keep private function name as alias if needed
# This allows existing code to continue working while migrating to public API
def _detect_generic_patterns(text: str, text_lower: str) -> List[Dict]:
    """
    Private function for detecting generic patterns.
    
    DEPRECATED: Use detect_generic_patterns_from_text() instead.
    This function is kept for backward compatibility only.
    
    Args:
        text: Original text
        text_lower: Lowercased text (for efficiency)
        
    Returns:
        List of detected pattern dictionaries
    """
    return detect_generic_patterns_from_text(text)


# Pre-compiled regex pattern for cliché detection (module-level for performance)
# Common clichés to detect (sorted by length, longest first for correct matching)
_CLICHE_PATTERNS = [
    "it was a dark and stormy night",
    "time seemed to stand still",
    "little did they know",
    "it was then that",
    "once upon a time",
    "without warning",
    "out of nowhere",
    "in that moment",
    "her heart pounded",
    "his eyes widened"
]

# Pre-compile regex pattern once at module level for better performance
# Use word boundaries to avoid partial matches, case-insensitive
_CLICHE_REGEX_PATTERN: Pattern[str] = re.compile(
    "|".join(r"\b" + re.escape(cliche) + r"\b" for cliche in _CLICHE_PATTERNS),
    re.IGNORECASE
)


def _create_cliche_detail(cliche: str) -> Dict:
    """
    Create a cliché detail dictionary for a detected cliché.
    
    Args:
        cliche: The cliché phrase that was detected
        
    Returns:
        Dict with cliché detail information:
        {
            "phrase": str,
            "in_dialogue": bool,
            "suggestion": str
        }
    """
    return {
        "phrase": cliche,
        "in_dialogue": False,  # Simplified - would need dialogue detection
        "suggestion": f"Replace clichéd phrase '{cliche}' with something more original"
    }


def _find_cliches_in_text(text_lower: str) -> tuple[List[str], List[Dict]]:
    """
    Find clichés in text using pre-compiled regex patterns.
    
    Args:
        text_lower: Lowercased text to search
        
    Returns:
        Tuple of (found_cliches, cliche_details) lists
    """
    found_cliches = []
    cliche_details = []
    matched_cliches = set()  # Use set to avoid duplicates
    
    # Find all matches using the pre-compiled pattern
    matches = _CLICHE_REGEX_PATTERN.finditer(text_lower)
    
    for match in matches:
        matched_text = match.group(0).lower()
        # Find which cliché pattern matched (handle case-insensitive matching)
        for cliche in _CLICHE_PATTERNS:
            if cliche.lower() == matched_text and cliche not in matched_cliches:
                matched_cliches.add(cliche)
                found_cliches.append(cliche)
                cliche_details.append(_create_cliche_detail(cliche))
                break  # Found the matching cliché, move to next match
    
    return found_cliches, cliche_details


def detect_cliches(text: Optional[str] = None) -> Dict:
    """
    Detect clichés in the given text.
    
    Uses pre-compiled regex patterns for efficient detection.
    Delegates actual detection to _find_cliches_in_text().
    
    Args:
        text: Text to check for clichés
        
    Returns:
        Dict with cliché detection results:
        {
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": List[str],
            "cliche_details": List[Dict]
        }
    """
    if not text:
        return _get_default_cliche_results()
    
    # Use pre-compiled regex pattern for efficient matching
    # Only lowercase once for all matches
    text_lower = text.lower()
    found_cliches, cliche_details = _find_cliches_in_text(text_lower)
    
    return {
        "has_cliches": len(found_cliches) > 0,
        "cliche_count": len(found_cliches),
        "found_cliches": found_cliches,
        "cliche_details": cliche_details
    }


def _extract_character_description(character: Optional[Dict]) -> str:
    """
    Extract character description from various input formats.
    
    This function handles different character input formats:
    - Dict with 'description' key
    - Dict without 'description' key (converts to string)
    - String directly
    
    Args:
        character: Character description in various formats
        
    Returns:
        String representation of character description
    """
    if not character:
        return ""
    
    if isinstance(character, dict):
        char_desc = character.get("description", "")
        if not char_desc:
            char_desc = str(character)
        return char_desc
    else:
        return str(character)


def _find_generic_archetypes_in_text(text_lower: str) -> List[str]:
    """
    Find generic archetypes present in the given text.
    
    Args:
        text_lower: Lowercased text to search for archetypes
        
    Returns:
        List of archetype strings found in the text
    """
    generic_elements = []
    for archetype in GENERIC_ARCHETYPES:
        if archetype in text_lower:
            generic_elements.append(archetype)
    return generic_elements


def detect_generic_archetypes(character: Optional[Dict] = None) -> Dict:
    """
    Detect generic archetypes in character description.
    
    This function orchestrates archetype detection by:
    1. Extracting character description from various formats
    2. Searching for generic archetypes in the description
    
    Args:
        character: Character description dict or string
        
    Returns:
        Dict with archetype detection results:
        {
            "has_generic_archetype": bool,
            "generic_elements": List[str]
        }
    """
    if not character:
        return {
            "has_generic_archetype": False,
            "generic_elements": []
        }
    
    # Extract character description (handles different input formats)
    char_desc = _extract_character_description(character)
    char_desc_lower = char_desc.lower()
    
    # Find generic archetypes
    generic_elements = _find_generic_archetypes_in_text(char_desc_lower)
    
    return {
        "has_generic_archetype": len(generic_elements) > 0,
        "generic_elements": generic_elements
    }


def _get_default_cliche_results() -> Dict:
    """
    Get default cliché detection results when no text is provided.
    
    Returns:
        Dict with default cliché detection results
    """
    return {
        "has_cliches": False,
        "cliche_count": 0,
        "found_cliches": [],
        "cliche_details": []
    }


def _get_default_archetype_results() -> Dict:
    """
    Get default archetype detection results when no character is provided.
    
    Returns:
        Dict with default archetype detection results
    """
    return {
        "has_generic_archetype": False,
        "generic_elements": []
    }


def _aggregate_distinctiveness_results(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict],
    distinctiveness_score: float,
    suggestions: List[str]
) -> Dict:
    """
    Aggregate all distinctiveness detection results into a single result dictionary.
    
    This function is responsible solely for combining results from different
    detection functions into a unified response structure.
    
    Args:
        cliche_results: Results from detect_cliches()
        archetype_results: Results from detect_generic_archetypes()
        pattern_results: Results from detect_generic_patterns_from_text()
        distinctiveness_score: Calculated distinctiveness score
        suggestions: Generated suggestions list
        
    Returns:
        Dict containing all distinctiveness check results:
        {
            "distinctiveness_score": float,
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": List[str],
            "cliche_details": List[Dict],
            "has_generic_archetype": bool,
            "generic_elements": List[str],
            "generic_patterns": List[Dict],
            "suggestions": List[str]
        }
    """
    return {
        "distinctiveness_score": distinctiveness_score,
        **cliche_results,
        **archetype_results,
        "generic_patterns": pattern_results,
        "suggestions": suggestions
    }


def calculate_distinctiveness_score(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict]
) -> float:
    """
    Calculate distinctiveness score from detection results.
    
    This function is responsible solely for score calculation logic.
    It takes detection results and computes a single distinctiveness score.
    
    Args:
        cliche_results: Results from detect_cliches()
        archetype_results: Results from detect_generic_archetypes()
        pattern_results: Results from detect_generic_patterns_from_text()
        
    Returns:
        Float between 0.0 and 1.0 representing distinctiveness
    """
    score = 1.0
    
    # Penalize for clichés
    cliche_count = cliche_results.get("cliche_count", 0)
    score -= min(MAX_CLICHE_PENALTY, cliche_count * PER_CLICHE_PENALTY)
    
    # Penalize for generic archetypes
    if archetype_results.get("has_generic_archetype", False):
        score -= ARCHETYPE_PENALTY
    
    # Penalize for generic patterns
    pattern_count = len(pattern_results)
    score -= min(MAX_PATTERN_PENALTY, pattern_count * PER_PATTERN_PENALTY)
    
    return max(0.0, score)  # Ensure score is between 0 and 1


def _validate_idea(idea: Optional[str]) -> tuple[List[str], List[str]]:
    """
    Validate story idea/premise text.
    
    Args:
        idea: Story idea/premise text to validate
        
    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    if not idea or not isinstance(idea, str) or not idea.strip():
        errors.append("Story idea is required and must be non-empty")
    elif len(idea.strip()) < 10:
        warnings.append("Story idea is very short - consider expanding")
    
    return errors, warnings


def _validate_character_dict(character: Dict) -> tuple[List[str], List[str]]:
    """
    Validate character dictionary structure.
    
    Args:
        character: Character dictionary to validate
        
    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    char_desc = character.get("description", "")
    char_name = character.get("name", "")
    
    # Description validation
    if not char_desc:
        warnings.append("Character description is missing")
    elif len(char_desc.strip()) < 5:
        warnings.append("Character description is very short (minimum 5 characters recommended)")
    elif len(char_desc.strip()) > 1000:
        warnings.append("Character description is very long (maximum 1000 characters recommended)")
    
    # Name validation (if provided)
    if char_name and not isinstance(char_name, str):
        errors.append("Character name must be a string if provided")
    elif char_name and len(char_name.strip()) > 100:
        warnings.append("Character name is very long (maximum 100 characters recommended)")
    
    # Validate quirks if present
    quirks = character.get("quirks", [])
    if quirks is not None:
        if not isinstance(quirks, list):
            errors.append("Character quirks must be a list if provided")
        else:
            for i, quirk in enumerate(quirks):
                if not isinstance(quirk, str):
                    errors.append(f"Character quirk at index {i} must be a string")
                elif len(quirk.strip()) > 200:
                    warnings.append(f"Character quirk at index {i} is very long")
    
    # Validate contradictions if present
    contradictions = character.get("contradictions", "")
    if contradictions and not isinstance(contradictions, str):
        errors.append("Character contradictions must be a string if provided")
    elif contradictions and len(contradictions.strip()) > 500:
        warnings.append("Character contradictions field is very long")
    
    return errors, warnings


def _validate_character_string(character: str) -> tuple[List[str], List[str]]:
    """
    Validate character string description.
    
    Args:
        character: Character description string to validate
        
    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    if len(character.strip()) < 5:
        warnings.append("Character description is very short (minimum 5 characters recommended)")
    elif len(character.strip()) > 1000:
        warnings.append("Character description is very long (maximum 1000 characters recommended)")
    
    return errors, warnings


def _validate_character(character: Optional[Dict]) -> tuple[List[str], List[str]]:
    """
    Validate character description (handles dict, string, or None).
    
    Args:
        character: Character description in various formats
        
    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    if character is None:
        return errors, warnings
    
    if isinstance(character, dict):
        char_errors, char_warnings = _validate_character_dict(character)
        errors.extend(char_errors)
        warnings.extend(char_warnings)
    elif isinstance(character, str):
        char_errors, char_warnings = _validate_character_string(character)
        errors.extend(char_errors)
        warnings.extend(char_warnings)
    else:
        errors.append("Character must be a dict or string if provided")
    
    return errors, warnings


def _validate_theme(theme: Optional[str]) -> tuple[List[str], List[str]]:
    """
    Validate story theme.
    
    Args:
        theme: Story theme to validate
        
    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []
    
    if theme is not None:
        if not isinstance(theme, str):
            errors.append("Theme must be a string if provided")
        elif theme.strip() and len(theme.strip()) < 3:
            warnings.append("Theme is very short - consider expanding")
        elif len(theme.strip()) > 500:
            warnings.append("Theme is very long (maximum 500 characters recommended)")
    
    return errors, warnings


def _check_premise_distinctiveness(
    idea: Optional[str],
    character: Optional[Dict]
) -> List[str]:
    """
    Check distinctiveness of premise components and return warnings.
    
    Args:
        idea: Story idea/premise text
        character: Character description
        
    Returns:
        List of distinctiveness-related warning messages
    """
    warnings = []
    
    # Check idea distinctiveness
    if idea:
        idea_check = check_distinctiveness(idea)
        if idea_check.get("has_cliches", False):
            cliches = idea_check.get("found_cliches", [])
            warnings.append(f"Story idea contains clichés: {', '.join(cliches[:3])}")
    
    # Check character distinctiveness
    if character:
        char_check = check_distinctiveness(None, character=character)
        if char_check.get("has_generic_archetype", False):
            generic = char_check.get("generic_elements", [])
            warnings.append(f"Character uses generic archetypes: {', '.join(generic[:3])}")
    
    return warnings


def validate_premise(
    idea: Optional[str] = None,
    character: Optional[Dict] = None,
    theme: Optional[str] = None
) -> Dict:
    """
    Validate a story premise.
    
    This is an orchestrator function that coordinates validation of different
    premise components. It delegates to specialized validation functions:
    - _validate_idea() for idea validation
    - _validate_character() for character validation
    - _validate_theme() for theme validation
    - _check_premise_distinctiveness() for distinctiveness checks
    
    Args:
        idea: Story idea/premise text
        character: Character description dict
        theme: Story theme
        
    Returns:
        Dict with validation results:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []
    
    # Validate each component using specialized functions
    idea_errors, idea_warnings = _validate_idea(idea)
    errors.extend(idea_errors)
    warnings.extend(idea_warnings)
    
    char_errors, char_warnings = _validate_character(character)
    errors.extend(char_errors)
    warnings.extend(char_warnings)
    
    theme_errors, theme_warnings = _validate_theme(theme)
    errors.extend(theme_errors)
    warnings.extend(theme_warnings)
    
    # Check distinctiveness (adds warnings only)
    distinctiveness_warnings = _check_premise_distinctiveness(idea, character)
    warnings.extend(distinctiveness_warnings)
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def check_distinctiveness(text: Optional[str] = None, character: Optional[Dict] = None) -> Dict:
    """
    Check for generic language, clichés, and stock elements with context-aware analysis.
    
    This is a pure orchestrator function that coordinates detection and scoring.
    It delegates all actual work to specialized functions:
    - detect_cliches() for cliché detection
    - detect_generic_archetypes() for archetype detection
    - detect_generic_patterns_from_text() for generic language pattern detection
    - calculate_distinctiveness_score() for score calculation
    - _generate_suggestions() for suggestion generation
    - _aggregate_distinctiveness_results() for result aggregation
    
    Args:
        text: Text to check (can be idea, description, dialogue, etc.)
        character: Character description (optional)
    
    Returns:
        Dict with flags and suggestions:
        {
            "distinctiveness_score": float,
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": List[str],
            "cliche_details": List[Dict],
            "has_generic_archetype": bool,
            "generic_elements": List[str],
            "generic_patterns": List[Dict],
            "suggestions": List[str]
        }
    """
    # Run detection functions (each focused on a single concern)
    cliche_results = detect_cliches(text) if text else _get_default_cliche_results()
    archetype_results = detect_generic_archetypes(character) if character else _get_default_archetype_results()
    pattern_results = detect_generic_patterns_from_text(text) if text else []
    
    # Calculate distinctiveness score (separate scoring concern)
    distinctiveness_score = calculate_distinctiveness_score(
        cliche_results,
        archetype_results,
        pattern_results
    )
    
    # Generate suggestions (separate suggestion generation concern)
    suggestions = _generate_suggestions(cliche_results, archetype_results, pattern_results)
    
    # Aggregate results (separate aggregation concern)
    return _aggregate_distinctiveness_results(
        cliche_results,
        archetype_results,
        pattern_results,
        distinctiveness_score,
        suggestions
    )


def validate_story_voices(story_text: str, character_info: Optional[Dict] = None) -> Dict:
    """
    Validate character voices in story text.
    
    Attempts to analyze character voices using the voice analyzer module.
    If the voice analyzer is unavailable, returns a default result with appropriate logging.
    
    Args:
        story_text: The story text to analyze
        character_info: Optional character information from premise
        
    Returns:
        Dict with voice analysis results:
        {
            "has_dialogue": bool,
            "characters": Dict,
            "voice_differentiation_score": float,
            "consistency_issues": List,
            "suggestions": List[str],
            "analysis": Optional[Dict]
        }
    """
    try:
        from ..voice_analyzer import analyze_character_voices
        analysis = analyze_character_voices(story_text, character_info)
        
        # Extract key metrics from analysis
        has_dialogue = analysis.get('overall', {}).get('total_dialogue_instances', 0) > 0
        characters = analysis.get('characters', {})
        voice_differentiation_score = analysis.get('overall', {}).get('voice_differentiation_score', 0.0)
        suggestions = analysis.get('overall', {}).get('suggestions', [])
        
        # Collect consistency issues
        # Import consistency threshold from voice_analyzer for consistency
        from ..voice_analyzer import CONSISTENCY_THRESHOLD
        
        consistency_issues = []
        for char_name, char_data in characters.items():
            consistency = char_data.get('consistency', {})
            if consistency.get('consistency_score', 1.0) < CONSISTENCY_THRESHOLD:
                consistency_issues.append(
                    f"{char_name}: Low voice consistency (score: {consistency.get('consistency_score', 0):.2f})"
                )
        
        return {
            "has_dialogue": has_dialogue,
            "characters": characters,
            "voice_differentiation_score": voice_differentiation_score,
            "consistency_issues": consistency_issues,
            "suggestions": suggestions,
            "analysis": analysis,
        }
    except ImportError as e:
        logger.warning(
            "Character voice analyzer not available: %s. Voice validation will be skipped.",
            e,
            exc_info=True
        )
        return {
            "has_dialogue": False,
            "characters": {},
            "voice_differentiation_score": 0.0,
            "consistency_issues": [],
            "suggestions": [f"Voice analyzer not available: {e}"],
            "analysis": None,
        }
    except Exception as e:
        logger.error(
            "Error during character voice analysis: %s",
            e,
            exc_info=True
        )
        return {
            "has_dialogue": False,
            "characters": {},
            "voice_differentiation_score": 0.0,
            "consistency_issues": [],
            "suggestions": [f"Error analyzing voices: {str(e)}"],
            "analysis": None,
        }
