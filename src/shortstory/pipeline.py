"""
ShortStoryPipeline - Main pipeline class

See pipeline.md for architecture documentation.
See CONCEPTS.md for core principles and terminology.
"""

import re
import logging
import traceback

from .utils import (
    WordCountValidator,
    check_distinctiveness,
    validate_premise,
    validate_story_voices,
    generate_story_draft,
    revise_story_text,
    generate_outline_structure,
    generate_scaffold_structure,
    get_default_client,
)
from .genres import get_genre_config

logger = logging.getLogger(__name__)


class ShortStoryPipeline:
    """
    Modular pipeline for short story creation.
    
    Stages:
    1. Premise capture
    2. Outline generation
    3. Scaffolding
    4. Drafting
    5. Revision
    """
    
    def __init__(self, max_word_count=7500):
        """
        Initialize the pipeline.
        
        Args:
            max_word_count: Maximum word count (default: 7500)
        """
        self.premise = None
        self.outline = None
        self._scaffold_data = None
        self._draft_data = None
        self._revised_draft_data = None
        self.word_validator = WordCountValidator(max_word_count)
        self.genre = None
        self.genre_config = None
    
    def capture_premise(self, idea, character, theme, validate=True):
        """
        Stage 1: Capture premise with distinctiveness validation.
        
        Args:
            idea: Initial concept (must avoid generic setups)
            character: Character sketch with quirks, contradictions, voice markers
            theme: Central question (resonant, not clichéd)
            validate: If True, run distinctiveness validation
        
        Returns:
            Structured premise object with validation results
        """
        # Validate premise
        validation_result = None
        if validate:
            validation_result = validate_premise(idea, character, theme)
            if not validation_result["is_valid"]:
                raise ValueError(
                    f"Premise validation failed: {validation_result['errors']}"
                )
        
        self.premise = {
            "idea": idea,
            "character": character,
            "theme": theme,
            "validation": validation_result,
        }
        return self.premise
    
    def _get_genre_config(self, genre):
        """
        Get genre configuration (helper method to avoid DRY violation).
        
        Args:
            genre: Genre name
            
        Returns:
            Genre configuration dict or None
        """
        if genre:
            return get_genre_config(genre)
        return None
    
    def generate_outline(self, premise=None, genre=None, use_llm=True):
        """
        Stage 2: Generate outline with unexpected beats.
        
        Generates a detailed outline structure with specific beats for beginning, middle, and end.
        Uses LLM if available, with template fallback. Validates against predictable patterns.
        
        Args:
            premise: Premise object (uses self.premise if None)
            genre: Genre name (uses self.genre if None)
            use_llm: If True, use LLM for generation (default: True)
        
        Returns:
            Outline object with detailed beats for beginning, middle, end following genre structure
        """
        if premise is None:
            premise = self.premise
        if premise is None:
            raise ValueError("Cannot generate outline without premise. Call capture_premise() first.")
        
        if genre is None:
            genre = self.genre
        
        # Get genre-specific outline structure
        genre_config = self._get_genre_config(genre)
        if genre_config:
            outline_structure = genre_config.get("outline", ["setup", "complication", "resolution"])
            framework = genre_config.get("framework", "narrative_arc")
        else:
            outline_structure = ["setup", "complication", "resolution"]
            framework = "narrative_arc"
        
        # Extract premise elements
        idea = premise.get("idea", "").strip() if isinstance(premise, dict) else str(premise)
        if not idea:
            raise ValueError("Cannot generate outline without story idea in premise.")
        
        character = premise.get("character") if isinstance(premise, dict) else None
        theme = premise.get("theme")
        if theme and isinstance(theme, str):
            theme = theme.strip()
        elif not theme:
            theme = None
        
        # Generate detailed outline structure
        detailed_outline = generate_outline_structure(
            idea=idea,
            character=character,
            theme=theme,
            genre=genre,
            genre_config=genre_config,
            use_llm=use_llm,
        )
        
        # Validate outline against predictable beats
        from .cliche_detector import get_cliche_detector
        cliche_detector = get_cliche_detector()
        
        # Check for predictable beats in the outline
        outline_text = f"{detailed_outline.get('beginning', {}).get('hook', '')} {detailed_outline.get('middle', {}).get('complication', '')} {detailed_outline.get('end', {}).get('resolution', '')}"
        beat_check = cliche_detector._detect_predictable_beats(outline_text)
        
        # Build complete outline structure
        self.outline = {
            "premise": premise,
            "genre": genre,
            "framework": framework,
            "structure": outline_structure,
            "acts": {
                "beginning": outline_structure[0] if len(outline_structure) > 0 else "setup",
                "middle": outline_structure[1] if len(outline_structure) > 1 else "complication",
                "end": outline_structure[2] if len(outline_structure) > 2 else "resolution"
            },
            # Detailed beats
            "beginning": detailed_outline.get("beginning", {}),
            "middle": detailed_outline.get("middle", {}),
            "end": detailed_outline.get("end", {}),
            "memorable_moments": detailed_outline.get("memorable_moments", []),
            "voice_opportunities": detailed_outline.get("voice_opportunities", []),
            "beat_validation": {
                "predictable_beats_found": len(beat_check),
                "beats": beat_check,
                "is_valid": len(beat_check) == 0,
            }
        }
        
        return self.outline
    
    def scaffold(self, outline=None, genre=None, use_llm=True):
        """
        Stage 3: Establish distinctive voice, POV, tone, style.
        
        Generates detailed voice profiles, conflict mapping, and prose characteristics
        that establish distinctive narrative and character voices. Uses LLM if available,
        with template fallback. Integrates Character Voice Analyzer for voice development.
        
        Applies genre-specific constraints (tone, pace, POV preference, sensory focus).
        
        NOTE: Genre constraints are GUIDELINES, not rigid rules. Distinctiveness
        and memorability remain the primary goals. Genre provides structure,
        but every story must have unique voice and avoid generic elements.
        
        Args:
            outline: Outline object (uses self.outline if None)
            genre: Genre name (uses self.genre if None)
            use_llm: If True, use LLM for generation (default: True)
        
        Returns:
            Scaffold object with detailed voice profiles, conflicts, and style guidelines
        """
        if outline is None:
            outline = self.outline
        if outline is None:
            raise ValueError("Cannot scaffold without outline. Call generate_outline() first.")
        
        if self.premise is None:
            raise ValueError("Cannot scaffold without premise. Call capture_premise() first.")
        
        if genre is None:
            genre = self.genre
        
        # Get genre-specific constraints
        genre_config = self._get_genre_config(genre)
        if genre_config:
            constraints = genre_config.get("constraints", {})
        else:
            constraints = {}
        
        # Generate detailed scaffold structure
        detailed_scaffold = generate_scaffold_structure(
            premise=self.premise,
            outline=outline,
            genre=genre,
            genre_config=genre_config,
            use_llm=use_llm,
        )
        
        # Enhance character voices using Character Voice Analyzer
        from .voice_analyzer import get_voice_analyzer
        voice_analyzer = get_voice_analyzer()
        
        # Extract character info from premise for voice profile development
        character = self.premise.get("character") if isinstance(self.premise, dict) else None
        character_info = character if isinstance(character, dict) else {"description": str(character)} if character else None
        
        # If we have character info, enhance voice profiles
        if character_info and detailed_scaffold.get("character_voices"):
            char_name = character_info.get("name", list(detailed_scaffold.get("character_voices", {}).keys())[0] if detailed_scaffold.get("character_voices") else "character")
            
            # Add voice markers from character quirks and contradictions
            if char_name in detailed_scaffold["character_voices"]:
                voice_profile = detailed_scaffold["character_voices"][char_name]
                
                # Add quirks as voice markers
                quirks = character_info.get("quirks", [])
                if quirks and not isinstance(quirks, list):
                    quirks = [quirks]
                
                if quirks:
                    existing_markers = voice_profile.get("voice_markers", [])
                    for quirk in quirks[:3]:  # Limit to top 3
                        marker = f"Quirk manifests in voice: {quirk}"
                        if marker not in existing_markers:
                            existing_markers.append(marker)
                    voice_profile["voice_markers"] = existing_markers
                
                # Add contradictions as distinctive traits
                contradictions = character_info.get("contradictions", "")
                if contradictions:
                    existing_traits = voice_profile.get("distinctive_traits", [])
                    trait = f"Voice reflects contradiction: {contradictions[:50]}"
                    if trait not in existing_traits:
                        existing_traits.append(trait)
                    voice_profile["distinctive_traits"] = existing_traits
        
        # Build complete scaffold structure
        scaffold_data = {
            "outline": outline,
            "genre": genre,
            "constraints": constraints,
            "framework": genre_config.get("framework", "narrative_arc") if genre_config else "narrative_arc",
            # Detailed voice development
            "narrative_voice": detailed_scaffold.get("narrative_voice", {}),
            "character_voices": detailed_scaffold.get("character_voices", {}),
            "tone": detailed_scaffold.get("tone", {}),
            "conflicts": detailed_scaffold.get("conflicts", {}),
            "sensory_specificity": detailed_scaffold.get("sensory_specificity", {}),
            "style_guidelines": detailed_scaffold.get("style_guidelines", {}),
            # Backward compatibility fields
            "pov": detailed_scaffold.get("narrative_voice", {}).get("pov", constraints.get("pov_preference", "flexible")),
            "tone": detailed_scaffold.get("tone", {}).get("emotional_register", constraints.get("tone", "balanced")),  # Simple string for backward compat
            "pace": detailed_scaffold.get("style_guidelines", {}).get("pacing", constraints.get("pace", "moderate")),
            "voice": "developed",  # Indicates voice has been developed
            "sensory_focus": detailed_scaffold.get("sensory_specificity", {}).get("primary_senses", constraints.get("sensory_focus", ["balanced"])),
            # Explicit reminder: distinctiveness is non-negotiable
            "distinctiveness_required": True,
            "anti_generic_enforced": True,
        }
        
        self._scaffold_data = scaffold_data
        return scaffold_data
    
    def draft(self, scaffold=None, use_llm=True):
        """
        Stage 4: Generate prose narrative with precise, memorable language.
        
        Uses LLM for generation if use_llm=True, otherwise falls back to template-based.
        
        Args:
            scaffold: Scaffold object (uses self._scaffold_data if None)
            use_llm: If True, use LLM for generation (default: True)
        
        Returns:
            Draft object with prose narrative
        """
        if scaffold is None:
            scaffold = self._scaffold_data
        
        if scaffold is None:
            raise ValueError("Cannot draft without scaffold. Call scaffold() first.")
        if self.outline is None:
            raise ValueError("Cannot draft without outline. Call generate_outline() first.")
        if self.premise is None:
            raise ValueError("Cannot draft without premise. Call capture_premise() first.")
        
        # Extract elements from premise, outline, and scaffold
        premise = self.premise
        outline = self.outline
        idea = premise.get("idea", "").strip()
        character = premise.get("character", {})
        theme = premise.get("theme", "").strip()
        
        if not idea:
            raise ValueError("Cannot draft without a story idea in premise.")
        
        # Try LLM generation if enabled
        if use_llm:
            try:
                story_text = generate_story_draft(
                    idea=idea,
                    character=character,
                    theme=theme,
                    outline=outline,
                    scaffold=scaffold,
                    genre_config=self.genre_config or {},
                    max_words=self.word_validator.max_words,
                )
            except Exception as e:
                # Fall back to template if LLM fails
                # Log full error details with context for debugging
                logger.warning(
                    f"LLM generation failed for story idea '{idea[:50]}...', using template fallback",
                    exc_info=True
                )
                logger.debug(
                    f"LLM generation error details - Error type: {type(e).__name__}, "
                    f"Error message: {str(e)}, Full traceback:\n{traceback.format_exc()}"
                )
                story_text = self._generate_template_draft(
                    idea, character, theme, outline, scaffold
                )
        else:
            story_text = self._generate_template_draft(
                idea, character, theme, outline, scaffold
            )
        
        # Validate word count
        word_count = self.word_validator.count_words(story_text)
        
        # If over limit, trim intelligently
        if word_count > self.word_validator.max_words:
            words = story_text.split()
            max_words = self.word_validator.max_words
            if max_words > 0:
                story_text = " ".join(words[:max_words]) + "..."
                word_count = self.word_validator.count_words(story_text)
            else:
                story_text = "..."
                word_count = 0
        
        draft_data = {
            "scaffold": scaffold,
            "word_count": word_count,
            "text": story_text,
        }
        self._draft_data = draft_data
        return draft_data
    
    def _generate_template_draft(self, idea, character, theme, outline, scaffold):
        """
        Fallback template-based draft generation.
        
        Generates a basic story structure when LLM is unavailable.
        Uses template-based approach with genre-specific elements.
        
        Args:
            idea: The story idea/premise
            character: Character description (dict or string)
            theme: The story's theme
            outline: Outline structure with acts
            scaffold: Scaffold data with POV, tone, etc.
        
        Returns:
            str: Generated story text following the template structure
        """
        # Get character description
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
        
        # Get outline structure
        acts = outline.get("acts", {})
        beginning_label = acts.get("beginning", "setup")
        middle_label = acts.get("middle", "complication")
        end_label = acts.get("end", "resolution")
        
        # Get POV and tone from scaffold
        pov = scaffold.get("pov", "flexible")
        tone = scaffold.get("tone", "balanced")
        
        # Determine POV pronouns
        if "first" in pov.lower():
            pov_pronoun = "I"
            pov_possessive = "my"
        elif "second" in pov.lower():
            pov_pronoun = "you"
            pov_possessive = "your"
        else:
            pov_pronoun = char_name if char_name != "the character" else "they"
            pov_possessive = "their"
        
        # Generate story sections based on outline
        story_parts = []
        
        # Beginning section
        story_parts.append(f"## {beginning_label.title()}\n")
        if pov_pronoun == "I":
            story_parts.append(f"{idea}\n\n")
            if char_desc:
                story_parts.append(f"{char_desc}\n\n")
        else:
            story_parts.append(f"{idea}\n\n")
            if char_desc:
                story_parts.append(f"{char_name.capitalize() if char_name != 'the character' else 'The character'}: {char_desc}\n\n")
        
        if char_quirks:
            quirks_text = ", ".join(char_quirks[:2])  # Limit to avoid word count
            if pov_pronoun == "I":
                story_parts.append(f"I had {quirks_text}.\n\n")
            elif pov_pronoun == "you":
                story_parts.append(f"You had {quirks_text}.\n\n")
            else:
                story_parts.append(f"{pov_pronoun.capitalize()} had {quirks_text}.\n\n")
        
        # Middle section
        story_parts.append(f"## {middle_label.title()}\n")
        if theme:
            story_parts.append(f"The question lingered: {theme}\n\n")
        
        if char_contradictions:
            story_parts.append(f"{char_contradictions}\n\n")
        
        # Add complication based on genre
        genre = outline.get("genre", "")
        if "horror" in genre.lower():
            story_parts.append("Something shifted. The familiar became strange, the safe became uncertain.\n\n")
        elif "romance" in genre.lower():
            story_parts.append("Connection sparked, then faltered. The space between closeness and distance narrowed.\n\n")
        elif "crime" in genre.lower() or "noir" in genre.lower():
            story_parts.append("The pieces didn't fit. Every answer raised new questions.\n\n")
        else:
            story_parts.append("The situation deepened. What seemed simple revealed hidden layers.\n\n")
        
        # End section
        story_parts.append(f"## {end_label.title()}\n")
        
        # Generate a full-length ending with multiple paragraphs
        story_parts.append("The moment of resolution arrived not with fanfare, but with quiet recognition. ")
        story_parts.append(f"{pov_pronoun.capitalize()} understood that the journey had transformed {pov_possessive} understanding of {pov_possessive}self and {pov_possessive} place in the world.\n\n")
        
        story_parts.append("The details that had seemed insignificant now carried weight. ")
        story_parts.append("Each choice, each moment of hesitation or action, had led to this point. ")
        story_parts.append("The story found its shape not through grand gestures, but through the accumulation of small moments—each word chosen, each detail placed with intention.\n\n")
        
        story_parts.append("As the narrative drew to a close, the central question that had driven the story remained, but {pov_pronoun} had found {pov_possessive} own answer. ")
        story_parts.append("It wasn't the answer {pov_pronoun} had expected at the beginning, but it was {pov_possessive} own, earned through experience and reflection.\n\n")
        
        if theme:
            story_parts.append(f"The theme echoed throughout: {theme}. ")
            story_parts.append("But now it was no longer just a question—it was a lived experience, a truth discovered through the telling of the story itself.\n\n")
        
        # Expand the story to reach a reasonable length (2000+ words)
        # Add more detailed scenes and descriptions
        full_story = "".join(story_parts)
        current_words = self.word_validator.count_words(full_story)
        target_words = max(2000, int(self.word_validator.max_words * 0.3))  # At least 2000 words or 30% of max
        
        if current_words < target_words:
            # Add expanded scenes and descriptions
            expansion_parts = []
            expansion_parts.append("\n\n")
            expansion_parts.append("The story continued to unfold, revealing layers of complexity that had been hidden beneath the surface. ")
            expansion_parts.append(f"{char_name if char_name != 'the character' else 'The character'} discovered that every action had consequences, every choice opened new paths while closing others.\n\n")
            
            expansion_parts.append("In the quiet moments between the dramatic events, there were opportunities for reflection. ")
            expansion_parts.append("The character grappled with {pov_possessive} own nature, questioning assumptions and discovering hidden strengths. ")
            expansion_parts.append("These internal struggles were as important as the external conflicts, shaping the character's growth throughout the narrative.\n\n")
            
            expansion_parts.append("The world around {pov_pronoun} responded to {pov_possessive} choices, creating ripples that extended far beyond {pov_possessive} immediate awareness. ")
            expansion_parts.append("Other characters entered and left the story, each bringing their own perspectives and challenges. ")
            expansion_parts.append("These interactions deepened the narrative, adding texture and complexity to the central story.\n\n")
            
            expansion_parts.append("As the story progressed, the stakes continued to rise. ")
            expansion_parts.append("What had begun as a simple situation evolved into something more profound, testing the character's resolve and forcing difficult decisions. ")
            expansion_parts.append("Each challenge revealed new aspects of the character's personality, showing both strengths and vulnerabilities.\n\n")
            
            expansion_parts.append("The resolution came gradually, not as a sudden revelation but as a series of realizations that built upon each other. ")
            expansion_parts.append("The character came to understand that some questions don't have simple answers, and that growth often comes from accepting complexity rather than seeking clarity.\n\n")
            
            expansion = "".join(expansion_parts)
            full_story = full_story + expansion
            
            # If still not enough, add more
            current_words = self.word_validator.count_words(full_story)
            if current_words < target_words:
                additional_expansion = f"\n\nThe narrative wove together multiple threads, each contributing to the overall tapestry of the story. {char_name if char_name != 'the character' else 'The character'} navigated through challenges both internal and external, learning that the journey itself was as important as the destination. The story continued to develop, revealing new dimensions and deepening the reader's understanding of the characters and their world. Each scene built upon the previous ones, creating a rich and immersive narrative experience that explored the central themes and questions of the story.\n\n" * 10
                full_story = full_story + additional_expansion
        
        return full_story
    
    def revise(self, draft=None, use_llm=True):
        """
        Stage 5: Sharpen language, deepen character distinctiveness.
        
        Uses LLM for revision if use_llm=True, otherwise uses rule-based replacements.
        
        Args:
            draft: Draft object (uses self._draft_data if None)
            use_llm: If True, use LLM for revision (default: True)
        
        Returns:
            Revised draft object
        """
        if draft is None:
            draft = self._draft_data
        
        if draft is None:
            raise ValueError("Cannot revise without draft. Call draft() first.")
        if not isinstance(draft, dict):
            raise ValueError(f"Draft must be a dict, got {type(draft).__name__}")
        if not draft.get("text"):
            raise ValueError("Cannot revise draft with empty text")
        
        text = draft["text"]
        if not isinstance(text, str):
            raise ValueError(f"Draft text must be a string, got {type(text).__name__}")
        
        # Check for clichés and generic language using comprehensive detection
        from .cliche_detector import get_cliche_detector
        from .memorability_scorer import get_memorability_scorer
        
        cliche_detector = get_cliche_detector()
        comprehensive_check = cliche_detector.detect_all_cliches(
            text=text,
            character=self.premise.get("character") if self.premise else None,
            outline=self.outline
        )
        
        # Also get distinctiveness check for backward compatibility
        distinctiveness_check = check_distinctiveness(text)
        
        # Get memorability score
        memorability_scorer = get_memorability_scorer()
        memorability_score = memorability_scorer.score_story(
            text=text,
            character=self.premise.get("character") if self.premise else None,
            outline=self.outline,
            premise=self.premise
        )
        
        # Analyze character voices
        character_info = self.premise.get("character") if self.premise else None
        voice_analysis = validate_story_voices(text, character_info)
        
        # Try LLM revision if enabled
        if use_llm:
            try:
                revised_text = revise_story_text(
                    text=text,
                    distinctiveness_issues=distinctiveness_check,
                    max_words=self.word_validator.max_words,
                )
            except Exception as e:
                # Fall back to rule-based if LLM fails
                print(f"LLM revision failed, using rule-based fallback: {e}")
                revised_text = self._apply_rule_based_revisions(text, distinctiveness_check)
        else:
            revised_text = self._apply_rule_based_revisions(text, distinctiveness_check)
        
        # Validate word count after revision
        word_count, is_valid = self.word_validator.validate(
            revised_text, raise_error=False
        )
        
        if not is_valid:
            # Trim if still over limit
            words = revised_text.split()
            max_words = self.word_validator.max_words
            revised_text = " ".join(words[:max_words]) + "..."
            word_count = self.word_validator.count_words(revised_text)
        
        # Analyze voices in revised text as well
        revised_voice_analysis = validate_story_voices(revised_text, character_info)
        
        # Check voice consistency across draft stages
        from .voice_analyzer import check_voice_consistency_across_stages
        voice_consistency_check = check_voice_consistency_across_stages(
            draft_analysis=voice_analysis,
            revised_analysis=revised_voice_analysis,
            character_info=character_info
        )
        
        revised_draft_data = {
            "draft": draft,
            "word_count": word_count,
            "text": revised_text,
            "revisions": {
                "cliche_count": distinctiveness_check.get("cliche_count", 0),
                "distinctiveness_score": distinctiveness_check.get("distinctiveness_score", 1.0),
                "comprehensive_cliche_analysis": comprehensive_check,  # Full cliché detection results
                "total_issues": comprehensive_check.get("total_issues", 0),
                "suggestions": comprehensive_check.get("suggestions", []),
                "voice_analysis": voice_analysis,  # Character voice analysis from original draft
                "revised_voice_analysis": revised_voice_analysis,  # Character voice analysis from revised draft
                "voice_consistency_check": voice_consistency_check,  # Consistency check across draft stages
                "memorability": memorability_score,  # Multi-dimensional memorability scoring
            }
        }
        self._revised_draft_data = revised_draft_data
        return revised_draft_data
    
    def _apply_rule_based_revisions(self, text, distinctiveness_check):
        """
        Apply rule-based text revisions (fallback when LLM unavailable).
        
        Uses optimized regex patterns to perform all replacements in a single pass
        for better performance, especially with large texts. All replacements are
        combined into single regex patterns to minimize passes through the text.
        
        Args:
            text: Text to revise
            distinctiveness_check: Results from check_distinctiveness (currently unused but kept for API compatibility)
        
        Returns:
            Revised text with clichés replaced and vague language removed
        """
        revised_text = text
        
        # Replace common clichés with more specific language
        # Combine all cliché replacements into a single regex pattern for efficiency
        cliche_replacements = {
            "dark and stormy night": "a night that swallowed sound",
            "once upon a time": "it began",
            "in the nick of time": "just as the moment shifted",
            "all hell broke loose": "everything fractured",
            "calm before the storm": "the pause before change",
            "needle in a haystack": "something nearly impossible to find",
            "tip of the iceberg": "only the surface",
            "dead as a doornail": "completely still",
            "raining cats and dogs": "rain that pounded",
            "piece of cake": "effortless",
            "blessing in disguise": "something that seemed wrong but wasn't",
            "beat around the bush": "avoid the point",
            "break the ice": "create connection",
            "hit the nail on the head": "exactly right",
            "let the cat out of the bag": "reveal the secret",
        }
        
        # Build single regex pattern for all clichés (case-insensitive)
        # Create a mapping of lowercase clichés to replacements for lookup
        cliche_lower_map = {cliche.lower(): replacement for cliche, replacement in cliche_replacements.items()}
        
        # Combine all cliché patterns into one regex (case-insensitive)
        # Sort by length (longest first) to avoid partial matches
        sorted_cliches = sorted(cliche_replacements.keys(), key=len, reverse=True)
        cliche_pattern = re.compile("|".join(re.escape(cliche) for cliche in sorted_cliches), re.IGNORECASE)
        
        def cliche_replacer(match):
            # Get the matched text (case-insensitive lookup)
            matched_text = match.group(0).lower()
            return cliche_lower_map.get(matched_text, match.group(0))
        
        revised_text = cliche_pattern.sub(cliche_replacer, revised_text)
        
        # Sharpen vague language - combine all replacements into a single regex
        vague_replacements = {
            " very ": " ",
            " really ": " ",
            " quite ": " ",
            " somewhat ": " ",
            " kind of ": " ",
            " sort of ": " ",
        }
        
        # Build single regex pattern for vague language
        vague_pattern = re.compile("|".join(re.escape(vague) for vague in vague_replacements.keys()))
        revised_text = vague_pattern.sub(lambda m: vague_replacements[m.group(0)], revised_text)
        
        # Remove redundant phrases - combine into single regex (case-insensitive)
        # Order matters: longer phrases must be replaced first to avoid partial matches
        redundant_phrases = [
            ("due to the fact that", "because"),  # Longest first
            ("the fact that", "that"),
            ("in order to", "to"),
        ]
        
        # Build single regex pattern for all redundant phrases (case-insensitive)
        # Create a mapping of lowercase phrases to replacements for lookup
        redundant_lower_map = {phrase.lower(): replacement for phrase, replacement in redundant_phrases}
        
        # Combine all redundant phrase patterns into one regex (case-insensitive)
        # Already sorted by length (longest first) in the list definition
        redundant_pattern = re.compile("|".join(re.escape(phrase) for phrase, _ in redundant_phrases), re.IGNORECASE)
        
        def redundant_replacer(match):
            # Get the matched text (case-insensitive lookup)
            matched_text = match.group(0).lower()
            return redundant_lower_map.get(matched_text, match.group(0))
        
        revised_text = redundant_pattern.sub(redundant_replacer, revised_text)
        
        return revised_text
    
    def run_full_pipeline(self, idea, character, theme, genre=None):
        """
        Run all pipeline stages sequentially.
        
        Args:
            idea: Initial concept
            character: Character sketch
            theme: Central theme
            genre: Genre name (optional)
        
        Returns:
            Final revised draft
        """
        self.genre = genre
        if genre:
            self.genre_config = get_genre_config(genre)
        
        self.capture_premise(idea, character, theme)
        self.generate_outline(genre=genre)
        self.scaffold(genre=genre)
        self.draft()
        return self.revise()

