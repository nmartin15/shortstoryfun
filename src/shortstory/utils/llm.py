"""
LLM client for Google Gemini API.

This module provides a clean interface for generating prose using Google's Gemini API.

See CONCEPTS.md for distinctiveness and voice requirements.
"""

import os
import re
from typing import Dict, List, Optional, Any

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Allowed model names for security validation
ALLOWED_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash-exp",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.0-pro",
]
DEFAULT_MODEL = "gemini-2.5-flash"

# Context window sizes for different Gemini models (in tokens)
# These are approximate - actual limits may vary
MODEL_CONTEXT_WINDOWS = {
    "gemini-2.5-flash": 32000,
    "gemini-2.0-flash-exp": 32000,
    "gemini-1.5-pro": 32000,
    "gemini-1.5-flash": 32000,
    "gemini-1.0-pro": 32000,
}

# Default context window if model not found
DEFAULT_CONTEXT_WINDOW = 32000


def _estimate_tokens(text: str, model_name: str = DEFAULT_MODEL) -> int:
    """
    Estimate token count for a text string using tiktoken for accurate counting.
    
    Falls back to character-based estimation if tiktoken is not available.
    
    Args:
        text: Text to estimate tokens for
        model_name: Model name (used to select appropriate encoding)
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Use tiktoken for accurate token counting if available
    if TIKTOKEN_AVAILABLE:
        try:
            # Try to get encoding for the model
            # For Gemini models, we'll use cl100k_base as a reasonable approximation
            # since Gemini doesn't have a specific tiktoken encoding
            try:
                # Try common encodings that work well for English text
                encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding, good approximation
            except KeyError:
                # Fallback to p50k_base if cl100k_base is not available
                encoding = tiktoken.get_encoding("p50k_base")
            
            # Count tokens accurately
            token_count = len(encoding.encode(text))
            
            # Add small buffer for special tokens, formatting, etc.
            return int(token_count * 1.05) + 10
        except Exception as e:
            # If tiktoken fails, fall back to character-based estimation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"tiktoken token counting failed, falling back to estimation: {e}")
    
    # Fallback: Character-based estimation (less accurate but better than word-based)
    # This is used if tiktoken is not available or fails
    chars_no_spaces = len(text.replace(' ', ''))
    # Rough estimate: 1 token ≈ 4 characters (accounts for punctuation, etc.)
    char_based_estimate = chars_no_spaces / 4
    
    # Word-based estimate: 1.4 tokens per word (average for English)
    words = len(text.split())
    word_based_estimate = words * 1.4
    
    # Use the higher estimate to be safe (avoid truncation)
    estimated_tokens = max(char_based_estimate, word_based_estimate)
    
    # Add small buffer for special tokens, formatting, etc.
    return int(estimated_tokens * 1.1) + 10


def _calculate_max_output_tokens(
    prompt: str,
    system_prompt: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    target_word_count: Optional[int] = None
) -> int:
    """
    Calculate maximum output tokens based on prompt size and target word count.
    
    Args:
        prompt: Main prompt text
        system_prompt: System prompt text (optional)
        model_name: Model name to get context window
        target_word_count: Target word count for output (optional)
        
    Returns:
        Maximum tokens to allocate for output
    """
    # Get context window for model
    normalized_model = model_name.replace("models/", "")
    context_window = MODEL_CONTEXT_WINDOWS.get(normalized_model, DEFAULT_CONTEXT_WINDOW)
    
    # Estimate prompt tokens (pass model_name for accurate counting)
    prompt_tokens = _estimate_tokens(prompt, model_name=model_name)
    if system_prompt:
        prompt_tokens += _estimate_tokens(system_prompt, model_name=model_name)
    
    # Reserve tokens for response overhead (formatting, etc.)
    response_overhead = 100
    
    # Calculate available tokens
    available_tokens = context_window - prompt_tokens - response_overhead
    
    # If target word count is specified, calculate tokens needed for that
    if target_word_count:
        # Estimate tokens needed for target word count
        # Create a sample text with the target word count to get accurate token estimate
        # Use average English word length (~4.7 chars) + space = ~5.7 chars per word
        sample_text = "word " * target_word_count
        target_tokens = _estimate_tokens(sample_text, model_name=model_name)
        
        # Add 20% buffer to ensure we don't truncate
        target_tokens = int(target_tokens * 1.2)
        
        # Use the minimum of available tokens and target tokens
        max_tokens = min(available_tokens, target_tokens)
    else:
        # Use all available tokens (with safety margin)
        max_tokens = int(available_tokens * 0.9)
    
    # FOR FULL-LENGTH SHORT STORIES: Request maximum tokens possible
    # Gemini models support up to 8192 max_output_tokens
    # For full-length short stories (2000-7500 words), we need maximum tokens
    if target_word_count and target_word_count >= 2000:
        # For full-length stories, request MAXIMUM tokens (8192)
        # This ensures the model has enough space to complete the story
        min_required_tokens = 8192  # MAXIMUM for Gemini
    else:
        # For shorter stories, calculate based on word count
        min_required_tokens = int(target_word_count * 1.5) if target_word_count else 4000
        min_required_tokens = min(min_required_tokens, 8192)
    
    # Use the maximum of calculated tokens and minimum required
    # PRIORITIZE full-length stories by requesting maximum tokens
    final_tokens = max(min_required_tokens, max_tokens)
    
    # Cap at Gemini's max_output_tokens limit (8192) and available tokens
    # But prioritize getting close to 8192 for full-length stories
    final_tokens = min(final_tokens, 8192, available_tokens)
    
    # For full-length stories, ensure we're requesting at least 6000 tokens
    # This gives enough room for 3000-4000 word stories
    if target_word_count and target_word_count >= 2000:
        final_tokens = max(6000, final_tokens)
        final_tokens = min(final_tokens, 8192, available_tokens)
    
    # Log for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Token allocation: prompt={prompt_tokens}, available={available_tokens}, "
        f"target_words={target_word_count}, final_max_tokens={final_tokens}"
    )
    
    return final_tokens


def _validate_model_name(model_name: str) -> str:
    """
    Validate that the model name is in the allowed list.
    
    Args:
        model_name: The model name to validate
        
    Returns:
        The validated model name (with 'models/' prefix if needed)
        
    Raises:
        ValueError: If the model name is not in the allowed list
    """
    # Normalize model name (remove 'models/' prefix for comparison)
    normalized = model_name.replace("models/", "")
    
    # Check if normalized name is in allowed list
    allowed_normalized = [m.replace("models/", "") for m in ALLOWED_MODELS]
    if normalized not in allowed_normalized:
        raise ValueError(
            f"Model name '{model_name}' is not allowed. "
            f"Choose from: {', '.join(set(allowed_normalized))}"
        )
    
    # Return with 'models/' prefix if original had it, otherwise return as-is
    if model_name.startswith("models/"):
        return model_name
    return normalized


class LLMClient:
    """
    Client for Google Gemini API.
    
    Requires GOOGLE_API_KEY environment variable to be set.
    """
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM client.
        
        Args:
            model_name: Name of the Gemini model (default: uses DEFAULT_MODEL constant)
            api_key: Google API key (uses GOOGLE_API_KEY env var if None)
            temperature: Sampling temperature (0.0-1.0, higher = more creative)
            max_tokens: Maximum tokens to generate (None = no limit, but word count validator will enforce)
        """
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError(
                "Google Generative AI not installed. Install with: pip install google-generativeai"
            )
        
        # Get API key
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        genai.configure(api_key=api_key)
        
        # Get model name and validate it
        raw_model_name = model_name or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.model_name = _validate_model_name(raw_model_name)
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The main prompt
            system_prompt: System/instruction prompt (optional)
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            stop_sequences: Sequences that stop generation (optional)
        
        Returns:
            Generated text
        """
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Get the model (handle both full model names and short names)
            model_name = self.model_name
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
            
            model = self.genai.GenerativeModel(model_name)
            
            # Build generation config
            generation_config = {
                "temperature": temperature or self.temperature,
            }
            if max_tokens or self.max_tokens:
                generation_config["max_output_tokens"] = max_tokens or self.max_tokens
            
            # Generate
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            
            # Extract text - handle multiple response formats
            content = ""
            if hasattr(response, 'text') and response.text:
                content = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from candidates
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                content += part.text
                    elif hasattr(candidate, 'text') and candidate.text:
                        content += candidate.text
                # Fallback to original method if above didn't work
                if not content and response.candidates:
                    try:
                        content = response.candidates[0].content.parts[0].text
                    except (AttributeError, IndexError):
                        pass
            else:
                content = str(response)
            
            # Log if content seems too short (potential issue)
            # Check both character count and word count
            word_count = len(content.split()) if content else 0
            if content and (len(content) < 500 or word_count < 300):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Generated content seems very short ({len(content)} chars, {word_count} words). "
                    f"Response may have been truncated or extraction failed. "
                    f"Max tokens was: {max_tokens or self.max_tokens}"
                )
                # Check if response was cut off mid-sentence
                if content and not content.rstrip().endswith(('.', '!', '?', '"', "'")):
                    logger.warning(
                        "Story appears to be cut off mid-sentence. "
                        "Consider increasing max_output_tokens or simplifying the prompt."
                    )
            
            # Apply stop sequences if provided
            if stop_sequences and content:
                for stop_seq in stop_sequences:
                    if stop_seq in content:
                        content = content.split(stop_seq)[0]
            
            return content.strip() if content else ""
        
        except Exception as e:
            raise RuntimeError(
                f"Gemini API generation failed. Check your API key and model name.\n"
                f"Error: {str(e)}"
            )
    
    def check_availability(self) -> bool:
        """
        Check if the LLM backend is available.
        
        Returns:
            True if available, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Try to list models (lightweight check)
            models = self.genai.list_models()
            # Check if our model is available
            model_names = [m.name for m in models if hasattr(m, 'name')]
            is_available = any(self.model_name in name for name in model_names)
            if not is_available:
                logger.warning(f"Model '{self.model_name}' not found in available models")
            return is_available
        except AttributeError as e:
            logger.error(f"Error listing models (AttributeError): {e}", exc_info=True)
            # If list fails, try a simple generation test
            try:
                model_name = self.model_name
                if not model_name.startswith("models/"):
                    model_name = f"models/{model_name}"
                model = self.genai.GenerativeModel(model_name)
                return True
            except (ValueError, ImportError) as e2:
                logger.error(f"Error during generation test (configuration/import): {e2}", exc_info=True)
                return False
            except ConnectionError as e2:
                logger.error(f"Error during generation test (network): {e2}", exc_info=True)
                return False
            except TimeoutError as e2:
                logger.error(f"Error during generation test (timeout): {e2}", exc_info=True)
                return False
            except Exception as e2:
                logger.error(f"Error during generation test (unexpected): {e2}", exc_info=True)
                return False
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error checking model availability: {e}", exc_info=True)
            return False
        except ValueError as e:
            logger.error(f"Configuration error checking model availability: {e}", exc_info=True)
            return False
        except ImportError as e:
            logger.error(f"Import error checking model availability: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking model availability: {e}", exc_info=True)
            # If list fails, try a simple generation test as fallback
            try:
                model_name = self.model_name
                if not model_name.startswith("models/"):
                    model_name = f"models/{model_name}"
                model = self.genai.GenerativeModel(model_name)
                return True
            except (ValueError, ImportError) as e2:
                logger.error(f"Fallback generation test failed (configuration/import): {e2}", exc_info=True)
                return False
            except ConnectionError as e2:
                logger.error(f"Fallback generation test failed (network): {e2}", exc_info=True)
                return False
            except TimeoutError as e2:
                logger.error(f"Fallback generation test failed (timeout): {e2}", exc_info=True)
                return False
            except Exception as e2:
                logger.error(f"Fallback generation test failed (unexpected): {e2}", exc_info=True)
                return False


# Default client instance (lazy initialization)
_default_client: Optional[LLMClient] = None


def get_default_client() -> LLMClient:
    """
    Get or create the default LLM client.
    
    Uses environment variables for configuration:
    - GOOGLE_API_KEY: Google API key (required)
    - LLM_MODEL: Model name (default: uses DEFAULT_MODEL constant)
    - LLM_TEMPERATURE: Temperature (default: 0.7)
    
    Returns:
        LLMClient instance
    """
    global _default_client
    
    if _default_client is None:
        model_name = os.getenv("LLM_MODEL", DEFAULT_MODEL)
        # Model name will be validated in LLMClient.__init__
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        api_key = os.getenv("GOOGLE_API_KEY", None)
        
        _default_client = LLMClient(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
        )
    
    return _default_client


def generate_story_draft(
    idea: str,
    character: Dict[str, Any],
    theme: str,
    outline: Dict[str, Any],
    scaffold: Dict[str, Any],
    genre_config: Dict[str, Any],
    max_words: int = 7500,
    client: Optional[LLMClient] = None,
) -> str:
    """
    Generate a story draft using LLM.
    
    This function constructs a comprehensive prompt that includes:
    - Premise (idea, character, theme)
    - Outline structure
    - Genre constraints (tone, pace, POV)
    - Distinctiveness requirements
    - Word count limits
    
    Args:
        idea: Story idea
        character: Character description
        theme: Central theme
        outline: Outline structure
        scaffold: Scaffold with POV, tone, pace
        genre_config: Genre configuration
        max_words: Maximum word count
        client: LLM client (uses default if None)
    
    Returns:
        Generated story text
    """
    if client is None:
        client = get_default_client()
    
    # Extract character details
    if isinstance(character, dict):
        char_desc = character.get("description", str(character))
        char_name = character.get("name", "the character")
        char_quirks = character.get("quirks", [])
        char_contradictions = character.get("contradictions", "")
    else:
        char_desc = str(character) if character else ""
        char_name = "the character"
        char_quirks = []
        char_contradictions = ""
    
    # Extract outline structure
    acts = outline.get("acts", {})
    beginning_label = acts.get("beginning", "setup")
    middle_label = acts.get("middle", "complication")
    end_label = acts.get("end", "resolution")
    
    # Extract scaffold details
    pov = scaffold.get("pov", "flexible")
    tone = scaffold.get("tone", "balanced")
    pace = scaffold.get("pace", "moderate")
    constraints = scaffold.get("constraints", {})
    
    # Build system prompt (distinctiveness requirements + outstanding short story framework)
    system_prompt = """You are a skilled short story writer focused on distinctive voice, memorable characters, and non-generic language. Every word must earn its place.

**CRITICAL: You must generate a COMPLETE, FULL-LENGTH short story. Do NOT summarize, paraphrase, or echo back the input. Write the entire narrative from beginning to end.**

FRAMEWORK FOR OUTSTANDING SHORT STORIES:

1. START WITH A SINGLE, SHARP CORE:
   - One central conflict, one emotional question, one moment of change, one character's pivot point
   - The story should revolve around ONE thing done exceptionally well
   - If you can summarize the story's essence in one sentence, you're on the right track

2. DROP THE READER INTO MOTION (In Medias Res):
   - Start in the middle of something happening - no warm-ups
   - Introduce tension in the first paragraph
   - Let the reader feel the stakes before they fully understand them
   - AVOID: Long exposition, backstory dumps, or worldbuilding that doesn't immediately matter

3. USE CHARACTERS AS PRESSURE POINTS:
   - You don't need many characters - you need ONE unforgettable one
   - Give them a desire, a flaw, and a pressure that forces a choice
   - Short stories shine when characters are distilled to their most essential contradictions

4. BUILD TENSION THROUGH COMPRESSION:
   - Every sentence must: advance the plot, reveal character, deepen theme, OR create atmosphere
   - If a sentence does none of these, cut it
   - Compression = intensity

5. ANCHOR THE STORY IN A VIVID, SPECIFIC DETAIL:
   - Readers remember IMAGES, not summaries
   - A smell that defines a room, a gesture that reveals a relationship, a single object that symbolizes the emotional core
   - One or two strong sensory details can carry an entire short story

6. LET THE THEME EMERGE, DON'T ANNOUNCE IT:
   - Show the emotional truth through action
   - Let subtext do the heavy lifting
   - AVOID moralizing or explaining the meaning
   - The best themes are discovered, not delivered

7. END ON A TURN, NOT A BOW:
   - Short stories rarely end with everything resolved
   - End with: a realization, a reversal, a choice, a haunting image, or a question that reframes everything
   - The final beat should feel inevitable but surprising

8. POLISH THE LANGUAGE UNTIL IT SINGS:
   - Cut filler words, strengthen verbs, use rhythm intentionally
   - Make dialogue carry weight
   - Let silence and implication do work
   - A short story is closer to poetry than to a novel

CORE PRINCIPLES:

1. DISTINCTIVENESS (Non-negotiable):
   - NEVER use clichéd phrases like "dark and stormy night," "once upon a time," "in the nick of time," "all hell broke loose"
   - AVOID generic descriptions: "very," "really," "quite," "somewhat," "kind of," "sort of"
   - REJECT stock character archetypes: the wise old mentor, the chosen one, the damsel in distress
   - USE specific, concrete details instead of vague abstractions
   - CREATE unexpected story beats that subvert predictable patterns
   - Every phrase must be fresh and specific to THIS story

2. CHARACTER VOICE (Critical):
   - Each character must have a UNIQUE voice with distinct speech patterns
   - Dialogue should reflect: vocabulary choices, sentence rhythm, regional markers (if applicable), speech quirks
   - Character voice must be CONSISTENT throughout the story
   - Narrative voice (if first person) must match the character's personality and background
   - Character quirks and contradictions should manifest in HOW they speak, not just what they say
   - Avoid generic dialogue that could belong to any character

3. TONE CONSISTENCY (Essential):
   - Establish the tone early and MAINTAIN it throughout the entire story
   - Tone should align with genre expectations but remain distinctive
   - Avoid unintentional tone shifts that break immersion
   - Every sentence should reinforce the established tone
   - If tone shifts occur, they must be intentional and serve the narrative

4. LANGUAGE PRECISION:
   - Use vivid, precise language over vague descriptions
   - Prioritize specific sensory details over generic observations
   - Every word must contribute to voice, tone, or narrative momentum
   - Maximize impact per word within strict word count limits

5. STORY COMPLETENESS (Essential):
   - Write the ENTIRE story from first sentence to last
   - Include multiple scenes with dialogue, action, and description
   - Develop the full narrative arc: beginning, middle, and end
   - Do NOT stop after a few paragraphs - continue until the story is complete
   - Aim for substantial length (thousands of words, not dozens)"""

    # Build main prompt
    prompt_parts = [
        f"Write a short story with the following specifications:\n\n",
        f"**Story Idea (Single Sharp Core):** {idea}\n",
        "REMEMBER: Great short stories are about ONE thing done exceptionally well.\n",
        "This story should revolve around one central conflict, one emotional question, one moment of change.\n",
        "If you can summarize the story's essence in one sentence, you're on the right track.\n\n",
    ]
    
    # Enhanced character section with voice emphasis
    if char_desc:
        prompt_parts.append(f"**Character:** {char_name}: {char_desc}\n")
        if char_quirks:
            prompt_parts.append(f"Quirks: {', '.join(char_quirks[:3])}\n")
            prompt_parts.append("CRITICAL: These quirks must manifest in the character's VOICE—how they speak, their vocabulary choices, sentence rhythm, and speech patterns.\n")
        if char_contradictions:
            prompt_parts.append(f"Contradictions: {char_contradictions}\n")
            prompt_parts.append("CRITICAL: These contradictions should be evident in dialogue and internal voice, not just stated.\n")
        prompt_parts.append("\n")
    
    if theme:
        prompt_parts.append(f"**Theme:** {theme}\n\n")
    
    prompt_parts.append(f"**Story Structure (follow this flow, but DO NOT label sections with headers):**\n")
    prompt_parts.append(f"- Begin with: {beginning_label.title()} - establish the world and character\n")
    prompt_parts.append(f"- Develop: {middle_label.title()} - rising action and complications\n")
    prompt_parts.append(f"- Resolve: {end_label.title()} - satisfying conclusion\n")
    prompt_parts.append("REMEMBER: Write this as continuous prose, NOT as labeled sections with headers.\n\n")
    
    # Enhanced style requirements with tone consistency emphasis
    prompt_parts.append(f"**Style Requirements:**\n")
    prompt_parts.append(f"- POV: {pov}\n")
    prompt_parts.append(f"- Tone: {tone} (ESTABLISH THIS TONE IN THE FIRST PARAGRAPH AND MAINTAIN IT CONSISTENTLY THROUGHOUT)\n")
    prompt_parts.append(f"- Pace: {pace}\n\n")
    
    # Add sensory focus if available
    sensory_focus = constraints.get("sensory_focus", [])
    if sensory_focus and sensory_focus != ["balanced"]:
        prompt_parts.append(f"**Sensory Focus:** {', '.join(sensory_focus)}\n")
        prompt_parts.append("Emphasize these sensory details throughout the story to create vivid, specific imagery.\n\n")
    
    prompt_parts.append(f"**CRITICAL REQUIREMENTS:**\n")
    prompt_parts.append(f"- Maximum word count: {max_words} words (STRICT LIMIT)\n")
    prompt_parts.append("- DISTINCTIVENESS: Zero tolerance for clichés, generic phrases, or stock character archetypes\n")
    prompt_parts.append("- CHARACTER VOICE: Every character must have a unique, consistent voice that reflects their quirks and contradictions\n")
    prompt_parts.append("- TONE CONSISTENCY: Maintain the '{tone}' tone from first sentence to last—no unintentional shifts\n")
    prompt_parts.append("- LANGUAGE: Use specific, vivid descriptions. Replace vague words with precise details\n")
    prompt_parts.append("- DIALOGUE: Each character's speech must be distinctive and consistent with their personality\n")
    prompt_parts.append("- NARRATIVE VOICE: If first person, the narrator's voice must match their character throughout\n\n")
    
    prompt_parts.append("**WRITING INSTRUCTIONS (Following Outstanding Short Story Framework):**\n\n")
    prompt_parts.append("**OPENING (In Medias Res):**\n")
    prompt_parts.append("1. Drop the reader into motion - start in the middle of something happening\n")
    prompt_parts.append("2. Create immediate tension in the first paragraph\n")
    prompt_parts.append("3. Establish tone and stakes before full context is revealed\n")
    prompt_parts.append("4. AVOID exposition dumps or backstory - let details emerge naturally\n\n")
    prompt_parts.append("**CHARACTER AS PRESSURE POINT:**\n")
    prompt_parts.append("5. Focus on ONE unforgettable character with a clear desire, flaw, and pressure point\n")
    prompt_parts.append("6. Introduce character through their unique voice and specific actions, not generic descriptions\n")
    prompt_parts.append("7. Show their essential contradictions through what they do and say\n")
    prompt_parts.append("8. Dialogue must sound like THIS specific character, not a generic person\n\n")
    prompt_parts.append("**COMPRESSION & TENSION:**\n")
    prompt_parts.append("9. Every sentence must: advance plot, reveal character, deepen theme, OR create atmosphere\n")
    prompt_parts.append("10. If a sentence does none of these, it doesn't belong\n")
    prompt_parts.append("11. Build tension through compression - intensity comes from what's left unsaid\n\n")
    prompt_parts.append("**VIVID, SPECIFIC DETAILS:**\n")
    prompt_parts.append("12. Anchor the story in concrete sensory details: a smell, a gesture, a specific object\n")
    prompt_parts.append("13. Use one or two strong images that carry emotional weight throughout\n")
    prompt_parts.append("14. Show, don't tell - let readers remember images, not summaries\n\n")
    prompt_parts.append("**THEME & LANGUAGE:**\n")
    prompt_parts.append("15. Let the theme emerge through action and subtext - DON'T announce or moralize\n")
    prompt_parts.append("16. Polish language: cut filler words, strengthen verbs, use rhythm intentionally\n")
    prompt_parts.append("17. Make dialogue carry weight - let silence and implication do work\n")
    prompt_parts.append("18. Every word must earn its place - this is closer to poetry than prose\n\n")
    prompt_parts.append("**ENDING (Turn, Not a Bow):**\n")
    prompt_parts.append("19. End on a turn: a realization, reversal, choice, haunting image, or reframing question\n")
    prompt_parts.append("20. The ending should feel inevitable but surprising\n")
    prompt_parts.append("21. Don't tie everything up - short stories rarely end with everything resolved\n")
    prompt_parts.append("22. The final beat should shift the reader's understanding\n\n")
    
    # Calculate target word count for a standard short story (aim for substantial length)
    # Standard short stories are typically 1,000-7,500 words
    # Aim for 2,000-4,000 words for a substantial short story
    target_word_count = min(max_words, max(2000, int(max_words * 0.5)))
    
    prompt_parts.append("**CRITICAL: Write a COMPLETE, FULL-LENGTH short story.**\n\n")
    prompt_parts.append(f"**TARGET LENGTH: Aim for approximately {target_word_count:,} to {max_words:,} words.**\n")
    prompt_parts.append("This must be a FULL story with:\n")
    prompt_parts.append("- A complete beginning that establishes the world and character\n")
    prompt_parts.append("- A developed middle with rising action and complications\n")
    prompt_parts.append("- A satisfying ending that resolves the central conflict\n")
    prompt_parts.append("- Multiple scenes and character interactions\n")
    prompt_parts.append("- Dialogue, action, and description throughout\n\n")
    prompt_parts.append("**DO NOT:**\n")
    prompt_parts.append("- Summarize or paraphrase the story idea\n")
    prompt_parts.append("- Write a brief synopsis or outline\n")
    prompt_parts.append("- Echo back the input information\n")
    prompt_parts.append("- Stop after a few sentences\n\n")
    prompt_parts.append("**DO:**\n")
    prompt_parts.append("- Write the complete narrative prose from start to finish\n")
    prompt_parts.append("- Develop scenes with specific details and dialogue\n")
    prompt_parts.append("- Show character development through actions and interactions\n")
    prompt_parts.append("- Create a full story arc with all three acts fully developed\n")
    prompt_parts.append("- Use vivid, specific language throughout\n\n")
    
    prompt_parts.append("**EXCELLENCE CHECKLIST (Verify Before Writing):**\n")
    prompt_parts.append("✓ Does the story revolve around ONE central emotional or narrative idea?\n")
    prompt_parts.append("✓ Does the opening create immediate tension (in medias res)?\n")
    prompt_parts.append("✓ Does every scene push the story forward (compression)?\n")
    prompt_parts.append("✓ Is the protagonist forced to make a meaningful choice?\n")
    prompt_parts.append("✓ Does the ending shift the reader's understanding (turn, not bow)?\n")
    prompt_parts.append("✓ Is the language tight, vivid, and intentional (polished)?\n")
    prompt_parts.append("✓ Are there vivid, specific details that anchor the story?\n")
    prompt_parts.append("✓ Does the theme emerge naturally without being announced?\n\n")
    
    prompt_parts.append("**FINAL INSTRUCTIONS - READ CAREFULLY:**\n")
    prompt_parts.append("Write the complete story now, following the structure and framework above.\n\n")
    prompt_parts.append("**CRITICAL FORMATTING RULES:**\n")
    prompt_parts.append("✗ DO NOT use markdown headers like ## Setup, ## Complication, ## Resolution\n")
    prompt_parts.append("✗ DO NOT use any markdown formatting (no #, ##, ###, **, etc.)\n")
    prompt_parts.append("✓ Write ONLY plain prose narrative\n")
    prompt_parts.append("✓ Start directly with the story - no headers, no labels, just the story\n")
    prompt_parts.append("✓ Write in paragraphs, using natural story flow\n\n")
    prompt_parts.append("Be precise, memorable, and distinctive. Every word must earn its place.\n\n")
    prompt_parts.append(f"**CRITICAL: FULL-LENGTH STORY REQUIREMENT**\n")
    prompt_parts.append(f"This MUST be a COMPLETE, FULL-LENGTH short story of {target_word_count:,} to {max_words:,} words.\n\n")
    prompt_parts.append("**YOU MUST CONTINUE WRITING UNTIL:**\n")
    prompt_parts.append(f"✓ You have written at least {target_word_count:,} words (this is MANDATORY)\n")
    prompt_parts.append("✓ The story has a complete beginning, middle, and ending\n")
    prompt_parts.append("✓ All major plot threads are resolved\n")
    prompt_parts.append("✓ The story feels complete and satisfying\n\n")
    prompt_parts.append("**DO NOT:**\n")
    prompt_parts.append("✗ Stop after a few paragraphs\n")
    prompt_parts.append("✗ Stop mid-sentence\n")
    prompt_parts.append("✗ Stop before reaching the target word count\n")
    prompt_parts.append("✗ Leave the story incomplete or unresolved\n\n")
    prompt_parts.append("**CONTINUE WRITING:**\n")
    prompt_parts.append("Keep writing scene after scene. Develop dialogue, action, and description.\n")
    prompt_parts.append("Build tension, develop characters, and resolve conflicts.\n")
    prompt_parts.append(f"Write until you have reached at least {target_word_count:,} words.\n")
    prompt_parts.append("The story should hit hard, feel complete, and linger in the reader's mind.\n")
    prompt_parts.append("DO NOT STOP UNTIL THE STORY IS FULLY COMPLETE.\n\n")
    prompt_parts.append("**REMEMBER: Write ONLY plain prose. NO markdown headers (##, ###). NO section labels. Just the story narrative from start to finish.**\n")
    
    prompt = "".join(prompt_parts)
    
    # Calculate accurate max tokens based on prompt size and target word count
    # Use the target word count (not max) to ensure we allocate enough tokens
    estimated_max_tokens = _calculate_max_output_tokens(
        prompt=prompt,
        system_prompt=system_prompt,
        model_name=client.model_name,
        target_word_count=target_word_count
    )
    
    # FOR FULL-LENGTH STORIES: Request MAXIMUM tokens (8192)
    # This ensures the model has enough space to write complete stories
    if target_word_count >= 2000:
        # For full-length stories, always request maximum tokens
        estimated_max_tokens = min(8192, estimated_max_tokens)
        estimated_max_tokens = max(6000, estimated_max_tokens)  # At least 6000 tokens
    else:
        # For shorter stories, calculate based on word count
        min_tokens_for_story = int(target_word_count * 1.5)  # ~1.5 tokens per word
        estimated_max_tokens = max(estimated_max_tokens, min_tokens_for_story)
    
    # Log token allocation for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Story generation: target_words={target_word_count}, "
        f"max_tokens={estimated_max_tokens}, "
        f"min_required={min_tokens_for_story}"
    )
    
    # Generate
    try:
        generated_text = client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,  # Slightly higher for creativity
            max_tokens=estimated_max_tokens,
        )
        
        # Log initial generation result
        initial_word_count = len(generated_text.split()) if generated_text else 0
        logger.info(
            f"Initial generation complete: {initial_word_count} words, "
            f"{len(generated_text)} characters, max_tokens={estimated_max_tokens}"
        )
        
        if not generated_text or len(generated_text.strip()) < 100:
            logger.error(
                f"Generated text is suspiciously short: {len(generated_text)} chars. "
                f"This may indicate an API error or response extraction failure."
            )
            # Log the actual response for debugging
            logger.error(f"Generated text content: {repr(generated_text[:500])}")
            # If text is extremely short, raise exception to trigger template fallback
            # But log it clearly so we know what happened
            if len(generated_text.strip()) < 50:
                logger.error(
                    f"LLM returned extremely short text: {repr(generated_text)}. "
                    f"This suggests the API key may be invalid or the API call failed. "
                    f"Falling back to template generation."
                )
                raise ValueError(
                    f"Story generation returned suspiciously short text ({len(generated_text)} chars): {repr(generated_text[:100])}. "
                    f"This may indicate an API issue. Please check your API key and model configuration."
                )
    except Exception as e:
        logger.error(f"Story generation failed: {e}", exc_info=True)
        raise
    
    # Clean up any markdown headers that might have been generated
    if generated_text:
        # Remove markdown headers (##, ###, etc.)
        lines = generated_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are just markdown headers
            if re.match(r'^#+\s+\w+', line.strip()):
                continue
            # Remove markdown formatting from lines
            cleaned_line = re.sub(r'^#+\s+', '', line)
            cleaned_lines.append(cleaned_line)
        generated_text = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining markdown formatting
        generated_text = re.sub(r'^##+\s*', '', generated_text, flags=re.MULTILINE)
        generated_text = re.sub(r'^###+\s*', '', generated_text, flags=re.MULTILINE)
    
    # Check if story is too short (FULL-LENGTH requirement)
    word_count = len(generated_text.split()) if generated_text else 0
    is_too_short = word_count < target_word_count * 0.8  # Less than 80% of target
    is_truncated = (
        generated_text and 
        not generated_text.rstrip().endswith(('.', '!', '?', '"', "'"))
    )
    
    # If story is too short OR truncated, continue generation
    if is_too_short or is_truncated:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Story appears truncated: {word_count} words (target: {target_word_count}). "
            f"Attempting to continue generation..."
        )
        
        # Try to continue the story - be aggressive about reaching full length
        remaining_words = max(0, target_word_count - word_count)
        continuation_prompt = f"""Continue and complete the following short story. 

CURRENT STATUS: The story is at {word_count} words but MUST reach at least {target_word_count:,} words total.

REQUIREMENT: Continue writing until the story is FULLY COMPLETE with:
- A complete middle section with multiple scenes
- A satisfying ending that resolves the central conflict
- At least {remaining_words:,} more words to reach the target length

Current story so far:
{generated_text}

Continue writing the story from where it left off. Develop scenes, dialogue, and action. Build to a complete resolution. DO NOT STOP until you have added at least {remaining_words:,} more words and the story feels complete."""
        
        try:
            # Request maximum tokens for continuation to ensure we get enough
            continuation_tokens = min(8192, estimated_max_tokens)
            continuation = client.generate(
                prompt=continuation_prompt,
                system_prompt="You are completing a short story. Continue writing until the story is FULLY COMPLETE and reaches the target word count. Do not stop early.",
                temperature=0.8,
                max_tokens=continuation_tokens,
            )
            generated_text = generated_text + " " + continuation
            new_word_count = len(generated_text.split())
            logger.info(f"Story continuation added: {len(continuation.split())} additional words (total: {new_word_count} words)")
            
            # If still too short, try one more continuation
            if new_word_count < target_word_count * 0.9:
                logger.warning(f"Story still short after continuation ({new_word_count} words). Attempting second continuation...")
                second_continuation_prompt = f"""The story is still incomplete at {new_word_count} words. It needs to reach {target_word_count:,} words. Continue writing more scenes and complete the ending.

Current story:
{generated_text}

Continue with more scenes, dialogue, and action. Complete the story fully."""
                second_continuation = client.generate(
                    prompt=second_continuation_prompt,
                    system_prompt="Complete the short story. Keep writing until it's fully done.",
                    temperature=0.8,
                    max_tokens=min(4000, continuation_tokens),
                )
                generated_text = generated_text + " " + second_continuation
                final_word_count = len(generated_text.split())
                logger.info(f"Second continuation added: {len(second_continuation.split())} words (final total: {final_word_count} words)")
        except Exception as e:
            logger.error(f"Failed to continue story: {e}")
    
    return generated_text


def revise_story_text(
    text: str,
    distinctiveness_issues: Dict[str, Any],
    max_words: int = 7500,
    client: Optional[LLMClient] = None,
) -> str:
    """
    Revise story text to improve distinctiveness and sharpen language.
    
    Args:
        text: Original story text
        distinctiveness_issues: Results from check_distinctiveness()
        max_words: Maximum word count
        client: LLM client (uses default if None)
    
    Returns:
        Revised story text
    """
    if client is None:
        client = get_default_client()
    
    # Build revision instructions
    revision_notes = []
    
    if distinctiveness_issues.get("has_cliches"):
        cliches = distinctiveness_issues.get("found_cliches", [])
        revision_notes.append(f"Replace clichéd phrases: {', '.join(cliches)}")
    
    if distinctiveness_issues.get("has_generic_archetype"):
        generic = distinctiveness_issues.get("generic_elements", [])
        revision_notes.append(f"Avoid generic archetypes: {', '.join(generic)}")
    
    score = distinctiveness_issues.get("distinctiveness_score", 1.0)
    if score < 0.7:
        revision_notes.append("Improve distinctiveness—use more specific, vivid language")
    
    # Calculate original word count to preserve length
    original_word_count = len(text.split()) if text else 0
    
    system_prompt = """You are a skilled editor focused on sharpening language, eliminating clichés, and improving distinctiveness. Every word must earn its place.

**CRITICAL: PRESERVE STORY LENGTH**
- The story must remain approximately the SAME LENGTH after revision
- Do NOT shorten the story significantly
- If the story is already full-length (2000+ words), maintain that length
- Expand descriptions and scenes if needed to maintain length while improving quality

CORE EDITING PRINCIPLES:

1. DISTINCTIVENESS IMPROVEMENT:
   - Replace ALL clichéd phrases with specific, vivid alternatives unique to this story
   - Eliminate generic language: "very," "really," "quite," "somewhat," "kind of," "sort of"
   - Remove stock phrases and predictable descriptions
   - Replace vague abstractions with concrete, sensory details
   - Ensure every phrase is fresh and specific to THIS narrative

2. CHARACTER VOICE CONSISTENCY:
   - PRESERVE each character's unique voice throughout the revision
   - Ensure dialogue maintains distinctive speech patterns, vocabulary, and rhythm
   - Character quirks must be evident in HOW they speak, not just what they say
   - If revising dialogue, maintain the character's voice while improving language quality
   - Narrative voice (if first person) must remain consistent with the character

3. TONE CONSISTENCY:
   - MAINTAIN the established tone throughout the entire revision
   - Do not introduce tone shifts unless they were intentional in the original
   - Every revised sentence must reinforce the original tone
   - Preserve genre-appropriate tone while improving language quality

4. LANGUAGE PRECISION:
   - Sharpen vague language to be precise and memorable
   - Replace generic descriptions with specific, vivid imagery
   - Maintain the story's core meaning and narrative structure
   - Preserve approximately the same length as the original story
   - Stay within the maximum word count limit
   - Improve distinctiveness WITHOUT changing the core narrative or character voices"""

    current_words = len(text.split())
    
    # Determine target word count - expand if too short
    if current_words < 2000:
        # Story is too short - expand it to full length
        target_words = max(2000, min(int(max_words * 0.5), max_words))
        length_instruction = f"**CRITICAL:** The story is currently only {current_words} words, which is too short. "
        length_instruction += f"You MUST expand it to at least {target_words:,} words by adding more scenes, dialogue, descriptions, and narrative development. "
        length_instruction += "Develop the middle section with multiple scenes. Add character interactions and dialogue. "
        length_instruction += "Expand descriptions and add sensory details. Build to a complete, satisfying ending.\n\n"
    else:
        # Story is already full-length - preserve similar length
        target_words = min(current_words, max_words)
        length_instruction = f"**CRITICAL:** The revised story must be approximately {current_words} words (similar length to the original). "
        length_instruction += "Do not significantly shorten or truncate the story. Maintain the full narrative.\n\n"
    
    # Extract tone and voice information from the original text if possible
    # This helps maintain consistency during revision
    prompt_parts = [
        "Revise the following story to improve distinctiveness, strengthen character voices, and sharpen the language:\n\n",
        f"**Current Word Count:** {current_words} words\n",
        f"**Maximum Word Count:** {max_words} words\n",
        length_instruction,
    ]
    
    if revision_notes:
        prompt_parts.append("**Specific Issues to Address:**\n")
        for note in revision_notes:
            prompt_parts.append(f"- {note}\n")
        prompt_parts.append("\n")
    
    prompt_parts.append("**REVISION REQUIREMENTS:**\n")
    prompt_parts.append("1. DISTINCTIVENESS: Replace all clichés and generic language with specific, vivid alternatives\n")
    prompt_parts.append("2. CHARACTER VOICE: Preserve and strengthen each character's unique voice—maintain their speech patterns, vocabulary, and rhythm\n")
    prompt_parts.append("3. TONE CONSISTENCY: Maintain the established tone throughout—do not introduce tone shifts\n")
    prompt_parts.append("4. LANGUAGE PRECISION: Sharpen vague language while preserving meaning and voice\n")
    if current_words < 2000:
        prompt_parts.append(f"5. LENGTH: Expand the story from {current_words} words to at least {target_words:,} words\n")
    else:
        prompt_parts.append(f"5. LENGTH: Keep approximately the same length as the original ({current_words} words)\n")
    prompt_parts.append("6. COMPLETENESS: Provide the COMPLETE revised story—do not truncate or shorten\n\n")
    
    prompt_parts.append("**Original Story:**\n")
    prompt_parts.append(text)
    prompt_parts.append("\n\n")
    
    prompt_parts.append("**REVISION INSTRUCTIONS:**\n")
    prompt_parts.append("1. Analyze the original story's tone and maintain it consistently throughout the revision\n")
    prompt_parts.append("2. Identify each character's voice in the original and preserve/strengthen it in dialogue\n")
    prompt_parts.append("3. Replace clichéd phrases with fresh, specific language unique to this story\n")
    prompt_parts.append("4. Sharpen vague descriptions with concrete, sensory details\n")
    prompt_parts.append("5. Ensure character quirks and contradictions are evident in their speech patterns\n")
    prompt_parts.append("6. Maintain narrative structure and meaning while improving language quality\n")
    if current_words < 2000:
        prompt_parts.append(f"7. Expand the narrative to at least {target_words:,} words while maintaining quality\n\n")
    else:
        prompt_parts.append(f"7. Preserve the approximate length ({current_words} words) and complete narrative\n\n")
    
    if current_words < 2000:
        prompt_parts.append(f"Provide the COMPLETE, EXPANDED revised story. ")
        prompt_parts.append(f"The story must be expanded from {current_words} words to at least {target_words:,} words. ")
        prompt_parts.append("Add more scenes, dialogue, descriptions, and narrative development. ")
        prompt_parts.append("Develop the middle section with multiple scenes and character interactions. ")
        prompt_parts.append("Expand descriptions with sensory details. Build to a complete, satisfying ending. ")
    else:
        prompt_parts.append("Provide the COMPLETE revised story. ")
        prompt_parts.append(f"Maintain similar length ({current_words:,} words). ")
    
    prompt_parts.append("Maintain the same structure, meaning, character voices, and tone. ")
    prompt_parts.append("Improve distinctiveness and language precision without changing the core narrative. ")
    prompt_parts.append(f"Do not exceed the maximum word count limit ({max_words} words). ")
    prompt_parts.append("Do not include markdown formatting—just the revised prose.")
    
    prompt = "".join(prompt_parts)
    
    # Calculate accurate max tokens based on prompt size and target word count
    
    estimated_max_tokens = _calculate_max_output_tokens(
        prompt=prompt,
        system_prompt=system_prompt,
        model_name=client.model_name,
        target_word_count=target_words
    )
    
    # For short stories, ensure we request enough tokens
    if current_words < 2000:
        estimated_max_tokens = max(estimated_max_tokens, 6000)  # At least 6000 tokens for expansion
    
    # Generate revision
    revised_text = client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.6,  # Lower temperature for more focused revision
        max_tokens=estimated_max_tokens,
    )
    
    return revised_text


def generate_outline_structure(
    idea: str,
    character: Optional[Dict[str, Any]] = None,
    theme: Optional[str] = None,
    genre: Optional[str] = None,
    genre_config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Generate a detailed story outline structure with specific beats.
    
    Creates a three-act structure (beginning, middle, end) with specific beats
    that avoid predictable patterns and emphasize distinctiveness.
    
    Args:
        idea: Story idea/premise
        character: Character description (optional)
        theme: Central theme (optional)
        genre: Genre name (optional)
        genre_config: Genre configuration dict (optional, will be fetched if genre provided)
        use_llm: If True, use LLM for generation (default: True)
        client: LLM client (optional, will use default if not provided)
    
    Returns:
        Dict with outline structure:
        {
            "beginning": {
                "hook": str,  # Opening hook/inciting incident
                "setup": str,  # Setup details
                "beats": List[str]  # Specific beats for beginning
            },
            "middle": {
                "complication": str,  # Main complication
                "rising_action": str,  # Rising action description
                "beats": List[str]  # Specific beats for middle
            },
            "end": {
                "climax": str,  # Climax description
                "resolution": str,  # Resolution details
                "beats": List[str]  # Specific beats for end
            },
            "memorable_moments": List[str],  # Key memorable moments
            "voice_opportunities": List[str]  # Scenes where voice can shine
        }
    """
    # Get genre config if needed
    if genre_config is None and genre:
        from ..genres import get_genre_config
        genre_config = get_genre_config(genre)
    
    # Get outline structure labels from genre
    if genre_config:
        outline_labels = genre_config.get("outline", ["setup", "complication", "resolution"])
        framework = genre_config.get("framework", "narrative_arc")
    else:
        outline_labels = ["setup", "complication", "resolution"]
        framework = "narrative_arc"
    
    beginning_label = outline_labels[0] if len(outline_labels) > 0 else "setup"
    middle_label = outline_labels[1] if len(outline_labels) > 1 else "complication"
    end_label = outline_labels[2] if len(outline_labels) > 2 else "resolution"
    
    # Try LLM generation if enabled
    if use_llm:
        try:
            if client is None:
                client = get_default_client()
            
            # Build character description
            char_desc = ""
            if character:
                if isinstance(character, dict):
                    char_name = character.get("name", "the character")
                    char_desc = character.get("description", str(character))
                    quirks = character.get("quirks", [])
                    contradictions = character.get("contradictions", "")
                    
                    char_desc = f"Character: {char_name}\n"
                    if char_desc:
                        char_desc += f"Description: {char_desc}\n"
                    if quirks:
                        char_desc += f"Quirks: {', '.join(quirks) if isinstance(quirks, list) else quirks}\n"
                    if contradictions:
                        char_desc += f"Contradictions: {contradictions}\n"
                else:
                    char_desc = f"Character: {str(character)}\n"
            
            # Build prompt
            system_prompt = """You are a creative writing assistant specializing in distinctive, memorable short stories.
Your task is to create a detailed outline structure that avoids predictable beats and emphasizes unique, specific moments.

CRITICAL REQUIREMENTS:
1. AVOID PREDICTABLE BEATS: No "call to adventure", "refusal of the call", "meeting the mentor", "grand gesture", etc.
2. BE SPECIFIC: Use concrete details, not generic descriptions
3. CREATE MEMORABLE MOMENTS: Scenes that create lasting impressions
4. IDENTIFY VOICE OPPORTUNITIES: Mark scenes where character voice can shine
5. FOLLOW GENRE STRUCTURE: Use the provided genre framework as a guide, not a formula

Output format (JSON):
{
    "beginning": {
        "hook": "specific opening hook/inciting incident",
        "setup": "setup details",
        "beats": ["beat 1", "beat 2", "beat 3"]
    },
    "middle": {
        "complication": "main complication",
        "rising_action": "rising action description",
        "beats": ["beat 1", "beat 2", "beat 3"]
    },
    "end": {
        "climax": "climax description",
        "resolution": "resolution details",
        "beats": ["beat 1", "beat 2"]
    },
    "memorable_moments": ["moment 1", "moment 2"],
    "voice_opportunities": ["scene 1", "scene 2"]
}"""
            
            prompt_parts = [
                f"Story Idea: {idea}\n",
            ]
            
            if char_desc:
                prompt_parts.append(char_desc)
            
            if theme:
                prompt_parts.append(f"Theme: {theme}\n")
            
            if genre:
                prompt_parts.append(f"Genre: {genre}\n")
                prompt_parts.append(f"Framework: {framework}\n")
                prompt_parts.append(f"Structure: {beginning_label} → {middle_label} → {end_label}\n")
            
            prompt_parts.append(
                "\nGenerate a detailed outline structure with specific beats for each act. "
                "Avoid predictable story patterns. Focus on unique, memorable moments that make this story distinctive."
            )
            
            prompt = "".join(prompt_parts)
            
            # Generate outline
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher temperature for creative outline generation
            )
            
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                try:
                    outline_data = json.loads(json_str)
                    # Validate structure
                    if all(key in outline_data for key in ["beginning", "middle", "end"]):
                        return outline_data
                except json.JSONDecodeError:
                    pass
            
            # If JSON parsing failed, try to extract structure from text
            # This is a fallback for when LLM doesn't return valid JSON
            outline_data = _parse_outline_from_text(response, beginning_label, middle_label, end_label)
            if outline_data:
                return outline_data
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM outline generation failed: {e}, using template fallback")
    
    # Template-based fallback
    return _generate_template_outline(idea, character, theme, beginning_label, middle_label, end_label)


def _parse_outline_from_text(text: str, beginning_label: str, middle_label: str, end_label: str) -> Optional[Dict[str, Any]]:
    """
    Parse outline structure from text response (fallback when JSON parsing fails).
    
    Args:
        text: Text response from LLM
        beginning_label: Label for beginning act
        middle_label: Label for middle act
        end_label: Label for end act
    
    Returns:
        Dict with outline structure or None if parsing fails
    """
    import re
    
    # Try to extract sections
    beginning_match = re.search(rf'(?i)(?:{re.escape(beginning_label)}|beginning)[\s:]*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:{re.escape(middle_label)}|middle)|$)', text, re.DOTALL)
    middle_match = re.search(rf'(?i)(?:{re.escape(middle_label)}|middle)[\s:]*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:{re.escape(end_label)}|end)|$)', text, re.DOTALL)
    end_match = re.search(rf'(?i)(?:{re.escape(end_label)}|end)[\s:]*([^\n]+(?:\n[^\n]+)*?)$', text, re.DOTALL)
    
    outline = {
        "beginning": {
            "hook": beginning_match.group(1).strip()[:200] if beginning_match else f"{beginning_label}: Opening scene",
            "setup": "",
            "beats": []
        },
        "middle": {
            "complication": middle_match.group(1).strip()[:200] if middle_match else f"{middle_label}: Complication develops",
            "rising_action": "",
            "beats": []
        },
        "end": {
            "climax": end_match.group(1).strip()[:200] if end_match else f"{end_label}: Resolution",
            "resolution": "",
            "beats": []
        },
        "memorable_moments": [],
        "voice_opportunities": []
    }
    
    return outline


def _generate_template_outline(
    idea: str,
    character: Optional[Dict[str, Any]],
    theme: Optional[str],
    beginning_label: str,
    middle_label: str,
    end_label: str,
) -> Dict[str, Any]:
    """
    Generate a template-based outline structure (fallback when LLM unavailable).
    
    Args:
        idea: Story idea
        character: Character description (optional)
        theme: Theme (optional)
        beginning_label: Label for beginning
        middle_label: Label for middle
        end_label: Label for end
    
    Returns:
        Dict with outline structure
    """
    # Extract character name if available
    char_name = "the character"
    if character:
        if isinstance(character, dict):
            char_name = character.get("name", "the character")
        else:
            char_name = str(character).split()[0] if str(character).split() else "the character"
    
    outline = {
        "beginning": {
            "hook": f"Opening: {idea[:100]}",
            "setup": f"Introduce {char_name} and the initial situation",
            "beats": [
                f"Establish {char_name}'s world",
                "Inciting incident that disrupts the status quo",
                "Initial response or reaction"
            ]
        },
        "middle": {
            "complication": "The situation deepens with unexpected complications",
            "rising_action": "Stakes increase as challenges mount",
            "beats": [
                "First major obstacle or conflict",
                "Character must make difficult choices",
                "Tension escalates toward climax"
            ]
        },
        "end": {
            "climax": "The moment of highest tension and decision",
            "resolution": "How the story resolves and what changes",
            "beats": [
                "Climactic moment",
                "Resolution and consequences"
            ]
        },
        "memorable_moments": [
            "A scene that creates a lasting visual or emotional impression",
            "A moment that reveals character depth"
        ],
        "voice_opportunities": [
            "Dialogue scene that shows character voice",
            "Internal moment that reveals perspective"
        ]
    }
    
    if theme:
        outline["end"]["resolution"] += f" (exploring theme: {theme})"
    
    return outline


def generate_scaffold_structure(
    premise: Dict[str, Any],
    outline: Dict[str, Any],
    genre: Optional[str] = None,
    genre_config: Optional[Dict[str, Any]] = None,
    use_llm: bool = True,
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Generate a detailed scaffold structure with voice development.
    
    Creates voice profiles, conflict mapping, prose characteristics, and stylistic
    parameters that establish distinctive narrative and character voices.
    
    Args:
        premise: Premise object with idea, character, theme
        outline: Outline object with beats and structure
        genre: Genre name (optional)
        genre_config: Genre configuration dict (optional)
        use_llm: If True, use LLM for generation (default: True)
        client: LLM client (optional, will use default if not provided)
    
    Returns:
        Dict with scaffold structure:
        {
            "narrative_voice": {
                "pov": str,  # Point of view with specific characteristics
                "pov_rationale": str,  # Why this POV was chosen
                "prose_style": str,  # Sparse, lyrical, dialogue-heavy, etc.
                "sentence_rhythm": str,  # Short bursts, long flowing, varied
                "language_register": str,  # Formal/colloquial/slang mix
                "voice_characteristics": List[str]  # Specific voice markers
            },
            "character_voices": {
                "character_name": {
                    "speech_patterns": str,
                    "vocabulary": List[str],
                    "rhythm": str,
                    "voice_markers": List[str],
                    "distinctive_traits": List[str]
                }
            },
            "tone": {
                "emotional_register": str,  # Nuanced tone description
                "mood": str,
                "atmosphere": str,
                "emotional_arc": str
            },
            "conflicts": {
                "internal": List[str],  # Internal tensions
                "external": List[str],  # External conflicts
                "primary_conflict": str,
                "conflict_arc": str
            },
            "sensory_specificity": {
                "primary_senses": List[str],  # Which senses to emphasize
                "sensory_details": Dict[str, str],  # Specific sensory guidance
            },
            "style_guidelines": {
                "sentence_length": str,
                "dialogue_ratio": str,  # How much dialogue vs narrative
                "description_density": str,  # Sparse vs rich
                "pacing": str
            }
        }
    """
    # Extract premise elements
    idea = premise.get("idea", "").strip() if isinstance(premise, dict) else ""
    character = premise.get("character") if isinstance(premise, dict) else None
    theme = premise.get("theme")
    if theme and isinstance(theme, str):
        theme = theme.strip()
    elif not theme:
        theme = None
    
    # Get genre config if needed
    if genre_config is None and genre:
        from ..genres import get_genre_config
        genre_config = get_genre_config(genre)
    
    # Get genre constraints as starting point
    if genre_config:
        constraints = genre_config.get("constraints", {})
        framework = genre_config.get("framework", "narrative_arc")
    else:
        constraints = {}
        framework = "narrative_arc"
    
    # Try LLM generation if enabled
    if use_llm:
        try:
            if client is None:
                client = get_default_client()
            
            # Build character description
            char_desc = ""
            char_name = "the character"
            if character:
                if isinstance(character, dict):
                    char_name = character.get("name", "the character")
                    char_desc = character.get("description", str(character))
                    quirks = character.get("quirks", [])
                    contradictions = character.get("contradictions", "")
                    
                    char_desc = f"Character: {char_name}\n"
                    if char_desc:
                        char_desc += f"Description: {char_desc}\n"
                    if quirks:
                        quirks_str = ', '.join(quirks) if isinstance(quirks, list) else str(quirks)
                        char_desc += f"Quirks: {quirks_str}\n"
                    if contradictions:
                        char_desc += f"Contradictions: {contradictions}\n"
                else:
                    char_desc = f"Character: {str(character)}\n"
            
            # Extract outline information
            outline_acts = outline.get("acts", {})
            beginning_label = outline_acts.get("beginning", "setup")
            middle_label = outline_acts.get("middle", "complication")
            end_label = outline_acts.get("end", "resolution")
            
            voice_opportunities = outline.get("voice_opportunities", [])
            memorable_moments = outline.get("memorable_moments", [])
            
            # Build prompt
            system_prompt = """You are a creative writing assistant specializing in distinctive voice development for short stories.
Your task is to create a detailed scaffold structure that establishes unique narrative and character voices.

CRITICAL REQUIREMENTS:
1. DISTINCTIVE VOICE: Create specific, memorable voice characteristics, not generic descriptions
2. CHARACTER VOICES: Each character must have unique speech patterns, vocabulary, and rhythm
3. CONFLICT-FIRST: Map specific conflicts (internal and external) that drive the story
4. SENSORY SPECIFICITY: Define which senses to emphasize for vividness
5. PROSE CHARACTERISTICS: Specify sentence rhythm, language register, and style
6. AVOID GENERIC: No generic archetypes or formulaic voice patterns

Output format (JSON):
{
    "narrative_voice": {
        "pov": "specific POV with characteristics",
        "pov_rationale": "why this POV was chosen",
        "prose_style": "specific style description",
        "sentence_rhythm": "rhythm description",
        "language_register": "register description",
        "voice_characteristics": ["characteristic 1", "characteristic 2"]
    },
    "character_voices": {
        "character_name": {
            "speech_patterns": "specific patterns",
            "vocabulary": ["word1", "word2"],
            "rhythm": "rhythm description",
            "voice_markers": ["marker1", "marker2"],
            "distinctive_traits": ["trait1", "trait2"]
        }
    },
    "tone": {
        "emotional_register": "nuanced tone",
        "mood": "mood description",
        "atmosphere": "atmosphere description",
        "emotional_arc": "arc description"
    },
    "conflicts": {
        "internal": ["conflict1", "conflict2"],
        "external": ["conflict1", "conflict2"],
        "primary_conflict": "main conflict",
        "conflict_arc": "how conflict develops"
    },
    "sensory_specificity": {
        "primary_senses": ["sense1", "sense2"],
        "sensory_details": {
            "sight": "guidance",
            "sound": "guidance",
            "touch": "guidance"
        }
    },
    "style_guidelines": {
        "sentence_length": "guidance",
        "dialogue_ratio": "guidance",
        "description_density": "guidance",
        "pacing": "guidance"
    }
}"""
            
            prompt_parts = [
                f"Story Idea: {idea}\n",
            ]
            
            if char_desc:
                prompt_parts.append(char_desc)
            
            if theme:
                prompt_parts.append(f"Theme: {theme}\n")
            
            if genre:
                prompt_parts.append(f"Genre: {genre}\n")
                prompt_parts.append(f"Framework: {framework}\n")
            
            prompt_parts.append(f"Outline Structure: {beginning_label} → {middle_label} → {end_label}\n")
            
            if voice_opportunities:
                prompt_parts.append(f"Voice Opportunities: {', '.join(voice_opportunities[:3])}\n")
            
            if memorable_moments:
                prompt_parts.append(f"Memorable Moments: {', '.join(memorable_moments[:2])}\n")
            
            prompt_parts.append(
                "\nGenerate a detailed scaffold structure that establishes distinctive narrative and character voices. "
                "Focus on specific, memorable voice characteristics that make this story unique. "
                "Map conflicts that drive the story. Define sensory specificity and prose characteristics."
            )
            
            prompt = "".join(prompt_parts)
            
            # Generate scaffold
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher temperature for creative voice development
            )
            
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                try:
                    scaffold_data = json.loads(json_str)
                    # Validate structure
                    if "narrative_voice" in scaffold_data:
                        return scaffold_data
                except json.JSONDecodeError:
                    pass
            
            # If JSON parsing failed, use template fallback
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM scaffold generation failed: {e}, using template fallback")
    
    # Template-based fallback
    return _generate_template_scaffold(premise, outline, constraints, framework)


def _generate_template_scaffold(
    premise: Dict[str, Any],
    outline: Dict[str, Any],
    constraints: Dict[str, Any],
    framework: str,
) -> Dict[str, Any]:
    """
    Generate a template-based scaffold structure (fallback when LLM unavailable).
    
    Args:
        premise: Premise object
        outline: Outline object
        constraints: Genre constraints
        framework: Genre framework
    
    Returns:
        Dict with scaffold structure
    """
    # Extract character info
    character = premise.get("character") if isinstance(premise, dict) else None
    char_name = "the character"
    char_quirks = []
    if character:
        if isinstance(character, dict):
            char_name = character.get("name", "the character")
            char_quirks = character.get("quirks", [])
            if not isinstance(char_quirks, list):
                char_quirks = [char_quirks] if char_quirks else []
        else:
            char_name = str(character).split()[0] if str(character).split() else "the character"
    
    # Determine POV from constraints or default
    pov_preference = constraints.get("pov_preference", "flexible")
    if "first" in pov_preference.lower():
        pov = "First person, intimate and immediate"
        pov_rationale = "First person creates closeness to the character's inner world"
    elif "third" in pov_preference.lower():
        pov = "Third person limited, focused on character perspective"
        pov_rationale = "Third person limited provides narrative distance while maintaining character focus"
    else:
        pov = "Third person, flexible perspective"
        pov_rationale = "Third person allows narrative flexibility"
    
    # Determine tone from constraints
    tone_constraint = constraints.get("tone", "balanced")
    if tone_constraint == "dark":
        emotional_register = "Somber with moments of unease, avoiding gratuitous darkness"
        mood = "Atmospheric tension"
    elif tone_constraint == "warm":
        emotional_register = "Tender with emotional depth, avoiding sentimentality"
        mood = "Intimate connection"
    elif tone_constraint == "gritty":
        emotional_register = "Raw and unflinching, with specific detail over generic toughness"
        mood = "Urban realism"
    else:
        emotional_register = "Nuanced emotional range, specific to the story's needs"
        mood = "Balanced emotional landscape"
    
    # Get sensory focus from constraints
    sensory_focus = constraints.get("sensory_focus", ["balanced"])
    if not isinstance(sensory_focus, list):
        sensory_focus = [sensory_focus] if sensory_focus else ["balanced"]
    
    # Build character voice profile
    character_voices = {}
    if char_name and char_name != "the character":
        voice_markers = []
        if char_quirks:
            voice_markers.extend([f"Reflects quirk: {q}" for q in char_quirks[:2]])
        
        character_voices[char_name] = {
            "speech_patterns": "Distinctive patterns that reflect character's unique voice",
            "vocabulary": ["Specific", "memorable", "word choices"] if char_quirks else [],
            "rhythm": "Sentence rhythm that matches character's personality",
            "voice_markers": voice_markers if voice_markers else ["Unique voice characteristics"],
            "distinctive_traits": char_quirks[:3] if char_quirks else ["Distinctive speech"]
        }
    
    # Map conflicts from outline
    outline_beginning = outline.get("beginning", {})
    outline_middle = outline.get("middle", {})
    outline_end = outline.get("end", {})
    
    complication = outline_middle.get("complication", "The situation deepens")
    primary_conflict = complication[:100] if complication else "Character faces specific challenge"
    
    conflicts = {
        "internal": [
            "Character's internal struggle with their own nature",
            "Emotional conflict related to theme"
        ],
        "external": [
            primary_conflict,
            "External forces that complicate the situation"
        ],
        "primary_conflict": primary_conflict,
        "conflict_arc": f"Begins with {outline_beginning.get('hook', 'setup')[:50]}, escalates through {complication[:50]}, resolves with {outline_end.get('resolution', 'resolution')[:50]}"
    }
    
    # Build scaffold structure
    scaffold = {
        "narrative_voice": {
            "pov": pov,
            "pov_rationale": pov_rationale,
            "prose_style": "Precise and memorable, every word earns its place",
            "sentence_rhythm": "Varied rhythm that creates narrative texture",
            "language_register": "Specific register that matches character and setting",
            "voice_characteristics": [
                "Distinctive narrative perspective",
                "Specific, vivid language",
                "Memorable phrasing"
            ]
        },
        "character_voices": character_voices,
        "tone": {
            "emotional_register": emotional_register,
            "mood": mood,
            "atmosphere": "Atmosphere that supports the story's emotional core",
            "emotional_arc": f"Emotional journey from {outline_beginning.get('hook', 'beginning')[:30]} to {outline_end.get('resolution', 'resolution')[:30]}"
        },
        "conflicts": conflicts,
        "sensory_specificity": {
            "primary_senses": sensory_focus[:3] if sensory_focus else ["sight", "sound"],
            "sensory_details": {
                sense: f"Emphasize {sense} for vivid, specific details"
                for sense in (sensory_focus[:3] if sensory_focus else ["sight", "sound", "touch"])
            }
        },
        "style_guidelines": {
            "sentence_length": "Varied sentence length for rhythm and emphasis",
            "dialogue_ratio": "Balance dialogue and narrative based on voice opportunities",
            "description_density": "Specific, vivid details over generic descriptions",
            "pacing": constraints.get("pace", "moderate")
        }
    }
    
    return scaffold
