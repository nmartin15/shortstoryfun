"""
Distinctiveness and quality validation utilities.

See CONCEPTS.md for definitions of distinctiveness requirements.
"""

import re
from typing import List, Dict, Tuple, Optional

# Common clichéd phrases with variations and patterns
# Format: (base_phrase, [variations], pattern_type)
CLICHE_PATTERNS = [
    ("dark and stormy night", ["dark stormy night", "stormy dark night"], "exact"),
    ("once upon a time", ["once upon", "long ago"], "exact"),
    ("in the nick of time", ["nick of time", "just in time"], "exact"),
    ("all hell broke loose", ["hell broke loose", "all hell"], "exact"),
    ("calm before the storm", ["calm before storm", "quiet before storm"], "exact"),
    ("needle in a haystack", ["needle in haystack", "finding a needle"], "exact"),
    ("tip of the iceberg", ["tip of iceberg", "just the tip"], "exact"),
    ("dead as a doornail", ["dead as doornail", "dead doornail"], "exact"),
    ("raining cats and dogs", ["raining cats", "cats and dogs"], "exact"),
    ("piece of cake", ["easy as pie", "walk in the park"], "exact"),
    ("blessing in disguise", ["blessing disguise"], "exact"),
    ("beat around the bush", ["beating around bush", "around the bush"], "exact"),
    ("break the ice", ["breaking the ice", "ice breaker"], "exact"),
    ("hit the nail on the head", ["nail on head", "hit nail"], "exact"),
    ("let the cat out of the bag", ["cat out of bag", "let cat out"], "exact"),
]

# Generic character archetypes with semantic variations
# Format: (base_archetype, [variations], [related_terms])
ARCHETYPE_PATTERNS = [
    ("chosen one", ["chosen", "prophesied", "destined hero", "special one"], ["prophecy", "destiny", "fated"]),
    ("wise old mentor", ["wise mentor", "old wise man", "elder guide", "sage"], ["guru", "teacher", "master"]),
    ("damsel in distress", ["damsel", "helpless woman", "princess needs saving"], ["rescue", "save her"]),
    ("evil villain", ["evil antagonist", "dark lord", "wicked villain", "bad guy"], ["malicious", "sinister", "cruel"]),
    ("comic relief", ["funny sidekick", "jester", "humor character"], ["jokes", "comedy"]),
    ("mysterious stranger", ["mysterious figure", "unknown person", "stranger appears"], ["mystery", "enigmatic"]),
    ("rebellious teenager", ["rebellious youth", "angry teen", "defiant young"], ["rebellion", "teen angst"]),
    ("perfect hero", ["flawless hero", "perfect protagonist", "ideal hero"], ["perfect", "flawless", "ideal"]),
]

# Generic language patterns (vague descriptors, overused phrases)
GENERIC_PATTERNS = [
    # Vague intensifiers
    (r'\bvery\s+\w+', "vague_intensifier", "Replace 'very [adjective]' with a more specific descriptor"),
    (r'\breally\s+\w+', "vague_intensifier", "Replace 'really [adjective]' with a more specific descriptor"),
    (r'\bquite\s+\w+', "vague_intensifier", "Replace 'quite [adjective]' with a more specific descriptor"),
    # Overused descriptive patterns
    (r'\bdeep\s+(breath|sigh)', "overused_phrase", "Consider a more specific physical description"),
    (r'\bheart\s+(pounded|raced|sank)', "overused_phrase", "Consider a more unique physical reaction"),
    (r'\beyes\s+(widened|narrowed|met)', "overused_phrase", "Consider more specific eye descriptions"),
    # Generic emotional descriptors
    (r'\b(felt|feeling)\s+(sad|happy|angry|scared)', "generic_emotion", "Replace generic emotion with specific physical/behavioral details"),
    # Stock phrases
    (r'\bit\s+was\s+(then|at\s+that\s+moment)\s+that', "stock_phrase", "Consider a more direct narrative approach"),
    (r'\blittle\s+did\s+(he|she|they|i)\s+know', "stock_phrase", "Consider showing rather than telling"),
]

# Common generic word combinations
GENERIC_WORD_PAIRS = [
    ("suddenly", "everything"),
    ("without warning", "all"),
    ("in an instant", "changed"),
    ("out of nowhere", "appeared"),
    ("as if", "by magic"),
]

# Backward compatibility: simple lists for existing code
COMMON_CLICHES = [pattern[0] for pattern in CLICHE_PATTERNS]
GENERIC_ARCHETYPES = [pattern[0] for pattern in ARCHETYPE_PATTERNS]


def _detect_cliche_variations(text_lower: str, base_phrase: str, variations: List[str]) -> Optional[str]:
    """
    Detect cliché using word boundary matching and variations.
    
    Returns the matched phrase if found, None otherwise.
    """
    # Check base phrase with word boundaries
    pattern = r'\b' + re.escape(base_phrase) + r'\b'
    if re.search(pattern, text_lower):
        return base_phrase
    
    # Check variations
    for variation in variations:
        pattern = r'\b' + re.escape(variation) + r'\b'
        if re.search(pattern, text_lower):
            return base_phrase  # Return base phrase for consistency
    
    return None


def _is_in_dialogue(text: str, position: int) -> bool:
    """
    Determine if a position in text is within dialogue.
    Simple heuristic: check for quotes around the position.
    """
    # Count quotes before position
    quotes_before = text[:position].count('"') + text[:position].count("'")
    return quotes_before % 2 == 1


def _detect_archetype_variations(text_lower: str, base_archetype: str, 
                                  variations: List[str], related_terms: List[str]) -> Optional[Dict]:
    """
    Detect archetype using semantic variations and related terms.
    
    Returns dict with archetype info if found, None otherwise.
    """
    # Check base archetype
    pattern = r'\b' + re.escape(base_archetype) + r'\b'
    if re.search(pattern, text_lower):
        return {"archetype": base_archetype, "confidence": "high"}
    
    # Check variations
    for variation in variations:
        pattern = r'\b' + re.escape(variation) + r'\b'
        if re.search(pattern, text_lower):
            return {"archetype": base_archetype, "confidence": "medium", "matched": variation}
    
    # Check related terms (lower confidence, might be false positive)
    related_count = sum(1 for term in related_terms if re.search(r'\b' + re.escape(term) + r'\b', text_lower))
    if related_count >= 2:  # Multiple related terms suggest archetype
        return {"archetype": base_archetype, "confidence": "low", "related_terms": related_count}
    
    return None


def _detect_generic_patterns(text: str, text_lower: str) -> List[Dict]:
    """
    Detect generic language patterns using regex and semantic analysis.
    
    Returns list of detected patterns with context.
    """
    detected = []
    
    # Check regex patterns
    for pattern, pattern_type, suggestion in GENERIC_PATTERNS:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            start, end = match.span()
            context_start = max(0, start - 30)
            context_end = min(len(text), end + 30)
            context = text[context_start:context_end]
            
            # Check if in dialogue (less penalty)
            in_dialogue = _is_in_dialogue(text, start)
            
            detected.append({
                "pattern": match.group(),
                "type": pattern_type,
                "suggestion": suggestion,
                "context": context,
                "in_dialogue": in_dialogue,
                "position": start,
            })
    
    # Check generic word pairs (semantic patterns)
    words = text_lower.split()
    for i in range(len(words) - 1):
        word_pair = (words[i], words[i+1])
        for generic_pair in GENERIC_WORD_PAIRS:
            if word_pair[0] == generic_pair[0] and generic_pair[1] in words[max(0, i-2):i+5]:
                detected.append({
                    "pattern": f"{word_pair[0]} {word_pair[1]}",
                    "type": "generic_word_pair",
                    "suggestion": f"Replace generic phrase '{word_pair[0]} {word_pair[1]}' with more specific language",
                    "context": " ".join(words[max(0, i-2):min(len(words), i+5)]),
                    "in_dialogue": False,  # Simplified for word pairs
                    "position": sum(len(w) + 1 for w in words[:i]),
                })
                break
    
    return detected


def detect_cliches(text: str) -> Dict:
    """
    Detect clichés in the given text with context-aware analysis.
    
    This function focuses solely on cliché detection, including:
    - Word boundary matching for clichés
    - Detection of cliché variations
    - Context-aware detection (dialogue vs narrative)
    
    Args:
        text: Text to check for clichés (can be idea, description, dialogue, etc.)
    
    Returns:
        Dict with cliché detection results:
        {
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": list[str],
            "cliche_details": list[dict]  # Detailed info with context and position
        }
    """
    if not text:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    
    text_lower = text.lower()
    
    # Enhanced cliché detection with variations
    found_cliches = []
    cliche_details = []
    for base_phrase, variations, pattern_type in CLICHE_PATTERNS:
        matched = _detect_cliche_variations(text_lower, base_phrase, variations)
        if matched:
            found_cliches.append(matched)
            # Find position for context
            pattern = r'\b' + re.escape(base_phrase) + r'\b'
            match = re.search(pattern, text_lower)
            if not match:
                # Try variations
                for var in variations:
                    pattern = r'\b' + re.escape(var) + r'\b'
                    match = re.search(pattern, text_lower)
                    if match:
                        break
            
            if match:
                start, end = match.span()
                context_start = max(0, start - 30)
                context_end = min(len(text), end + 30)
                in_dialogue = _is_in_dialogue(text, start)
                
                cliche_details.append({
                    "phrase": matched,
                    "context": text[context_start:context_end],
                    "in_dialogue": in_dialogue,
                    "position": start,
                })
    
    return {
        "has_cliches": len(found_cliches) > 0,
        "cliche_count": len(found_cliches),
        "found_cliches": found_cliches,
        "cliche_details": cliche_details,
    }


def detect_generic_archetypes(character) -> Dict:
    """
    Detect generic archetypes in the given character description.
    
    This function focuses solely on archetype detection, including:
    - Detection of archetype variations
    - Semantic detection using related terms
    
    Args:
        character: Character description (string or dict)
    
    Returns:
        Dict with archetype detection results:
        {
            "has_generic_archetype": bool,
            "generic_elements": list[str],
            "archetype_details": list[dict]  # Detailed info with confidence
        }
    """
    if not character:
        return {
            "has_generic_archetype": False,
            "generic_elements": [],
            "archetype_details": [],
        }
    
    char_text = str(character)
    char_lower = char_text.lower()
    
    # Enhanced archetype detection with semantic variations
    generic_elements = []
    archetype_details = []
    for base_archetype, variations, related_terms in ARCHETYPE_PATTERNS:
        detected = _detect_archetype_variations(char_lower, base_archetype, variations, related_terms)
        if detected:
            generic_elements.append(base_archetype)
            archetype_details.append(detected)
    
    return {
        "has_generic_archetype": len(generic_elements) > 0,
        "generic_elements": generic_elements,
        "archetype_details": archetype_details,
    }


def calculate_distinctiveness_score(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict]
) -> float:
    """
    Calculate distinctiveness score from detection results.
    
    This function focuses solely on score calculation based on:
    - Cliché penalties (weighted by dialogue vs narrative)
    - Archetype penalties
    - Generic pattern penalties (weighted by type)
    
    Args:
        cliche_results: Results from detect_cliches()
        archetype_results: Results from detect_generic_archetypes()
        pattern_results: Results from _detect_generic_patterns()
    
    Returns:
        float: Distinctiveness score (0-1, higher = more distinctive)
    """
    cliche_details = cliche_results.get("cliche_details", [])
    generic_elements = archetype_results.get("generic_elements", [])
    
    # Calculate distinctiveness score with context weighting
    # Clichés in dialogue are less penalized (0.1 vs 0.2)
    cliche_penalty = 0.0
    for detail in cliche_details:
        if detail.get("in_dialogue", False):
            cliche_penalty += 0.1  # Less penalty for dialogue
        else:
            cliche_penalty += 0.2  # Full penalty for narrative
    
    # Archetype penalty
    archetype_penalty = len(generic_elements) * 0.3
    
    # Generic pattern penalty (weighted by type)
    pattern_penalty = 0.0
    for pattern in pattern_results:
        if pattern.get("in_dialogue", False):
            pattern_penalty += 0.05  # Minimal penalty for dialogue
        else:
            pattern_type = pattern.get("type", "")
            if pattern_type == "vague_intensifier":
                pattern_penalty += 0.03
            elif pattern_type == "overused_phrase":
                pattern_penalty += 0.05
            elif pattern_type == "generic_emotion":
                pattern_penalty += 0.04
            elif pattern_type == "stock_phrase":
                pattern_penalty += 0.08
            else:
                pattern_penalty += 0.04
    
    distinctiveness_score = max(0.0, 1.0 - cliche_penalty - archetype_penalty - pattern_penalty)
    return distinctiveness_score


def _generate_suggestions(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict]
) -> List[str]:
    """
    Generate context-aware suggestions from detection results.
    
    Args:
        cliche_results: Results from detect_cliches()
        archetype_results: Results from detect_generic_archetypes()
        pattern_results: Results from _detect_generic_patterns()
    
    Returns:
        list[str]: List of suggestion messages
    """
    suggestions = []
    
    found_cliches = cliche_results.get("found_cliches", [])
    cliche_details = cliche_results.get("cliche_details", [])
    generic_elements = archetype_results.get("generic_elements", [])
    
    if found_cliches:
        dialogue_cliches = sum(1 for d in cliche_details if d.get("in_dialogue", False))
        narrative_cliches = len(found_cliches) - dialogue_cliches
        
        if narrative_cliches > 0:
            suggestions.append(
                f"Found {narrative_cliches} clichéd phrase(s) in narrative. "
                "Replace with specific, vivid language."
            )
        if dialogue_cliches > 0:
            suggestions.append(
                f"Found {dialogue_cliches} clichéd phrase(s) in dialogue. "
                "Consider if this serves character voice or should be replaced."
            )
    
    if generic_elements:
        suggestions.append(
            f"Character shows generic archetype traits ({', '.join(generic_elements)}). "
            "Add unique quirks, contradictions, or specific details."
        )
    
    if pattern_results:
        # Group by type for better suggestions
        pattern_types = {}
        for pattern in pattern_results:
            ptype = pattern.get("type", "")
            if ptype not in pattern_types:
                pattern_types[ptype] = []
            pattern_types[ptype].append(pattern)
        
        for ptype, patterns in pattern_types.items():
            narrative_patterns = [p for p in patterns if not p.get("in_dialogue", False)]
            if narrative_patterns:
                suggestions.append(
                    f"Found {len(narrative_patterns)} instance(s) of {ptype.replace('_', ' ')}. "
                    f"{patterns[0].get('suggestion', '')}"
                )
    
    return suggestions


def check_distinctiveness(text, character=None, idea=None):
    """
    Check for generic language, clichés, and stock elements with context-aware analysis.
    
    This is an orchestrator function that coordinates detection and scoring.
    It delegates to specialized functions:
    - detect_cliches() for cliché detection
    - detect_generic_archetypes() for archetype detection
    - _detect_generic_patterns() for generic language pattern detection
    - calculate_distinctiveness_score() for score calculation
    
    Enhanced with:
    - Word boundary matching for clichés
    - Detection of cliché variations
    - Context-aware detection (dialogue vs narrative)
    - Generic language pattern detection
    - Semantic archetype detection
    
    Args:
        text: Text to check (can be idea, description, dialogue, etc.)
        character: Character description (optional)
        idea: Story idea (optional, currently unused but kept for API compatibility)
    
    Returns:
        Dict with flags and suggestions:
        {
            "has_cliches": bool,
            "cliche_count": int,
            "found_cliches": list,
            "cliche_details": list[dict],
            "has_generic_archetype": bool,
            "generic_elements": list,
            "archetype_details": list[dict],
            "generic_patterns": list[dict],
            "generic_pattern_count": int,
            "distinctiveness_score": float,  # 0-1, higher = more distinctive
            "suggestions": list[str]
        }
    """
    # Normalize text input
    if not text:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    
    text_lower = text.lower()
    
    # Delegate to specialized detection functions
    cliche_results = detect_cliches(text)
    archetype_results = detect_generic_archetypes(character)
    pattern_results = _detect_generic_patterns(text, text_lower)
    
    # Calculate distinctiveness score from detection results
    distinctiveness_score = calculate_distinctiveness_score(
        cliche_results,
        archetype_results,
        pattern_results
    )
    
    # Generate suggestions from detection results
    suggestions = _generate_suggestions(
        cliche_results,
        archetype_results,
        pattern_results
    )
    
    # Combine all results into unified response
    return {
        "has_cliches": cliche_results["has_cliches"],
        "cliche_count": cliche_results["cliche_count"],
        "found_cliches": cliche_results["found_cliches"],
        "cliche_details": cliche_results["cliche_details"],
        "has_generic_archetype": archetype_results["has_generic_archetype"],
        "generic_elements": archetype_results["generic_elements"],
        "archetype_details": archetype_results["archetype_details"],
        "generic_patterns": pattern_results,
        "generic_pattern_count": len(pattern_results),
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
    # Character and theme are optional - only add warnings, not errors
    if not completeness["has_character"]:
        warnings.append("Character description is recommended for richer stories")
    if not completeness["has_theme"]:
        warnings.append("Theme is recommended to add depth to the story")
    
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


def validate_story_voices(story_text: str, character_info=None):
    """
    Validate character voice consistency and distinctiveness in story text.
    
    Uses the Character Voice Analyzer to check:
    - Voice consistency across dialogue instances
    - Distinctiveness between characters
    - Speech pattern quality
    
    Args:
        story_text: Full story text to analyze
        character_info: Optional character info from premise
        
    Returns:
        Dict with voice validation results:
        {
            "has_dialogue": bool,
            "characters": dict,  # Character voice analyses
            "voice_differentiation_score": float,  # 0-1
            "consistency_issues": list[str],
            "suggestions": list[str],
        }
    """
    try:
        from ..voice_analyzer import analyze_character_voices
        
        analysis = analyze_character_voices(story_text, character_info)
        
        # Extract consistency issues
        consistency_issues = []
        for char_name, char_data in analysis.get("characters", {}).items():
            consistency = char_data.get("consistency", {})
            if consistency.get("consistency_score", 1.0) < 0.7:
                consistency_issues.extend(consistency.get("issues", []))
        
        return {
            "has_dialogue": analysis["overall"]["total_dialogue_instances"] > 0,
            "characters": analysis.get("characters", {}),
            "voice_differentiation_score": analysis["overall"]["voice_differentiation_score"],
            "consistency_issues": consistency_issues,
            "suggestions": analysis["overall"]["suggestions"],
            "analysis": analysis,  # Full analysis for detailed inspection
        }
    except ImportError:
        # Voice analyzer not available
        return {
            "has_dialogue": False,
            "characters": {},
            "voice_differentiation_score": 0.0,
            "consistency_issues": [],
            "suggestions": ["Voice analyzer not available"],
            "analysis": None,
        }
    except Exception as e:
        # Error during analysis
        return {
            "has_dialogue": False,
            "characters": {},
            "voice_differentiation_score": 0.0,
            "consistency_issues": [],
            "suggestions": [f"Error analyzing voices: {str(e)}"],
            "analysis": None,
        }

