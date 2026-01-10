"""
Memorability Scorer

Builds on the validation refactoring to score distinctiveness across multiple dimensions
and provide actionable improvement suggestions.

See CONCEPTS.md for definitions of memorability requirements.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .utils.validation import (
    detect_cliches,
    detect_generic_archetypes,
    calculate_distinctiveness_score,
    detect_generic_patterns_from_text,
)
from .cliche_detector import get_cliche_detector


@dataclass
class DimensionScore:
    """Score for a single memorability dimension."""
    name: str
    score: float  # 0.0 to 1.0, higher = better
    max_score: float = 1.0
    issues: List[Dict] = None
    strengths: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.strengths is None:
            self.strengths = []


class MemorabilityScorer:
    """
    Scores story memorability across multiple dimensions.
    
    Dimensions:
    1. Language Precision - Clichés, generic patterns, vague language
    2. Character Uniqueness - Archetypes, generic traits, lack of quirks
    3. Voice Strength - Narrative voice distinctiveness, character voice consistency
    4. Beat Originality - Predictable beats, formulaic plot structures
    """
    
    # Dimension weights for overall score calculation
    DIMENSION_WEIGHTS = {
        "language_precision": 0.30,
        "character_uniqueness": 0.25,
        "voice_strength": 0.25,
        "beat_originality": 0.20,
    }
    
    # Thresholds for dimension scores
    EXCELLENT_THRESHOLD = 0.85
    GOOD_THRESHOLD = 0.70
    NEEDS_IMPROVEMENT_THRESHOLD = 0.50
    
    def __init__(self):
        """Initialize the memorability scorer."""
        self.cliche_detector = get_cliche_detector()
    
    def score_story(
        self,
        text: str,
        character: Optional[Dict] = None,
        outline: Optional[Dict] = None,
        premise: Optional[Dict] = None
    ) -> Dict:
        """
        Score story memorability across all dimensions.
        
        Args:
            text: Story text to analyze
            character: Character description (optional)
            outline: Story outline (optional, for beat detection)
            premise: Premise object (optional, for context)
        
        Returns:
            Dict with comprehensive scoring results:
            {
                "overall_score": float,  # 0.0-1.0, weighted average
                "dimensions": {
                    "language_precision": DimensionScore,
                    "character_uniqueness": DimensionScore,
                    "voice_strength": DimensionScore,
                    "beat_originality": DimensionScore,
                },
                "prioritized_suggestions": List[str],
                "summary": str,
                "detailed_analysis": Dict
            }
        """
        # Normalize inputs
        if not text:
            text = ""
        if not isinstance(text, str):
            text = str(text)
        
        # Score each dimension
        language_score = self._score_language_precision(text)
        character_score = self._score_character_uniqueness(text, character)
        voice_score = self._score_voice_strength(text, character, premise)
        beat_score = self._score_beat_originality(text, outline)
        
        dimensions = {
            "language_precision": language_score,
            "character_uniqueness": character_score,
            "voice_strength": voice_score,
            "beat_originality": beat_score,
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            dim.score * self.DIMENSION_WEIGHTS[name]
            for name, dim in dimensions.items()
        )
        
        # Generate prioritized suggestions
        prioritized_suggestions = self._generate_prioritized_suggestions(dimensions)
        
        # Generate summary
        summary = self._generate_summary(overall_score, dimensions)
        
        # Detailed analysis
        detailed_analysis = {
            "cliche_analysis": self._analyze_cliches(text),
            "character_analysis": self._analyze_character(character) if character else {},
            "voice_analysis": self._analyze_voice(text, character),
            "beat_analysis": self._analyze_beats(text, outline),
        }
        
        return {
            "overall_score": round(overall_score, 3),
            "dimensions": {
                name: {
                    "name": dim.name,
                    "score": round(dim.score, 3),
                    "max_score": dim.max_score,
                    "issues": dim.issues,
                    "strengths": dim.strengths,
                    "status": self._get_status(dim.score),
                }
                for name, dim in dimensions.items()
            },
            "prioritized_suggestions": prioritized_suggestions,
            "summary": summary,
            "detailed_analysis": detailed_analysis,
        }
    
    def _score_language_precision(self, text: str) -> DimensionScore:
        """
        Score language precision dimension.
        
        Evaluates:
        - Clichéd phrases
        - Generic language patterns
        - Vague descriptors
        """
        if not text:
            return DimensionScore(
                name="Language Precision",
                score=0.0,
                issues=[{"type": "missing_text", "message": "No text provided for analysis"}],
            )
        
        text_lower = text.lower()
        
        # Detect clichés
        cliche_results = detect_cliches(text)
        cliche_details = cliche_results.get("cliche_details", [])
        
        # Detect generic patterns
        pattern_results = detect_generic_patterns_from_text(text)
        
        # Calculate base score
        base_score = calculate_distinctiveness_score(
            cliche_results,
            {"generic_elements": []},  # No archetype for language-only
            pattern_results
        )
        
        # Collect issues
        issues = []
        strengths = []
        
        # Cliché issues
        narrative_cliches = [c for c in cliche_details if not c.get("in_dialogue", False)]
        dialogue_cliches = [c for c in cliche_details if c.get("in_dialogue", False)]
        
        if narrative_cliches:
            issues.append({
                "type": "narrative_cliche",
                "count": len(narrative_cliches),
                "examples": [c["phrase"] for c in narrative_cliches[:3]],
                "severity": "high",
                "message": f"Found {len(narrative_cliches)} clichéd phrase(s) in narrative text",
            })
        
        if dialogue_cliches:
            issues.append({
                "type": "dialogue_cliche",
                "count": len(dialogue_cliches),
                "examples": [c["phrase"] for c in dialogue_cliches[:3]],
                "severity": "medium",
                "message": f"Found {len(dialogue_cliches)} clichéd phrase(s) in dialogue",
            })
        
        # Generic pattern issues
        narrative_patterns = [p for p in pattern_results if not p.get("in_dialogue", False)]
        if narrative_patterns:
            pattern_types = {}
            for pattern in narrative_patterns:
                ptype = pattern.get("type", "unknown")
                pattern_types[ptype] = pattern_types.get(ptype, 0) + 1
            
            for ptype, count in pattern_types.items():
                issues.append({
                    "type": "generic_pattern",
                    "pattern_type": ptype,
                    "count": count,
                    "severity": "medium" if count > 3 else "low",
                    "message": f"Found {count} instance(s) of {ptype.replace('_', ' ')}",
                })
        
        # Strengths
        if not narrative_cliches and not narrative_patterns:
            strengths.append("No clichés or generic patterns detected in narrative")
        
        if base_score >= self.EXCELLENT_THRESHOLD:
            strengths.append("Language is precise and distinctive")
        elif base_score >= self.GOOD_THRESHOLD:
            strengths.append("Language is generally precise with minor improvements needed")
        
        return DimensionScore(
            name="Language Precision",
            score=base_score,
            issues=issues,
            strengths=strengths,
        )
    
    def _score_character_uniqueness(self, text: str, character: Optional[Dict]) -> DimensionScore:
        """
        Score character uniqueness dimension.
        
        Evaluates:
        - Generic archetypes
        - Lack of unique quirks
        - Contradictions and complexity
        """
        if not character:
            return DimensionScore(
                name="Character Uniqueness",
                score=0.5,  # Neutral score when no character provided
                issues=[{"type": "missing_character", "message": "No character description provided"}],
            )
        
        # Detect archetypes
        archetype_results = detect_generic_archetypes(character)
        generic_elements = archetype_results.get("generic_elements", [])
        archetype_details = archetype_results.get("archetype_details", [])
        
        # Analyze character structure
        char_text = str(character)
        if isinstance(character, dict):
            has_quirks = bool(character.get("quirks")) or bool(character.get("contradictions"))
            has_name = bool(character.get("name"))
            has_description = bool(character.get("description"))
        else:
            has_quirks = False
            has_name = False
            has_description = bool(char_text.strip())
        
        # Calculate score
        base_score = 1.0
        
        # Penalties
        archetype_penalty = len(generic_elements) * 0.3
        base_score -= archetype_penalty
        
        # Bonuses
        if has_quirks:
            base_score += 0.1
        if has_name and has_description:
            base_score += 0.05
        
        base_score = max(0.0, min(1.0, base_score))
        
        # Collect issues and strengths
        issues = []
        strengths = []
        
        if generic_elements:
            issues.append({
                "type": "generic_archetype",
                "archetypes": generic_elements,
                "count": len(generic_elements),
                "severity": "high",
                "message": f"Character shows generic archetype traits: {', '.join(generic_elements)}",
            })
        
        if not has_quirks:
            issues.append({
                "type": "missing_quirks",
                "severity": "medium",
                "message": "Character lacks unique quirks or contradictions",
            })
        
        if has_quirks:
            strengths.append("Character has unique quirks or contradictions")
        
        if not generic_elements:
            strengths.append("Character avoids generic archetypes")
        
        if base_score >= self.EXCELLENT_THRESHOLD:
            strengths.append("Character is highly distinctive and memorable")
        
        return DimensionScore(
            name="Character Uniqueness",
            score=base_score,
            issues=issues,
            strengths=strengths,
        )
    
    def _score_voice_strength(self, text: str, character: Optional[Dict], premise: Optional[Dict]) -> DimensionScore:
        """
        Score voice strength dimension.
        
        Evaluates:
        - Narrative voice distinctiveness
        - Character voice consistency (if multiple characters)
        - Voice markers and unique patterns
        """
        if not text:
            return DimensionScore(
                name="Voice Strength",
                score=0.0,
                issues=[{"type": "missing_text", "message": "No text provided for analysis"}],
            )
        
        # Analyze voice markers
        voice_analysis = self._analyze_voice(text, character)
        
        # Calculate score based on voice indicators
        base_score = 0.5  # Start neutral
        
        # Positive indicators
        has_dialogue = '"' in text or "'" in text
        has_specific_details = self._count_specific_details(text)
        has_varied_sentence_length = self._has_varied_sentence_length(text)
        has_unique_phrases = self._has_unique_phrases(text)
        
        if has_dialogue:
            base_score += 0.1
        if has_specific_details >= 3:
            base_score += 0.15
        if has_varied_sentence_length:
            base_score += 0.1
        if has_unique_phrases:
            base_score += 0.15
        
        base_score = min(1.0, base_score)
        
        # Collect issues and strengths
        issues = []
        strengths = []
        
        if not has_dialogue:
            issues.append({
                "type": "no_dialogue",
                "severity": "low",
                "message": "Story lacks dialogue, which can limit character voice",
            })
        
        if has_specific_details < 3:
            issues.append({
                "type": "vague_descriptions",
                "count": has_specific_details,
                "severity": "medium",
                "message": f"Story has few specific details ({has_specific_details} found)",
            })
        
        if not has_varied_sentence_length:
            issues.append({
                "type": "monotonous_rhythm",
                "severity": "low",
                "message": "Sentence length lacks variation, affecting narrative rhythm",
            })
        
        if has_dialogue:
            strengths.append("Story includes dialogue, showing character voice")
        
        if has_specific_details >= 3:
            strengths.append("Story includes specific, vivid details")
        
        if has_varied_sentence_length:
            strengths.append("Sentence rhythm shows variation")
        
        if base_score >= self.EXCELLENT_THRESHOLD:
            strengths.append("Narrative voice is strong and distinctive")
        
        return DimensionScore(
            name="Voice Strength",
            score=base_score,
            issues=issues,
            strengths=strengths,
        )
    
    def _score_beat_originality(self, text: str, outline: Optional[Dict]) -> DimensionScore:
        """
        Score beat originality dimension.
        
        Evaluates:
        - Predictable story beats
        - Formulaic plot structures
        """
        if not text:
            return DimensionScore(
                name="Beat Originality",
                score=0.0,
                issues=[{"type": "missing_text", "message": "No text provided for analysis"}],
            )
        
        # Use cliché detector for beat detection
        comprehensive_check = self.cliche_detector.detect_all_cliches(
            text=text,
            character=None,
            outline=outline
        )
        
        predictable_beats = comprehensive_check.get("predictable_beats", [])
        formulaic_plots = comprehensive_check.get("formulaic_plots", [])
        
        # Calculate score
        base_score = 1.0
        
        # Penalties
        beat_penalty = len(predictable_beats) * 0.15
        plot_penalty = len(formulaic_plots) * 0.25
        
        base_score -= beat_penalty + plot_penalty
        base_score = max(0.0, base_score)
        
        # Collect issues and strengths
        issues = []
        strengths = []
        
        if predictable_beats:
            unique_beats = set(b["beat"] for b in predictable_beats)
            issues.append({
                "type": "predictable_beats",
                "count": len(predictable_beats),
                "unique_beats": list(unique_beats),
                "severity": "high",
                "message": f"Found {len(predictable_beats)} predictable story beat(s)",
            })
        
        if formulaic_plots:
            issues.append({
                "type": "formulaic_plot",
                "count": len(formulaic_plots),
                "patterns": [p.get("pattern", "") for p in formulaic_plots],
                "severity": "high",
                "message": f"Story follows {len(formulaic_plots)} formulaic plot structure(s)",
            })
        
        if not predictable_beats and not formulaic_plots:
            strengths.append("Story avoids predictable beats and formulaic structures")
        
        if base_score >= self.EXCELLENT_THRESHOLD:
            strengths.append("Story beats are original and unexpected")
        
        return DimensionScore(
            name="Beat Originality",
            score=base_score,
            issues=issues,
            strengths=strengths,
        )
    
    def _generate_prioritized_suggestions(self, dimensions: Dict[str, DimensionScore]) -> List[str]:
        """
        Generate prioritized, actionable suggestions based on dimension scores.
        
        Prioritizes:
        1. High-severity issues
        2. Lowest-scoring dimensions
        3. Most impactful improvements
        """
        suggestions = []
        
        # Sort dimensions by score (lowest first)
        sorted_dims = sorted(
            dimensions.items(),
            key=lambda x: x[1].score
        )
        
        # Collect high-severity issues first
        high_severity_issues = []
        medium_severity_issues = []
        low_severity_issues = []
        
        for dim_name, dim_score in sorted_dims:
            for issue in dim_score.issues:
                severity = issue.get("severity", "low")
                if severity == "high":
                    high_severity_issues.append((dim_name, dim_score, issue))
                elif severity == "medium":
                    medium_severity_issues.append((dim_name, dim_score, issue))
                else:
                    low_severity_issues.append((dim_name, dim_score, issue))
        
        # Generate suggestions from high-severity issues
        for dim_name, dim_score, issue in high_severity_issues:
            suggestion = self._issue_to_suggestion(dim_name, dim_score, issue)
            if suggestion:
                suggestions.append(suggestion)
        
        # Generate suggestions for lowest-scoring dimensions
        for dim_name, dim_score in sorted_dims:
            if dim_score.score < self.GOOD_THRESHOLD and dim_name not in [d[0] for d in high_severity_issues]:
                if dim_score.issues:
                    # Use first issue if available
                    suggestion = self._issue_to_suggestion(dim_name, dim_score, dim_score.issues[0])
                    if suggestion:
                        suggestions.append(suggestion)
                else:
                    # Generic suggestion for low score
                    suggestions.append(
                        f"Improve {dim_score.name.lower()}: "
                        f"Current score is {dim_score.score:.1%}. "
                        f"Focus on making this aspect more distinctive and memorable."
                    )
        
        # Add medium-severity issues
        for dim_name, dim_score, issue in medium_severity_issues[:3]:  # Limit to top 3
            suggestion = self._issue_to_suggestion(dim_name, dim_score, issue)
            if suggestion:
                suggestions.append(suggestion)
        
        # Limit total suggestions
        return suggestions[:10]
    
    def _issue_to_suggestion(self, dim_name: str, dim_score: DimensionScore, issue: Dict) -> Optional[str]:
        """Convert an issue to an actionable suggestion."""
        issue_type = issue.get("type", "")
        message = issue.get("message", "")
        
        # Dimension-specific suggestions
        if dim_name == "language_precision":
            if issue_type == "narrative_cliche":
                examples = issue.get("examples", [])[:2]
                examples_str = ", ".join(f'"{e}"' for e in examples) if examples else ""
                return (
                    f"Replace clichéd phrases in narrative: {examples_str}. "
                    "Use specific, vivid language that creates a unique image."
                )
            elif issue_type == "generic_pattern":
                pattern_type = issue.get("pattern_type", "").replace("_", " ")
                count = issue.get("count", 0)
                return (
                    f"Found {count} instance(s) of {pattern_type}. "
                    "Replace vague language with specific, concrete details."
                )
        
        elif dim_name == "character_uniqueness":
            if issue_type == "generic_archetype":
                archetypes = issue.get("archetypes", [])
                return (
                    f"Character shows generic traits: {', '.join(archetypes)}. "
                    "Add unique quirks, contradictions, or specific details that make them memorable."
                )
            elif issue_type == "missing_quirks":
                return (
                    "Add unique quirks, habits, or contradictions to your character. "
                    "What makes them different from every other character of this type?"
                )
        
        elif dim_name == "voice_strength":
            if issue_type == "vague_descriptions":
                return (
                    "Add more specific, sensory details. Instead of 'it was nice,' "
                    "describe what made it nice: the texture, the sound, the feeling."
                )
            elif issue_type == "no_dialogue":
                return (
                    "Consider adding dialogue to show character voice. "
                    "How characters speak reveals who they are."
                )
        
        elif dim_name == "beat_originality":
            if issue_type == "predictable_beats":
                return (
                    "Story contains predictable beats. Consider subverting expectations: "
                    "what if the expected moment doesn't happen, or happens differently?"
                )
            elif issue_type == "formulaic_plot":
                return (
                    "Story follows a formulaic structure. Add unexpected complications or "
                    "subvert the expected pattern to create something memorable."
                )
        
        # Generic fallback
        if message:
            return f"{message}. Consider how to make this more distinctive."
        
        return None
    
    def _generate_summary(self, overall_score: float, dimensions: Dict[str, DimensionScore]) -> str:
        """Generate a human-readable summary of the memorability score."""
        status = self._get_status(overall_score)
        
        if status == "excellent":
            return (
                f"Excellent memorability score ({overall_score:.1%}). "
                "Your story is distinctive and memorable across all dimensions."
            )
        elif status == "good":
            return (
                f"Good memorability score ({overall_score:.1%}). "
                "Your story is generally distinctive with room for targeted improvements."
            )
        elif status == "needs_improvement":
            return (
                f"Memorability score needs improvement ({overall_score:.1%}). "
                "Focus on the prioritized suggestions to increase distinctiveness."
            )
        else:
            return (
                f"Low memorability score ({overall_score:.1%}). "
                "Significant improvements needed to make the story distinctive and memorable."
            )
    
    def _get_status(self, score: float) -> str:
        """Get status label for a score."""
        if score >= self.EXCELLENT_THRESHOLD:
            return "excellent"
        elif score >= self.GOOD_THRESHOLD:
            return "good"
        elif score >= self.NEEDS_IMPROVEMENT_THRESHOLD:
            return "needs_improvement"
        else:
            return "poor"
    
    # Helper methods for voice analysis
    def _analyze_cliches(self, text: str) -> Dict:
        """Analyze clichés in text."""
        if not text:
            return {}
        return detect_cliches(text)
    
    def _analyze_character(self, character: Optional[Dict]) -> Dict:
        """Analyze character description."""
        if not character:
            return {}
        return detect_generic_archetypes(character)
    
    def _analyze_voice(self, text: str, character: Optional[Dict]) -> Dict:
        """Analyze voice markers in text."""
        if not text:
            return {}
        
        return {
            "has_dialogue": '"' in text or "'" in text,
            "specific_details_count": self._count_specific_details(text),
            "has_varied_sentence_length": self._has_varied_sentence_length(text),
            "has_unique_phrases": self._has_unique_phrases(text),
        }
    
    def _analyze_beats(self, text: str, outline: Optional[Dict]) -> Dict:
        """Analyze story beats."""
        if not text:
            return {}
        
        comprehensive_check = self.cliche_detector.detect_all_cliches(
            text=text,
            character=None,
            outline=outline
        )
        
        return {
            "predictable_beats": comprehensive_check.get("predictable_beats", []),
            "formulaic_plots": comprehensive_check.get("formulaic_plots", []),
        }
    
    def _count_specific_details(self, text: str) -> int:
        """Count specific, concrete details in text."""
        # Look for specific indicators: numbers, colors, specific objects, sensory words
        import re
        
        # Count numbers
        numbers = len(re.findall(r'\b\d+\b', text))
        
        # Count color words
        colors = len(re.findall(r'\b(red|blue|green|yellow|black|white|gray|grey|brown|orange|purple|pink)\b', text, re.IGNORECASE))
        
        # Count sensory words (simplified)
        sensory_words = len(re.findall(
            r'\b(smelled|tasted|felt|heard|saw|smooth|rough|cold|warm|hot|cool|sharp|dull|bright|dark|loud|quiet|soft|hard)\b',
            text,
            re.IGNORECASE
        ))
        
        return numbers + colors + sensory_words
    
    def _has_varied_sentence_length(self, text: str) -> bool:
        """Check if text has varied sentence length."""
        import re
        
        sentences = re.split(r'[.!?]+', text)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        
        if len(sentence_lengths) < 3:
            return False
        
        # Check if there's significant variation (std dev > mean/3)
        if not sentence_lengths:
            return False
        
        mean_length = sum(sentence_lengths) / len(sentence_lengths)
        if mean_length == 0:
            return False
        
        variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        std_dev = variance ** 0.5
        
        return std_dev > mean_length / 3
    
    def _has_unique_phrases(self, text: str) -> bool:
        """Check if text has unique, non-generic phrases."""
        # Simple heuristic: check for uncommon word combinations
        # This is a simplified check - could be enhanced with n-gram analysis
        words = text.lower().split()
        
        # Look for specific, concrete nouns
        specific_nouns = ['door', 'window', 'key', 'book', 'paper', 'pen', 'cup', 'table', 'chair']
        has_specific_nouns = any(noun in words for noun in specific_nouns)
        
        # Look for specific verbs
        specific_verbs = ['opened', 'closed', 'picked', 'placed', 'moved', 'turned', 'walked', 'ran']
        has_specific_verbs = any(verb in words for verb in specific_verbs)
        
        return has_specific_nouns and has_specific_verbs


def get_memorability_scorer() -> MemorabilityScorer:
    """
    Get or create a singleton memorability scorer instance.
    
    Returns:
        MemorabilityScorer instance
    """
    global _scorer_instance
    if '_scorer_instance' not in globals():
        _scorer_instance = MemorabilityScorer()
    return _scorer_instance

