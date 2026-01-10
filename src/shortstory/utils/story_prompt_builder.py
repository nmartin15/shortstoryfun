"""
Story prompt builder for LLM story generation.

This module builds prompts for story generation and revision.
It follows best practices by using parameter objects and extracting
magic strings to constants.

Key Components:
- Enums: Pace, Tone, GenreKeyword, SensoryFocus - Type-safe constants
- TypedDict: GenreConstraints - Structured type definition for constraints
- Dataclasses: StoryParams, RevisionParams - Parameter objects for prompts
- Functions: Prompt builders and constraint normalizers

Constraints Dictionary Structure:
The GenreConstraints TypedDict defines the structure for genre constraints:
{
    "tone": str,                    # Story tone (e.g., "dark", "warm", "balanced")
    "pace": str,                    # Story pacing (e.g., "fast", "moderate", "deliberate")
    "pov_preference": str,          # POV preference (e.g., "first_or_limited", "flexible")
    "sensory_focus": List[str],     # Sensory focus areas (e.g., ["sound", "touch"])
    "style": str,                   # Writing style (e.g., "literary", "commercial")
    "genre_keywords": List[str]     # Genre-specific keywords for constraint checking
}

All fields are optional to support flexible constraint definitions.
Use normalize_constraints() to convert Dict[str, Any] to GenreConstraints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, TypedDict
from enum import Enum

from .llm_constants import (
    STORY_MIN_WORDS,
    STORY_MAX_WORDS,
    TARGET_WORD_COUNT_RATIO,
    OPENING_MIN_WORDS,
    OPENING_MAX_WORDS,
    RISING_ACTION_MIN_WORDS,
    RISING_ACTION_MAX_WORDS,
    MIDPOINT_SHIFT_MIN_WORDS,
    MIDPOINT_SHIFT_MAX_WORDS,
    CLIMAX_MIN_WORDS,
    CLIMAX_MAX_WORDS,
    RESOLUTION_MIN_WORDS,
    RESOLUTION_MAX_WORDS,
)


class Pace(str, Enum):
    """Story pacing options."""
    FAST = "fast"
    MODERATE = "moderate"
    DELIBERATE = "deliberate"
    COMPRESSED = "compressed"


class Tone(str, Enum):
    """Story tone options."""
    DARK = "dark"
    WARM = "warm"
    GRITTY = "gritty"
    SUSPENSEFUL = "suspenseful"
    LIGHT = "light"
    BALANCED = "balanced"
    URGENT = "urgent"


class GenreKeyword(str, Enum):
    """Genre keywords for constraint checking."""
    HORROR = "horror"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    THRILLER = "thriller"
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"


class SensoryFocus(str, Enum):
    """Sensory focus options for genre constraints."""
    WORLD_DETAIL = "world_detail"
    WORLD_BUILDING = "world_building"
    CONCEPT = "concept"
    TECHNOLOGY = "technology"
    SOUND = "sound"
    TOUCH = "touch"
    ATMOSPHERE = "atmosphere"
    SIGHT = "sight"
    EMOTION = "emotion"
    INTIMACY = "intimacy"
    ACTION = "action"
    TENSION = "tension"
    URGENCY = "urgency"


class GenreConstraints(TypedDict, total=False):
    """
    Type definition for genre constraints dictionary.
    
    This TypedDict provides a clear structure for genre constraints used
    in prompt generation. All fields are optional to support flexible
    constraint definitions across different genres.
    
    Attributes:
        tone: Story tone (should match Tone enum values)
        pace: Story pacing (should match Pace enum values)
        pov_preference: Point of view preference (e.g., "first_or_limited", "flexible")
        sensory_focus: List of sensory focus areas (e.g., ["sound", "touch", "atmosphere"])
        style: Writing style preference (e.g., "literary", "commercial")
        genre_keywords: Optional list of genre-specific keywords for constraint checking
    """
    tone: str
    pace: str
    pov_preference: str
    sensory_focus: List[str]
    style: str
    genre_keywords: List[str]


@dataclass
class StoryParams:
    """Parameters for building story generation prompts."""
    idea: str
    char_desc: str
    char_name: str
    char_quirks: List[str]
    char_contradictions: str
    theme: str
    beginning_label: str
    middle_label: str
    end_label: str
    pov: str
    tone: str
    pace: str
    constraints: GenreConstraints
    max_words: int


@dataclass
class RevisionParams:
    """Parameters for building revision prompts."""
    text: str
    revision_notes: List[str]
    current_words: int
    max_words: int


def build_story_system_prompt() -> str:
    """
    Build the system prompt for story generation.
    
    Returns:
        System prompt string for story generation
    """
    return f"""You are an expert short story writer specializing in distinctive, memorable narratives.

Your task is to generate a complete short story that:
1. Tells a compelling, original story with a single sharp core idea
2. Features distinctive characters with unique voices and contradictions
3. Uses vivid, specific language that avoids clichés and generic phrases
4. Maintains consistent narrative voice throughout
5. Follows a clear structure: Opening, Rising Action, Midpoint Shift, Climax, Resolution

CRITICAL WORD COUNT REQUIREMENT - THIS IS MANDATORY:
- The story MUST be at least {STORY_MIN_WORDS:,} words (minimum requirement)
- The story should be between {STORY_MIN_WORDS:,} and {STORY_MAX_WORDS:,} words
- DO NOT STOP WRITING until you have reached at least {STORY_MIN_WORDS:,} words
- Opening section: {OPENING_MIN_WORDS}-{OPENING_MAX_WORDS} words
- Rising Action: {RISING_ACTION_MIN_WORDS}-{RISING_ACTION_MAX_WORDS} words
- Midpoint Shift: {MIDPOINT_SHIFT_MIN_WORDS}-{MIDPOINT_SHIFT_MAX_WORDS} words
- Climax: {CLIMAX_MIN_WORDS}-{CLIMAX_MAX_WORDS} words
- Resolution: {RESOLUTION_MIN_WORDS}-{RESOLUTION_MAX_WORDS} words
- If your story is shorter than {STORY_MIN_WORDS:,} words, you MUST continue writing until it reaches this minimum

WRITING QUALITY REQUIREMENTS:
- Use specific, concrete details instead of vague descriptions
- Show character emotions through actions and dialogue, not just telling
- Create memorable moments that stand out
- Avoid generic plot beats and predictable story structures
- Develop distinctive narrative voice that matches the story's tone

Provide ONLY the story text, without any metadata or headers."""


def build_story_user_prompt(params: StoryParams) -> Tuple[str, int, int, int]:
    """
    Build the user prompt for story generation.
    
    Args:
        params: Story parameters dataclass
        
    Returns:
        Tuple of (prompt, min_words, max_words, target_words)
    """
    prompt_parts = []
    
    # Story idea
    prompt_parts.append(f"**Story Idea (Single Sharp Core):** {params.idea}\n")
    
    # Character details
    prompt_parts.append(f"**Character:**")
    prompt_parts.append(f"- Name: {params.char_name}")
    prompt_parts.append(f"- Description: {params.char_desc}")
    if params.char_quirks:
        prompt_parts.append(f"- Quirks: {', '.join(params.char_quirks)}")
    if params.char_contradictions:
        prompt_parts.append(f"- Contradictions: {params.char_contradictions}")
    prompt_parts.append("")
    
    # Theme
    if params.theme:
        prompt_parts.append(f"**Theme:** {params.theme}\n")
    
    # Structure
    prompt_parts.append(f"**Story Structure:**")
    prompt_parts.append(f"- Beginning: {params.beginning_label}")
    prompt_parts.append(f"- Middle: {params.middle_label}")
    prompt_parts.append(f"- End: {params.end_label}")
    prompt_parts.append("")
    
    # Voice and style
    prompt_parts.append(f"**Narrative Voice:**")
    prompt_parts.append(f"- POV: {params.pov}")
    prompt_parts.append(f"- Tone: {params.tone}")
    prompt_parts.append(f"- Pace: {params.pace}")
    prompt_parts.append("")
    
    # Genre-specific guidance
    if params.constraints:
        guidance = _build_genre_adapted_structure_guidance(
            pace=params.pace,
            tone=params.tone,
            constraints=params.constraints
        )
        if guidance:
            prompt_parts.append("**Genre-Specific Guidance:**")
            # Format guidance keys into readable labels
            for key, value in guidance.items():
                # Convert snake_case to Title Case with spaces
                label = key.replace('_', ' ').title()
                prompt_parts.append(f"- {label}: {value}")
            prompt_parts.append("")
    
    # Word count requirements - make this VERY explicit
    target_words = int(params.max_words * TARGET_WORD_COUNT_RATIO)
    prompt_parts.append(f"**CRITICAL WORD COUNT REQUIREMENT:**")
    prompt_parts.append(f"- MINIMUM: The story MUST be at least {STORY_MIN_WORDS:,} words (this is mandatory, not optional)")
    prompt_parts.append(f"- TARGET: Aim for {target_words:,} words")
    prompt_parts.append(f"- MAXIMUM: Do not exceed {STORY_MAX_WORDS:,} words")
    prompt_parts.append(f"- DO NOT STOP WRITING until you have written at least {STORY_MIN_WORDS:,} words")
    prompt_parts.append(f"- If you find yourself ending the story before {STORY_MIN_WORDS:,} words, you MUST continue with more scenes, dialogue, character development, or plot resolution")
    
    prompt = "\n".join(prompt_parts)
    
    return prompt, STORY_MIN_WORDS, STORY_MAX_WORDS, target_words


def _normalize_enum_value(value: Any, enum_class: type) -> str:
    """
    Normalize a value to its string representation.
    
    Handles both enum instances and string values.
    
    Args:
        value: Value to normalize (enum or string)
        enum_class: Enum class for type checking
        
    Returns:
        String representation of the value
    """
    if isinstance(value, enum_class):
        return value.value
    if isinstance(value, str):
        return value
    return str(value)


def normalize_constraints(constraints: Dict[str, Any]) -> GenreConstraints:
    """
    Normalize and validate a constraints dictionary to GenreConstraints format.
    
    This function ensures that constraints dictionaries from various sources
    (genre configs, API requests, etc.) are properly formatted and typed.
    It handles type conversions and provides defaults for missing fields.
    
    Args:
        constraints: Raw constraints dictionary (may be Dict[str, Any])
        
    Returns:
        Normalized GenreConstraints dictionary
        
    Examples:
        >>> constraints = {"tone": "dark", "pace": "fast", "sensory_focus": ["sound"]}
        >>> normalized = normalize_constraints(constraints)
        >>> assert normalized["tone"] == "dark"
    """
    normalized: GenreConstraints = {}
    
    # Normalize tone
    if "tone" in constraints:
        tone = constraints["tone"]
        normalized["tone"] = str(tone) if tone is not None else ""
    
    # Normalize pace
    if "pace" in constraints:
        pace = constraints["pace"]
        normalized["pace"] = str(pace) if pace is not None else ""
    
    # Normalize pov_preference
    if "pov_preference" in constraints:
        pov = constraints["pov_preference"]
        normalized["pov_preference"] = str(pov) if pov is not None else ""
    
    # Normalize sensory_focus (ensure it's a list)
    if "sensory_focus" in constraints:
        sensory = constraints["sensory_focus"]
        if isinstance(sensory, list):
            normalized["sensory_focus"] = [str(s) for s in sensory if s]
        elif sensory is not None:
            normalized["sensory_focus"] = [str(sensory)]
        else:
            normalized["sensory_focus"] = []
    
    # Normalize style
    if "style" in constraints:
        style = constraints["style"]
        normalized["style"] = str(style) if style is not None else ""
    
    # Normalize genre_keywords (ensure it's a list)
    if "genre_keywords" in constraints:
        keywords = constraints["genre_keywords"]
        if isinstance(keywords, list):
            normalized["genre_keywords"] = [str(k) for k in keywords if k]
        elif keywords is not None:
            normalized["genre_keywords"] = [str(keywords)]
        else:
            normalized["genre_keywords"] = []
    
    return normalized


def _build_genre_adapted_structure_guidance(
    pace: str,
    tone: str,
    constraints: GenreConstraints
) -> Dict[str, str]:
    """
    Build genre-adapted structure guidance from constraints.
    
    This function extracts relevant guidance from genre constraints and formats
    it for inclusion in story generation prompts. It combines pace, tone, and
    genre-specific constraints to provide structured guidance.
    
    Args:
        pace: Story pacing (Pace enum value or string)
        tone: Story tone (Tone enum value or string)
        constraints: Genre constraints dictionary (GenreConstraints TypedDict)
        
    Returns:
        Dictionary of formatted guidance messages with keys like:
        - "rising_action_focus": Guidance for rising action pacing
        - "sensory_details": Guidance for sensory focus areas
    """
    guidance: Dict[str, str] = {}
    
    # Normalize pace and tone to strings for comparison
    pace_str = _normalize_enum_value(pace, Pace)
    tone_str = _normalize_enum_value(tone, Tone)
    
    # Pace-based guidance (only set if not overridden by tone)
    if pace_str == Pace.FAST.value:
        guidance["rising_action_focus"] = "Build momentum quickly, escalate tension rapidly"
    elif pace_str == Pace.DELIBERATE.value:
        guidance["rising_action_focus"] = "Develop tension gradually, allow moments to breathe"
    elif pace_str == Pace.COMPRESSED.value:
        guidance["rising_action_focus"] = "Maintain tight pacing, maximize impact per word"
    
    # Tone-based guidance (can override pace guidance)
    if (tone_str == Tone.DARK.value or 
        _has_genre_keyword(constraints, GenreKeyword.HORROR.value)):
        guidance["rising_action_focus"] = "Build dread and tension, escalate fear"
    elif tone_str == Tone.WARM.value:
        guidance["rising_action_focus"] = "Develop emotional connections, build warmth"
    elif tone_str == Tone.SUSPENSEFUL.value:
        guidance["rising_action_focus"] = "Create uncertainty, maintain tension"
    elif tone_str == Tone.URGENT.value:
        guidance["rising_action_focus"] = "Maintain high energy, escalate stakes rapidly"
    elif tone_str == Tone.GRITTY.value:
        guidance["rising_action_focus"] = "Build raw intensity, escalate conflict"
    
    # Genre-specific constraints: sensory focus
    sensory_focus = constraints.get("sensory_focus", [])
    if sensory_focus and isinstance(sensory_focus, list):
        # Format sensory focus list into readable guidance
        formatted_focus = ", ".join(str(s) for s in sensory_focus if s)
        if formatted_focus:
            guidance["sensory_details"] = f"Emphasize: {formatted_focus}"
    
    # Genre-specific constraints: style preference
    style = constraints.get("style")
    if style:
        guidance["writing_style"] = f"Adopt a {style} writing style"
    
    return guidance


def _has_genre_keyword(constraints: GenreConstraints, keyword: str) -> bool:
    """
    Check if constraints contain a genre keyword.
    
    This function searches for genre keywords in the constraints dictionary,
    checking both the explicit genre_keywords list and performing a fallback
    string search for backward compatibility.
    
    Args:
        constraints: Genre constraints dictionary (GenreConstraints TypedDict)
        keyword: Keyword to search for (case-insensitive)
        
    Returns:
        True if keyword found in constraints, False otherwise
    """
    # Check explicit genre_keywords list first
    genre_keywords = constraints.get("genre_keywords", [])
    if isinstance(genre_keywords, list) and genre_keywords:
        return keyword.lower() in [str(k).lower() for k in genre_keywords]
    
    # Fallback: check if keyword appears in constraint values (for backward compatibility)
    # This handles cases where genre info might be embedded in other fields
    keyword_lower = keyword.lower()
    for value in constraints.values():
        if isinstance(value, str) and keyword_lower in value.lower():
            return True
        elif isinstance(value, list):
            if any(keyword_lower in str(v).lower() for v in value):
                return True
    
    return False


def build_revision_system_prompt() -> str:
    """
    Build the system prompt for story revision.
    
    Returns:
        System prompt string for story revision
    """
    return """You are an expert story editor specializing in refining short stories.

Your task is to revise a story to:
1. Improve clarity, flow, and impact
2. Enhance distinctive voice and memorable moments
3. Remove clichés and generic language
4. Strengthen character development and dialogue
5. Ensure the story meets word count requirements

CRITICAL: You must provide the COMPLETE revised story, not just changes or suggestions.
The output must be a full, polished narrative ready for publication."""


def _get_word_count_messages(
    current_words: int,
    story_min_words: int,
    story_max_words: int,
    target_words: int,
) -> Dict[str, str]:
    """
    Get word count state messages for revision prompts.
    
    Args:
        current_words: Current word count
        story_min_words: Minimum required words
        story_max_words: Maximum allowed words
        target_words: Target word count
        
    Returns:
        Dictionary with length_instruction, requirements_section, and final_instruction
    """
    messages = {
        "length_instruction": "",
        "requirements_section": "",
        "final_instruction": "",
    }
    
    if current_words < story_min_words:
        messages["length_instruction"] = (
            f"**CRITICAL:** The story is currently only {current_words:,} words. "
            f"It must be expanded to at least {story_min_words:,} words to meet "
            f"professional short story length requirements."
        )
        messages["requirements_section"] = (
            f"5. LENGTH: Expand the story from {current_words:,} words to at least "
            f"{story_min_words:,} words. Add depth to character development, "
            f"expand key scenes, and enrich sensory details while maintaining "
            f"the story's core narrative and distinctive voice."
        )
        messages["final_instruction"] = (
            f"Provide the COMPLETE, EXPANDED revised story. The story must be "
            f"expanded from {current_words:,} words to at least {story_min_words:,} words. "
            f"Maintain the original narrative structure and distinctive voice while "
            f"adding depth and detail."
        )
    elif current_words > story_max_words:
        messages["length_instruction"] = (
            f"**CRITICAL:** The story is currently {current_words:,} words. "
            f"It must be reduced to {story_max_words:,} words or less to meet "
            f"the maximum length requirement."
        )
        messages["requirements_section"] = (
            f"5. LENGTH: Reduce the story from {current_words:,} words to "
            f"{story_max_words:,} words or less. Tighten prose, remove redundancy, "
            f"and condense scenes while preserving the story's core narrative, "
            f"distinctive voice, and most memorable moments."
        )
        messages["final_instruction"] = (
            f"Provide the COMPLETE revised story. The story must be reduced from "
            f"{current_words:,} words to {story_max_words:,} words or less. "
            f"Maintain the original narrative structure and distinctive voice while "
            f"tightening the prose."
        )
    else:
        messages["length_instruction"] = (
            f"**CRITICAL:** The revised story must be approximately {current_words:,} words. "
            f"Maintain the current length while improving quality."
        )
        messages["requirements_section"] = (
            f"5. LENGTH: Keep approximately the same length as the original "
            f"({current_words:,} words). Focus on improving quality rather than "
            f"changing length."
        )
        messages["final_instruction"] = (
            f"Provide the COMPLETE revised story. Maintain similar length "
            f"({current_words:,} words) while improving clarity, voice, and impact."
        )
    
    return messages


def build_revision_user_prompt(
    text: str,
    revision_notes: List[str],
    current_words: int,
    max_words: int,
) -> Tuple[str, int, int, int]:
    """
    Build the user prompt for story revision.
    
    Args:
        text: Current story text
        revision_notes: List of revision notes/instructions
        current_words: Current word count
        max_words: Maximum allowed words
        
    Returns:
        Tuple of (prompt, min_words, max_words, target_words)
    """
    prompt_parts = []
    
    # Current story
    prompt_parts.append("**Current Story:**")
    prompt_parts.append(text)
    prompt_parts.append("")
    
    # Revision notes
    if revision_notes:
        prompt_parts.append("**Revision Instructions:**")
        for i, note in enumerate(revision_notes, 1):
            prompt_parts.append(f"{i}. {note}")
        prompt_parts.append("")
    
    # Word count messages
    story_min_words = STORY_MIN_WORDS
    story_max_words = min(max_words, STORY_MAX_WORDS)
    target_words = int(story_max_words * TARGET_WORD_COUNT_RATIO)
    
    messages = _get_word_count_messages(
        current_words=current_words,
        story_min_words=story_min_words,
        story_max_words=story_max_words,
        target_words=target_words,
    )
    
    prompt_parts.append(messages["length_instruction"])
    prompt_parts.append("")
    prompt_parts.append("**Revision Requirements:**")
    prompt_parts.append("1. Improve clarity and flow")
    prompt_parts.append("2. Enhance distinctive voice")
    prompt_parts.append("3. Remove clichés and generic language")
    prompt_parts.append("4. Strengthen character development")
    prompt_parts.append(messages["requirements_section"])
    prompt_parts.append("")
    prompt_parts.append(messages["final_instruction"])
    
    prompt = "\n".join(prompt_parts)
    
    return prompt, story_min_words, story_max_words, target_words
