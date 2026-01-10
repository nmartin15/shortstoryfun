"""
Cliché detection module.

See CONCEPTS.md for definitions of cliché detection requirements.
The ClicheDetector class provides the main interface for cliché detection.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


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
        # Common phrase clichés
        self.phrase_cliches = [
            "it was a dark and stormy night",
            "once upon a time",
            "little did they know",
            "in that moment",
            "her heart pounded",
            "his eyes widened",
            "time seemed to stand still",
            "it was then that",
            "without warning",
            "out of nowhere"
        ]
        
        # Predictable story beats
        self.story_beats_patterns = [
            {"beat": "call to adventure", "alternatives": ["unexpected summons", "reluctant discovery"]},
            {"beat": "hero's journey", "alternatives": ["subverted expectations", "non-linear progression"]},
        ]
        
        # Plot structure patterns
        self.plot_structures_patterns = [
            {"structure": ["setup", "conflict", "resolution"], "alternatives": ["complex narrative", "multi-threaded"]},
        ]
    
    def detect_all_cliches(
        self,
        text: Optional[str] = None,
        character: Optional[Dict] = None,
        outline: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive cliché detection across text, character, and outline.
        
        Args:
            text: Story text to analyze
            character: Character description dict
            outline: Story outline dict
            
        Returns:
            Dict with detection results:
            {
                "phrase_cliches": List[Dict],
                "character_archetypes": List[Dict],
                "predictable_beats": List[Dict],
                "plot_structures": List[Dict],
                "has_cliches": bool,
                "total_cliches": int
            }
        """
        results = {
            "phrase_cliches": [],
            "character_archetypes": [],
            "predictable_beats": [],
            "plot_structures": [],
            "has_cliches": False,
            "total_cliches": 0
        }
        
        # Detect phrase clichés in text
        if text and isinstance(text, str):
            text_lower = text.lower()
            for cliche in self.phrase_cliches:
                if cliche in text_lower:
                    results["phrase_cliches"].append({
                        "phrase": cliche,
                        "suggestion": f"Replace '{cliche}' with something more original"
                    })
        
        # Detect character archetypes
        if character:
            char_desc = character.get("description", "") if isinstance(character, dict) else str(character)
            char_desc_lower = char_desc.lower()
            
            archetypes = ["chosen one", "destined hero", "reluctant hero", "wise old mentor"]
            for archetype in archetypes:
                if archetype in char_desc_lower:
                    results["character_archetypes"].append({
                        "archetype": archetype,
                        "suggestion": f"Add unique traits to move beyond '{archetype}' archetype"
                    })
        
        # Detect predictable beats in outline
        if outline:
            outline_text = str(outline)
            beat_check = self._detect_predictable_beats(outline_text)
            if beat_check:
                results["predictable_beats"].extend(beat_check)
        
        # Calculate totals
        results["total_cliches"] = (
            len(results["phrase_cliches"]) +
            len(results["character_archetypes"]) +
            len(results["predictable_beats"]) +
            len(results["plot_structures"])
        )
        results["has_cliches"] = results["total_cliches"] > 0
        
        return results
    
    def _detect_predictable_beats(self, outline_text: str) -> List[Dict]:
        """
        Detect predictable story beats in outline text.
        
        Args:
            outline_text: Text representation of outline
            
        Returns:
            List of detected beat patterns
        """
        outline_lower = outline_text.lower()
        detected = []
        
        for pattern in self.story_beats_patterns:
            beat = pattern["beat"]
            if beat in outline_lower:
                detected.append({
                    "beat": beat,
                    "alternatives": pattern["alternatives"],
                    "suggestion": f"Consider alternatives to '{beat}': {', '.join(pattern['alternatives'])}"
                })
        
        return detected
    
    def suggest_replacements(self, cliche: Optional[str] = None) -> List[str]:
        """
        Suggest replacements for a detected cliché.
        
        Args:
            cliche: The cliché phrase to get replacements for
            
        Returns:
            List of suggested replacement phrases
        """
        if not cliche:
            return [
                "Use specific, concrete language",
                "Focus on unique character details",
                "Avoid stock phrases and predictable patterns"
            ]
        
        cliche_lower = cliche.lower()
        
        # Check phrase clichés
        for phrase in self.phrase_cliches:
            if phrase in cliche_lower:
                return [
                    f"Replace '{phrase}' with a more specific description",
                    "Use concrete sensory details instead",
                    "Focus on what makes this moment unique"
                ]
        
        # Check story beats
        for pattern in self.story_beats_patterns:
            if pattern["beat"] in cliche_lower:
                return pattern["alternatives"]
        
        # Generic suggestions
        return [
            "Use more specific language",
            "Focus on unique details",
            "Avoid generic phrasing"
        ]
    
    def apply_replacements(
        self,
        text: str,
        replacements: Dict[str, str]
    ) -> str:
        """
        Apply replacement suggestions to text.
        
        Args:
            text: Original text
            replacements: Dict mapping clichés to replacements
            
        Returns:
            Text with replacements applied
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text).__name__}")
        
        if not isinstance(replacements, dict):
            raise TypeError(f"replacements must be a dict, got {type(replacements).__name__}")
        
        result = text
        for cliche, replacement in replacements.items():
            if not isinstance(replacement, str):
                raise TypeError(f"Replacement for '{cliche}' must be a string, got {type(replacement).__name__}")
            result = result.replace(cliche, replacement)
        
        return result


# Singleton instance
_cliche_detector_instance: Optional[ClicheDetector] = None


def get_cliche_detector() -> ClicheDetector:
    """
    Get the singleton ClicheDetector instance.
    
    Returns:
        ClicheDetector instance
    """
    global _cliche_detector_instance
    if _cliche_detector_instance is None:
        _cliche_detector_instance = ClicheDetector()
    return _cliche_detector_instance
