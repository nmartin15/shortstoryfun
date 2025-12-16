"""
ShortStoryPipeline - Main pipeline class

See pipeline.md for architecture documentation.
See CONCEPTS.md for core principles and terminology.
"""

from .utils import WordCountValidator, check_distinctiveness, validate_premise
from .genres import get_genre_config


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
        self.scaffold = None
        self.draft = None
        self.revised_draft = None
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
    
    def generate_outline(self, premise=None, genre=None):
        """
        Stage 2: Generate outline with unexpected beats.
        
        Args:
            premise: Premise object (uses self.premise if None)
            genre: Genre name (uses self.genre if None)
        
        Returns:
            Outline object with beginning, middle, end following genre structure
        """
        if premise is None:
            premise = self.premise
        if genre is None:
            genre = self.genre
        
        # Get genre-specific outline structure
        if genre:
            genre_config = get_genre_config(genre)
            outline_structure = genre_config.get("outline", ["setup", "complication", "resolution"])
            framework = genre_config.get("framework", "narrative_arc")
        else:
            outline_structure = ["setup", "complication", "resolution"]
            framework = "narrative_arc"
        
        # TODO: Implement full outline generation with genre structure
        self.outline = {
            "premise": premise,
            "genre": genre,
            "framework": framework,
            "structure": outline_structure,
            "acts": {
                "beginning": outline_structure[0] if len(outline_structure) > 0 else "setup",
                "middle": outline_structure[1] if len(outline_structure) > 1 else "complication",
                "end": outline_structure[2] if len(outline_structure) > 2 else "resolution"
            }
        }
        return self.outline
    
    def scaffold(self, outline=None, genre=None):
        """
        Stage 3: Establish distinctive voice, POV, tone, style.
        
        Applies genre-specific constraints (tone, pace, POV preference, sensory focus).
        
        NOTE: Genre constraints are GUIDELINES, not rigid rules. Distinctiveness
        and memorability remain the primary goals. Genre provides structure,
        but every story must have unique voice and avoid generic elements.
        
        Args:
            outline: Outline object (uses self.outline if None)
            genre: Genre name (uses self.genre if None)
        
        Returns:
            Scaffold object with POV, tone, style, voice profiles based on genre
        """
        if outline is None:
            outline = self.outline
        if genre is None:
            genre = self.genre
        
        # Get genre-specific constraints
        if genre:
            genre_config = get_genre_config(genre)
            constraints = genre_config.get("constraints", {})
        else:
            constraints = {}
        
        # TODO: Implement full scaffolding with voice development
        # Genre constraints are starting points - voice must still be DISTINCTIVE
        # All stories must pass distinctiveness validation regardless of genre
        self.scaffold = {
            "outline": outline,
            "genre": genre,
            "constraints": constraints,
            "pov": constraints.get("pov_preference", "flexible"),
            "tone": constraints.get("tone", "balanced"),
            "pace": constraints.get("pace", "moderate"),
            "voice": constraints.get("voice", "balanced"),
            "sensory_focus": constraints.get("sensory_focus", ["balanced"]),
            # Explicit reminder: distinctiveness is non-negotiable
            "distinctiveness_required": True,
            "anti_generic_enforced": True,
        }
        return self.scaffold
    
    def draft(self, scaffold=None):
        """
        Stage 4: Generate prose narrative with precise, memorable language.
        
        Args:
            scaffold: Scaffold object (uses self.scaffold if None)
        
        Returns:
            Draft object with prose narrative
        """
        # TODO: Implement drafting with anti-generic filters
        if scaffold is None:
            scaffold = self.scaffold
        # Placeholder
        # Placeholder - will validate word count when implemented
        self.draft = {
            "scaffold": scaffold,
            "word_count": 0,
            "text": "",  # Will contain prose when implemented
        }
        return self.draft
    
    def revise(self, draft=None):
        """
        Stage 5: Sharpen language, deepen character distinctiveness.
        
        Args:
            draft: Draft object (uses self.draft if None)
        
        Returns:
            Revised draft object
        """
        # TODO: Implement revision with cliché elimination
        if draft is None:
            draft = self.draft
        
        # Validate word count on revision
        if draft.get("text"):
            word_count, is_valid = self.word_validator.validate(
                draft["text"], raise_error=False
            )
            if not is_valid:
                # Log warning but don't fail - revision stage should fix this
                print(
                    f"Warning: Draft exceeds word count ({word_count} > "
                    f"{self.word_validator.max_words})"
                )
        
        # Placeholder
        self.revised_draft = {
            "draft": draft,
            "word_count": draft.get("word_count", 0),
            "text": draft.get("text", ""),
        }
        return self.revised_draft
    
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

