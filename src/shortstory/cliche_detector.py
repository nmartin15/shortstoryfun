"""
Cliché Detection System

Comprehensive system for detecting and suggesting replacements for:
- Generic phrases and stock descriptions
- Predictable story beats
- Archetypal character traits
- Formulaic plot structures

See CONCEPTS.md for definitions of cliché detection requirements.
"""

from typing import Dict, List, Optional, Tuple
import re

from .utils.validation import (
    detect_cliches,
    detect_generic_archetypes,
    CLICHE_PATTERNS,
    ARCHETYPE_PATTERNS,
)

# Import private function for generic pattern detection
# Note: This is a private function, but we need it for comprehensive detection
from .utils.validation import _detect_generic_patterns


# Enhanced replacement suggestions for clichés
# Format: (cliche_phrase, [replacement_options], context_notes)
CLICHE_REPLACEMENTS = {
    "dark and stormy night": [
        "a night that swallowed sound",
        "a night without stars or moon",
        "a night that pressed down",
    ],
    "once upon a time": [
        "it began",
        "the story starts",
        "in the beginning",
    ],
    "in the nick of time": [
        "just as the moment shifted",
        "at the last possible instant",
        "when all seemed lost",
    ],
    "all hell broke loose": [
        "everything fractured",
        "chaos erupted",
        "the situation unraveled",
    ],
    "calm before the storm": [
        "the pause before change",
        "a deceptive stillness",
        "the quiet that precedes",
    ],
    "needle in a haystack": [
        "something nearly impossible to find",
        "a search with no clear path",
        "finding what shouldn't be found",
    ],
    "tip of the iceberg": [
        "only the surface",
        "the visible part of something larger",
        "what showed above the waterline",
    ],
    "dead as a doornail": [
        "completely still",
        "without life or movement",
        "utterly motionless",
    ],
    "raining cats and dogs": [
        "rain that pounded",
        "a deluge that soaked everything",
        "water falling in sheets",
    ],
    "piece of cake": [
        "effortless",
        "without difficulty",
        "easily accomplished",
    ],
    "blessing in disguise": [
        "something that seemed wrong but wasn't",
        "a gift wrapped in difficulty",
        "good fortune in unexpected form",
    ],
    "beat around the bush": [
        "avoid the point",
        "speak without saying",
        "circle the truth",
    ],
    "break the ice": [
        "create connection",
        "find common ground",
        "begin the conversation",
    ],
    "hit the nail on the head": [
        "exactly right",
        "precisely correct",
        "the truth of it",
    ],
    "let the cat out of the bag": [
        "reveal the secret",
        "expose what was hidden",
        "speak the truth that shouldn't be spoken",
    ],
}

# Predictable story beats (formulaic plot structures)
PREDICTABLE_BEATS = [
    # Hero's journey patterns
    ("the call to adventure", ["unexpected invitation", "chance encounter", "sudden opportunity"]),
    ("refusal of the call", ["initial hesitation", "doubts surface", "resistance to change"]),
    ("meeting the mentor", ["wise guide appears", "teacher arrives", "elder provides wisdom"]),
    ("crossing the threshold", ["entering new world", "leaving comfort zone", "taking the leap"]),
    ("the ordeal", ["greatest challenge", "ultimate test", "final confrontation"]),
    ("the reward", ["victory achieved", "goal reached", "prize obtained"]),
    ("the return", ["coming home", "back to beginning", "full circle"]),
    
    # Romance patterns
    ("love at first sight", ["instant connection", "immediate attraction", "spark between them"]),
    ("misunderstanding drives them apart", ["conflict separates", "miscommunication divides", "wrong assumption creates distance"]),
    ("grand gesture wins them back", ["dramatic declaration", "profound act of love", "ultimate proof of feeling"]),
    
    # Mystery patterns
    ("red herring", ["false clue", "misleading evidence", "distraction from truth"]),
    ("the butler did it", ["obvious suspect", "too convenient solution", "predictable reveal"]),
    ("twist ending", ["unexpected conclusion", "surprise resolution", "revelation changes everything"]),
    
    # Horror patterns
    ("the jump scare", ["sudden appearance", "unexpected moment", "moment of shock"]),
    ("it was all a dream", ["waking from nightmare", "reality returns", "illusion fades"]),
    ("the final girl", ["last one standing", "sole survivor", "one who endures"]),
]

# Formulaic plot structures
FORMULAIC_PLOTS = [
    # Three-act structure (too rigid)
    ("setup, conflict, resolution", ["beginning, middle, end with unexpected turns"]),
    ("boy meets girl, boy loses girl, boy gets girl", ["connection, separation, reunion with complications"]),
    
    # Quest patterns
    ("find the magical object", ["search for something important", "quest for meaning", "journey toward understanding"]),
    ("defeat the evil villain", ["overcome the antagonist", "face the opposition", "confront the challenge"]),
    
    # Coming of age
    ("innocent youth learns harsh truth", ["naive character gains wisdom", "sheltered person faces reality", "protected individual discovers complexity"]),
]


class ClicheDetector:
    """
    Comprehensive cliché detection system.
    
    Detects and suggests replacements for:
    - Generic phrases and stock descriptions
    - Predictable story beats
    - Archetypal character traits
    - Formulaic plot structures
    """
    
    def __init__(self):
        """Initialize the cliché detector."""
        self.cliche_replacements = CLICHE_REPLACEMENTS
        self.predictable_beats = PREDICTABLE_BEATS
        self.formulaic_plots = FORMULAIC_PLOTS
    
    def detect_all_cliches(
        self,
        text: str,
        character: Optional[Dict] = None,
        outline: Optional[Dict] = None
    ) -> Dict:
        """
        Comprehensive cliché detection across all categories.
        
        Args:
            text: Story text to analyze
            character: Character description (optional)
            outline: Story outline (optional, for beat detection)
        
        Returns:
            Dict with comprehensive detection results:
            {
                "phrase_cliches": dict,  # From detect_cliches()
                "archetype_cliches": dict,  # From detect_generic_archetypes()
                "generic_patterns": list,  # From _detect_generic_patterns()
                "predictable_beats": list,  # Detected story beats
                "formulaic_plots": list,  # Detected plot structures
                "total_issues": int,
                "suggestions": list[str]
            }
        """
        results = {
            "phrase_cliches": {},
            "archetype_cliches": {},
            "generic_patterns": [],
            "predictable_beats": [],
            "formulaic_plots": [],
            "total_issues": 0,
            "suggestions": [],
        }
        
        # Detect phrase clichés
        if text:
            results["phrase_cliches"] = detect_cliches(text)
            results["generic_patterns"] = _detect_generic_patterns(text, text.lower())
        
        # Detect archetype clichés
        if character:
            results["archetype_cliches"] = detect_generic_archetypes(character)
        
        # Detect predictable story beats
        if text:
            results["predictable_beats"] = self._detect_predictable_beats(text)
        
        # Detect formulaic plot structures
        if outline:
            results["formulaic_plots"] = self._detect_formulaic_plots(outline)
        elif text:
            # Try to infer from text if outline not provided
            results["formulaic_plots"] = self._detect_formulaic_plots_from_text(text)
        
        # Calculate total issues
        results["total_issues"] = (
            results["phrase_cliches"].get("cliche_count", 0) +
            len(results["archetype_cliches"].get("generic_elements", [])) +
            len(results["generic_patterns"]) +
            len(results["predictable_beats"]) +
            len(results["formulaic_plots"])
        )
        
        # Generate suggestions
        results["suggestions"] = self._generate_replacement_suggestions(results)
        
        return results
    
    def _detect_predictable_beats(self, text: str) -> List[Dict]:
        """
        Detect predictable story beats in text.
        
        Args:
            text: Story text to analyze
        
        Returns:
            List of detected beats with context
        """
        detected = []
        text_lower = text.lower()
        
        for beat_phrase, alternatives in self.predictable_beats:
            # Check for beat phrase with word boundaries
            pattern = r'\b' + re.escape(beat_phrase) + r'\b'
            matches = list(re.finditer(pattern, text_lower))
            
            for match in matches:
                start, end = match.span()
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end]
                
                detected.append({
                    "beat": beat_phrase,
                    "position": start,
                    "context": context,
                    "alternatives": alternatives,
                })
        
        return detected
    
    def _detect_formulaic_plots(self, outline: Dict) -> List[Dict]:
        """
        Detect formulaic plot structures in outline.
        
        Args:
            outline: Story outline structure
        
        Returns:
            List of detected formulaic patterns
        """
        detected = []
        
        # Check outline structure
        acts = outline.get("acts", {})
        structure = outline.get("structure", [])
        
        # Convert to string for pattern matching
        structure_str = " ".join([str(v) for v in acts.values()] + structure).lower()
        
        for plot_pattern, alternatives in self.formulaic_plots:
            if plot_pattern.lower() in structure_str:
                detected.append({
                    "pattern": plot_pattern,
                    "alternatives": alternatives,
                    "location": "outline_structure",
                })
        
        return detected
    
    def _detect_formulaic_plots_from_text(self, text: str) -> List[Dict]:
        """
        Attempt to detect formulaic plots from text (less reliable than outline).
        
        Args:
            text: Story text to analyze
        
        Returns:
            List of detected formulaic patterns
        """
        detected = []
        text_lower = text.lower()
        
        # Look for key phrases that suggest formulaic plots
        for plot_pattern, alternatives in self.formulaic_plots:
            # Check if pattern appears in text
            if plot_pattern.lower() in text_lower:
                detected.append({
                    "pattern": plot_pattern,
                    "alternatives": alternatives,
                    "location": "text_content",
                    "confidence": "low",  # Less reliable from text alone
                })
        
        return detected
    
    def _generate_replacement_suggestions(self, results: Dict) -> List[str]:
        """
        Generate actionable replacement suggestions from detection results.
        
        Args:
            results: Detection results from detect_all_cliches()
        
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Phrase cliché suggestions
        phrase_cliches = results.get("phrase_cliches", {})
        if phrase_cliches.get("has_cliches"):
            found = phrase_cliches.get("found_cliches", [])
            count = phrase_cliches.get("cliche_count", 0)
            suggestions.append(
                f"Found {count} clichéd phrase(s): {', '.join(found[:3])}. "
                "Consider replacing with more specific, vivid language."
            )
        
        # Archetype suggestions
        archetype_cliches = results.get("archetype_cliches", {})
        if archetype_cliches.get("has_generic_archetype"):
            elements = archetype_cliches.get("generic_elements", [])
            suggestions.append(
                f"Character shows generic archetype traits: {', '.join(elements)}. "
                "Add unique quirks, contradictions, or specific details to make them distinctive."
            )
        
        # Generic pattern suggestions
        generic_patterns = results.get("generic_patterns", [])
        if generic_patterns:
            pattern_types = {}
            for pattern in generic_patterns:
                ptype = pattern.get("type", "unknown")
                pattern_types[ptype] = pattern_types.get(ptype, 0) + 1
            
            for ptype, count in pattern_types.items():
                suggestions.append(
                    f"Found {count} instance(s) of {ptype.replace('_', ' ')}. "
                    "Replace with more specific language."
                )
        
        # Predictable beat suggestions
        predictable_beats = results.get("predictable_beats", [])
        if predictable_beats:
            unique_beats = set(b["beat"] for b in predictable_beats)
            suggestions.append(
                f"Found {len(predictable_beats)} predictable story beat(s): {', '.join(list(unique_beats)[:3])}. "
                "Consider subverting expectations or adding unexpected complications."
            )
        
        # Formulaic plot suggestions
        formulaic_plots = results.get("formulaic_plots", [])
        if formulaic_plots:
            patterns = [p["pattern"] for p in formulaic_plots]
            suggestions.append(
                f"Story follows formulaic plot structure: {', '.join(patterns[:2])}. "
                "Consider adding unexpected turns or subverting the expected pattern."
            )
        
        return suggestions
    
    def suggest_replacements(self, cliche_phrase: str, context: Optional[str] = None) -> List[str]:
        """
        Get replacement suggestions for a specific cliché phrase.
        
        Args:
            cliche_phrase: The cliché phrase to replace
            context: Optional context to help choose better replacement
        
        Returns:
            List of replacement suggestions (best first)
        """
        # Normalize phrase
        phrase_lower = cliche_phrase.lower()
        
        # Check exact match
        if phrase_lower in self.cliche_replacements:
            return self.cliche_replacements[phrase_lower]
        
        # Check if it's a variation of a known cliché
        for known_cliche, replacements in self.cliche_replacements.items():
            if known_cliche in phrase_lower or phrase_lower in known_cliche:
                return replacements
        
        # Check CLICHE_PATTERNS for variations
        for base_phrase, variations, _ in CLICHE_PATTERNS:
            if base_phrase in phrase_lower:
                # Return replacements if available, otherwise generate generic suggestion
                if base_phrase in self.cliche_replacements:
                    return self.cliche_replacements[base_phrase]
                return [f"Replace '{cliche_phrase}' with more specific language"]
        
        # No specific replacement found
        return [f"Replace '{cliche_phrase}' with more specific, vivid language"]
    
    def apply_replacements(
        self,
        text: str,
        replacements: Optional[Dict[str, str]] = None,
        auto_replace: bool = False
    ) -> Tuple[str, List[Dict]]:
        """
        Apply cliché replacements to text.
        
        Args:
            text: Text to revise
            replacements: Optional dict of {cliche: replacement} to use
            auto_replace: If True, automatically use best suggestions
        
        Returns:
            Tuple of (revised_text, applied_replacements)
            applied_replacements is list of {original, replacement, position}
        """
        if not text:
            return text, []
        
        revised_text = text
        applied = []
        
        # Detect clichés
        cliche_results = detect_cliches(text)
        found_cliches = cliche_results.get("found_cliches", [])
        
        if not found_cliches:
            return text, []
        
        # Build replacement map
        replacement_map = replacements or {}
        
        if auto_replace and not replacement_map:
            # Auto-generate replacements
            for cliche in found_cliches:
                suggestions = self.suggest_replacements(cliche)
                if suggestions:
                    replacement_map[cliche] = suggestions[0]  # Use first (best) suggestion
        
        # Apply replacements (longest first to avoid partial matches)
        sorted_cliches = sorted(replacement_map.keys(), key=len, reverse=True)
        
        for cliche in sorted_cliches:
            if cliche in replacement_map:
                replacement = replacement_map[cliche]
                # Use word boundaries for safe replacement
                pattern = re.compile(r'\b' + re.escape(cliche) + r'\b', re.IGNORECASE)
                
                def replacer(match):
                    applied.append({
                        "original": match.group(0),
                        "replacement": replacement,
                        "position": match.start(),
                    })
                    return replacement
                
                revised_text = pattern.sub(replacer, revised_text)
        
        return revised_text, applied


def get_cliche_detector() -> ClicheDetector:
    """
    Get or create a singleton cliché detector instance.
    
    Returns:
        ClicheDetector instance
    """
    global _detector_instance
    if '_detector_instance' not in globals():
        _detector_instance = ClicheDetector()
    return _detector_instance

