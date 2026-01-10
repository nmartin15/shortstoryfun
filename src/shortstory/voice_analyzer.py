"""
Character Voice Analyzer

Analyzes speech patterns, vocabulary, rhythm, and consistency for character dialogue.
Tracks voice consistency across dialogue instances to ensure distinctive character voices.

See CONCEPTS.md for definitions of character voice requirements.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
import statistics

# Voice consistency thresholds
CONSISTENCY_THRESHOLD = 0.7  # Minimum consistency score for acceptable voice consistency
GOOD_CONSISTENCY_THRESHOLD = 0.8  # Threshold for good overall consistency


class DialogueExtractor:
    """Extracts dialogue from story text and identifies speakers."""
    
    def __init__(self):
        # Patterns for dialogue markers
        self.dialogue_patterns = [
            # Standard quotes: "dialogue" or 'dialogue'
            (r'["\']([^"\']+)["\']', 'quotes'),
            # Dialogue with attribution: "dialogue," said Character
            (r'["\']([^"\']+)["\'][,\s]+(?:said|says|asked|asks|replied|replies|whispered|whispers|shouted|shouts|muttered|mutters|exclaimed|exclaims)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'attributed'),
            # Character said: "dialogue"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:said|says|asked|asks|replied|replies|whispered|whispers|shouted|shouts|muttered|mutters|exclaimed|exclaims)[:\s]+["\']([^"\']+)["\']', 'character_first'),
        ]
    
    def extract_dialogue(self, text: str) -> List[Dict]:
        """
        Extract all dialogue from story text.
        
        Args:
            text: Story text to analyze
            
        Returns:
            List of dialogue dicts with:
            {
                "text": str,  # The dialogue text
                "speaker": Optional[str],  # Character name if identified
                "position": int,  # Character position in text
                "context": str,  # Surrounding text for context
            }
        """
        if not text or not isinstance(text, str):
            return []
        
        dialogue_instances = []
        
        # Extract quoted dialogue
        quote_pattern = r'["\']([^"\']+)["\']'
        for match in re.finditer(quote_pattern, text):
            dialogue_text = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            
            # Get context (50 chars before and after)
            context_start = max(0, start_pos - 50)
            context_end = min(len(text), end_pos + 50)
            context = text[context_start:context_end]
            
            # Try to identify speaker from context
            speaker = self._identify_speaker(text, start_pos, context)
            
            dialogue_instances.append({
                "text": dialogue_text.strip(),
                "speaker": speaker,
                "position": start_pos,
                "context": context,
            })
        
        return dialogue_instances
    
    def _identify_speaker(self, text: str, position: int, context: str) -> Optional[str]:
        """
        Identify speaker from dialogue context.
        
        Looks for patterns like:
        - "dialogue," said Character
        - Character said: "dialogue"
        - Character: "dialogue"
        """
        # Check before the dialogue (preserve case for name matching)
        before_text = text[max(0, position - 100):position]
        before_text_lower = before_text.lower()
        
        # Pattern: Character said: "dialogue"
        pattern1 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:said|says|asked|asks|replied|replies|whispered|whispers|shouted|shouts|muttered|mutters|exclaimed|exclaims)[:\s]+["\']'
        match1 = re.search(pattern1, before_text)
        if match1:
            return match1.group(1)
        
        # Pattern: "dialogue," said Character
        after_text = text[position:min(len(text), position + 100)]
        pattern2 = r'["\'][,\s]+(?:said|says|asked|asks|replied|replies|whispered|whispers|shouted|shouts|muttered|mutters|exclaimed|exclaims)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        match2 = re.search(pattern2, after_text)
        if match2:
            return match2.group(1)
        
        # Pattern: Character: "dialogue"
        pattern3 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?):\s*["\']'
        match3 = re.search(pattern3, before_text)
        if match3:
            return match3.group(1)
        
        return None


class SpeechPatternAnalyzer:
    """Analyzes speech patterns for vocabulary, sentence structure, and rhythm."""
    
    def analyze_dialogue(self, dialogue_text: str) -> Dict:
        """
        Analyze speech patterns in a dialogue instance.
        
        Args:
            dialogue_text: Single dialogue instance
            
        Returns:
            Dict with analysis:
            {
                "vocabulary": {
                    "unique_words": int,
                    "total_words": int,
                    "vocabulary_richness": float,  # unique/total ratio
                    "avg_word_length": float,
                    "complex_words": int,  # words > 6 chars
                    "common_words": int,  # very common words
                },
                "sentence_structure": {
                    "sentence_count": int,
                    "avg_sentence_length": float,
                    "sentence_lengths": List[int],
                    "complexity": float,  # based on punctuation, clauses
                },
                "rhythm": {
                    "punctuation_density": float,  # punctuation per word
                    "exclamation_count": int,
                    "question_count": int,
                    "ellipsis_count": int,
                    "contraction_ratio": float,
                },
                "dialect_markers": {
                    "regional_terms": List[str],
                    "slang_terms": List[str],
                    "formal_language": bool,
                }
            }
        """
        if not dialogue_text or not isinstance(dialogue_text, str):
            return self._empty_analysis()
        
        words = re.findall(r'\b\w+\b', dialogue_text.lower())
        sentences = re.split(r'[.!?]+', dialogue_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Vocabulary analysis
        unique_words = len(set(words))
        total_words = len(words)
        vocabulary_richness = unique_words / total_words if total_words > 0 else 0.0
        avg_word_length = statistics.mean([len(w) for w in words]) if words else 0.0
        complex_words = sum(1 for w in words if len(w) > 6)
        
        # Common words (very frequent English words)
        common_words_list = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its',
            'our', 'their', 'what', 'which', 'who', 'whom', 'whose', 'where',
            'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
        common_words = sum(1 for w in words if w in common_words_list)
        
        # Sentence structure
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        avg_sentence_length = statistics.mean(sentence_lengths) if sentence_lengths else 0.0
        
        # Complexity: count clauses (commas, semicolons, colons, conjunctions)
        clause_markers = len(re.findall(r'[,;:]', dialogue_text))
        conjunctions = len(re.findall(r'\b(and|or|but|because|since|although|while|if|when|where)\b', dialogue_text.lower()))
        complexity = (clause_markers + conjunctions) / total_words if total_words > 0 else 0.0
        
        # Rhythm analysis
        punctuation_count = len(re.findall(r'[.,!?;:—–-]', dialogue_text))
        punctuation_density = punctuation_count / total_words if total_words > 0 else 0.0
        exclamation_count = dialogue_text.count('!')
        question_count = dialogue_text.count('?')
        ellipsis_count = len(re.findall(r'\.{2,}', dialogue_text))
        
        # Contractions
        contractions = len(re.findall(r"\b\w+'(t|s|d|ll|ve|re|m)\b", dialogue_text.lower()))
        contraction_ratio = contractions / total_words if total_words > 0 else 0.0
        
        # Dialect markers (basic detection)
        # Regional terms and slang would need a more sophisticated approach
        # For now, detect informal markers
        slang_patterns = [
            r'\b(yeah|yep|nah|nope|gonna|wanna|gotta|lemme|dunno)\b',
            r'\b(ain\'t|cain\'t|don\'t|can\'t|won\'t)\b',
        ]
        slang_terms = []
        for pattern in slang_patterns:
            matches = re.findall(pattern, dialogue_text.lower())
            slang_terms.extend(matches)
        
        # Formal language detection (absence of contractions, longer sentences, formal vocabulary)
        formal_language = (
            contraction_ratio < 0.1 and
            avg_sentence_length > 10 and
            vocabulary_richness > 0.5
        )
        
        return {
            "vocabulary": {
                "unique_words": unique_words,
                "total_words": total_words,
                "vocabulary_richness": round(vocabulary_richness, 3),
                "avg_word_length": round(avg_word_length, 2),
                "complex_words": complex_words,
                "common_words": common_words,
                "common_word_ratio": round(common_words / total_words, 3) if total_words > 0 else 0.0,
            },
            "sentence_structure": {
                "sentence_count": len(sentences),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "sentence_lengths": sentence_lengths,
                "complexity": round(complexity, 3),
            },
            "rhythm": {
                "punctuation_density": round(punctuation_density, 3),
                "exclamation_count": exclamation_count,
                "question_count": question_count,
                "ellipsis_count": ellipsis_count,
                "contraction_ratio": round(contraction_ratio, 3),
            },
            "dialect_markers": {
                "slang_terms": list(set(slang_terms)),
                "formal_language": formal_language,
            }
        }
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            "vocabulary": {
                "unique_words": 0,
                "total_words": 0,
                "vocabulary_richness": 0.0,
                "avg_word_length": 0.0,
                "complex_words": 0,
                "common_words": 0,
                "common_word_ratio": 0.0,
            },
            "sentence_structure": {
                "sentence_count": 0,
                "avg_sentence_length": 0.0,
                "sentence_lengths": [],
                "complexity": 0.0,
            },
            "rhythm": {
                "punctuation_density": 0.0,
                "exclamation_count": 0,
                "question_count": 0,
                "ellipsis_count": 0,
                "contraction_ratio": 0.0,
            },
            "dialect_markers": {
                "slang_terms": [],
                "formal_language": False,
            }
        }


class VoiceConsistencyTracker:
    """Tracks voice consistency across dialogue instances for each character."""
    
    def calculate_consistency(self, character_dialogues: List[Dict]) -> Dict:
        """
        Calculate voice consistency metrics for a character.
        
        Args:
            character_dialogues: List of dialogue analysis dicts for one character
            
        Returns:
            Dict with consistency metrics:
            {
                "consistency_score": float,  # 0-1, higher = more consistent
                "vocabulary_consistency": float,
                "sentence_structure_consistency": float,
                "rhythm_consistency": float,
                "variations": {
                    "vocabulary_variation": float,
                    "sentence_length_variation": float,
                    "rhythm_variation": float,
                },
                "issues": List[str],  # Inconsistency issues found
            }
        """
        if len(character_dialogues) < 2:
            return {
                "consistency_score": 1.0,  # Perfect if only one instance
                "vocabulary_consistency": 1.0,
                "sentence_structure_consistency": 1.0,
                "rhythm_consistency": 1.0,
                "variations": {
                    "vocabulary_variation": 0.0,
                    "sentence_length_variation": 0.0,
                    "rhythm_variation": 0.0,
                },
                "issues": ["Insufficient dialogue to assess consistency"],
            }
        
        # Extract metrics from all dialogues
        vocab_richness = [d["vocabulary"]["vocabulary_richness"] for d in character_dialogues]
        avg_word_lengths = [d["vocabulary"]["avg_word_length"] for d in character_dialogues]
        sentence_lengths = [d["sentence_structure"]["avg_sentence_length"] for d in character_dialogues]
        contraction_ratios = [d["rhythm"]["contraction_ratio"] for d in character_dialogues]
        punctuation_densities = [d["rhythm"]["punctuation_density"] for d in character_dialogues]
        
        # Calculate coefficient of variation (std dev / mean) for each metric
        # Lower variation = higher consistency
        def cv(values):
            if not values or all(v == 0 for v in values):
                return 0.0
            mean = statistics.mean(values)
            if mean == 0:
                return 0.0
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            return std_dev / mean
        
        vocab_variation = cv(vocab_richness)
        word_length_variation = cv(avg_word_lengths)
        sentence_variation = cv(sentence_lengths)
        contraction_variation = cv(contraction_ratios)
        punctuation_variation = cv(punctuation_densities)
        
        # Consistency scores (1.0 = perfect, 0.0 = completely inconsistent)
        # Use inverse of variation, capped at 1.0
        vocab_consistency = max(0.0, 1.0 - min(vocab_variation, 1.0))
        word_length_consistency = max(0.0, 1.0 - min(word_length_variation, 1.0))
        sentence_consistency = max(0.0, 1.0 - min(sentence_variation, 1.0))
        rhythm_consistency = max(0.0, 1.0 - min((contraction_variation + punctuation_variation) / 2, 1.0))
        
        # Overall consistency score (weighted average)
        consistency_score = (
            vocab_consistency * 0.3 +
            word_length_consistency * 0.2 +
            sentence_consistency * 0.3 +
            rhythm_consistency * 0.2
        )
        
        # Identify issues
        issues = []
        if vocab_variation > 0.3:
            issues.append(f"Vocabulary richness varies significantly (CV: {vocab_variation:.2f})")
        if sentence_variation > 0.4:
            issues.append(f"Sentence length varies significantly (CV: {sentence_variation:.2f})")
        if contraction_variation > 0.5:
            issues.append("Contraction usage is inconsistent")
        if punctuation_variation > 0.5:
            issues.append("Punctuation patterns vary significantly")
        
        return {
            "consistency_score": round(consistency_score, 3),
            "vocabulary_consistency": round(vocab_consistency, 3),
            "sentence_structure_consistency": round(sentence_consistency, 3),
            "rhythm_consistency": round(rhythm_consistency, 3),
            "variations": {
                "vocabulary_variation": round(vocab_variation, 3),
                "sentence_length_variation": round(sentence_variation, 3),
                "rhythm_variation": round((contraction_variation + punctuation_variation) / 2, 3),
            },
            "issues": issues,
        }


class CharacterVoiceAnalyzer:
    """
    Main analyzer for character voice patterns and consistency.
    
    Analyzes:
    - Speech patterns (vocabulary, sentence structure, rhythm)
    - Voice consistency across dialogue instances
    - Distinctiveness between characters
    """
    
    def __init__(self):
        self.dialogue_extractor = DialogueExtractor()
        self.pattern_analyzer = SpeechPatternAnalyzer()
        self.consistency_tracker = VoiceConsistencyTracker()
    
    def analyze_story(self, story_text: str, character_info: Optional[Dict] = None) -> Dict:
        """
        Analyze character voices in a story.
        
        Args:
            story_text: Full story text
            character_info: Optional character info from premise (name, quirks, etc.)
            
        Returns:
            Dict with analysis:
            {
                "characters": {
                    "character_name": {
                        "dialogue_count": int,
                        "voice_profile": Dict,  # Average patterns
                        "consistency": Dict,  # Consistency metrics
                        "distinctiveness": float,  # How different from other characters
                    }
                },
                "overall": {
                    "total_dialogue_instances": int,
                    "characters_with_dialogue": int,
                    "voice_differentiation_score": float,  # 0-1, how distinct characters are
                    "suggestions": List[str],
                }
            }
        """
        if not story_text or not isinstance(story_text, str):
            return self._empty_analysis_result()
        
        # Extract dialogue
        dialogue_instances = self.dialogue_extractor.extract_dialogue(story_text)
        
        if not dialogue_instances:
            return {
                "characters": {},
                "overall": {
                    "total_dialogue_instances": 0,
                    "characters_with_dialogue": 0,
                    "voice_differentiation_score": 0.0,
                    "suggestions": ["No dialogue found in story. Consider adding character dialogue to develop voice."],
                }
            }
        
        # Group dialogue by character
        character_dialogues = defaultdict(list)
        for dialogue in dialogue_instances:
            speaker = dialogue.get("speaker") or "Unknown"
            character_dialogues[speaker].append(dialogue)
        
        # Analyze each character
        character_analyses = {}
        all_voice_profiles = []
        
        for character_name, dialogues in character_dialogues.items():
            # Analyze each dialogue instance
            analyzed_dialogues = []
            for dialogue in dialogues:
                analysis = self.pattern_analyzer.analyze_dialogue(dialogue["text"])
                analyzed_dialogues.append(analysis)
            
            # Calculate average voice profile
            voice_profile = self._calculate_average_profile(analyzed_dialogues)
            
            # Calculate consistency
            consistency = self.consistency_tracker.calculate_consistency(analyzed_dialogues)
            
            character_analyses[character_name] = {
                "dialogue_count": len(dialogues),
                "voice_profile": voice_profile,
                "consistency": consistency,
                "dialogue_instances": [
                    {
                        "text": d["text"][:100] + "..." if len(d["text"]) > 100 else d["text"],
                        "position": d["position"],
                    }
                    for d in dialogues
                ],
            }
            
            all_voice_profiles.append(voice_profile)
        
        # Calculate distinctiveness between characters
        differentiation_score = self._calculate_differentiation(all_voice_profiles)
        
        # Add distinctiveness scores to each character
        for char_name in character_analyses:
            char_profile = character_analyses[char_name]["voice_profile"]
            distinctiveness = self._calculate_character_distinctiveness(
                char_profile, all_voice_profiles
            )
            character_analyses[char_name]["distinctiveness"] = round(distinctiveness, 3)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(character_analyses, differentiation_score)
        
        return {
            "characters": character_analyses,
            "overall": {
                "total_dialogue_instances": len(dialogue_instances),
                "characters_with_dialogue": len(character_analyses),
                "voice_differentiation_score": round(differentiation_score, 3),
                "suggestions": suggestions,
            }
        }
    
    def _calculate_average_profile(self, analyzed_dialogues: List[Dict]) -> Dict:
        """Calculate average voice profile from multiple dialogue instances."""
        if not analyzed_dialogues:
            return self.pattern_analyzer._empty_analysis()
        
        # Average vocabulary metrics
        vocab_richness = statistics.mean([d["vocabulary"]["vocabulary_richness"] for d in analyzed_dialogues])
        avg_word_length = statistics.mean([d["vocabulary"]["avg_word_length"] for d in analyzed_dialogues])
        complex_words_avg = statistics.mean([d["vocabulary"]["complex_words"] for d in analyzed_dialogues])
        common_word_ratio = statistics.mean([d["vocabulary"]["common_word_ratio"] for d in analyzed_dialogues])
        
        # Average sentence structure
        avg_sentence_length = statistics.mean([d["sentence_structure"]["avg_sentence_length"] for d in analyzed_dialogues])
        complexity = statistics.mean([d["sentence_structure"]["complexity"] for d in analyzed_dialogues])
        
        # Average rhythm
        contraction_ratio = statistics.mean([d["rhythm"]["contraction_ratio"] for d in analyzed_dialogues])
        punctuation_density = statistics.mean([d["rhythm"]["punctuation_density"] for d in analyzed_dialogues])
        exclamation_ratio = statistics.mean([d["rhythm"]["exclamation_count"] / max(d["vocabulary"]["total_words"], 1) for d in analyzed_dialogues])
        
        # Dialect markers (union of all slang terms)
        all_slang = set()
        for d in analyzed_dialogues:
            all_slang.update(d["dialect_markers"]["slang_terms"])
        formal_language = all(not d["dialect_markers"]["slang_terms"] for d in analyzed_dialogues)
        
        return {
            "vocabulary": {
                "vocabulary_richness": round(vocab_richness, 3),
                "avg_word_length": round(avg_word_length, 2),
                "complex_words_avg": round(complex_words_avg, 2),
                "common_word_ratio": round(common_word_ratio, 3),
            },
            "sentence_structure": {
                "avg_sentence_length": round(avg_sentence_length, 2),
                "complexity": round(complexity, 3),
            },
            "rhythm": {
                "contraction_ratio": round(contraction_ratio, 3),
                "punctuation_density": round(punctuation_density, 3),
                "exclamation_ratio": round(exclamation_ratio, 3),
            },
            "dialect_markers": {
                "slang_terms": list(all_slang),
                "formal_language": formal_language,
            }
        }
    
    def _calculate_differentiation(self, voice_profiles: List[Dict]) -> float:
        """
        Calculate how distinct characters are from each other.
        
        Returns score 0-1, where 1 = very distinct, 0 = very similar.
        """
        if len(voice_profiles) < 2:
            return 0.0  # Can't differentiate with only one character
        
        # Extract key metrics for comparison
        metrics = []
        for profile in voice_profiles:
            metrics.append({
                "vocab_richness": profile["vocabulary"]["vocabulary_richness"],
                "word_length": profile["vocabulary"]["avg_word_length"],
                "sentence_length": profile["sentence_structure"]["avg_sentence_length"],
                "contraction": profile["rhythm"]["contraction_ratio"],
            })
        
        # Calculate pairwise differences
        differences = []
        for i in range(len(metrics)):
            for j in range(i + 1, len(metrics)):
                diff = sum(
                    abs(metrics[i][k] - metrics[j][k])
                    for k in metrics[i].keys()
                )
                differences.append(diff)
        
        # Normalize to 0-1 scale (assuming max difference of ~4.0 for 4 metrics)
        avg_difference = statistics.mean(differences) if differences else 0.0
        differentiation_score = min(1.0, avg_difference / 2.0)  # Normalize
        
        return differentiation_score
    
    def _calculate_character_distinctiveness(
        self, character_profile: Dict, all_profiles: List[Dict]
    ) -> float:
        """Calculate how distinct a character is from others."""
        if len(all_profiles) < 2:
            return 0.5  # Neutral if only one character
        
        # Calculate average distance from other characters
        distances = []
        for other_profile in all_profiles:
            if other_profile == character_profile:
                continue
            
            distance = (
                abs(character_profile["vocabulary"]["vocabulary_richness"] - 
                    other_profile["vocabulary"]["vocabulary_richness"]) +
                abs(character_profile["vocabulary"]["avg_word_length"] - 
                    other_profile["vocabulary"]["avg_word_length"]) +
                abs(character_profile["sentence_structure"]["avg_sentence_length"] - 
                    other_profile["sentence_structure"]["avg_sentence_length"]) +
                abs(character_profile["rhythm"]["contraction_ratio"] - 
                    other_profile["rhythm"]["contraction_ratio"])
            )
            distances.append(distance)
        
        if not distances:
            return 0.5
        
        avg_distance = statistics.mean(distances)
        # Normalize to 0-1 (assuming max distance ~4.0)
        distinctiveness = min(1.0, avg_distance / 2.0)
        return distinctiveness
    
    def _generate_suggestions(
        self, character_analyses: Dict, differentiation_score: float
    ) -> List[str]:
        """Generate suggestions for improving character voices."""
        suggestions = []
        
        # Check differentiation
        if differentiation_score < 0.3:
            suggestions.append(
                "Character voices are too similar. Consider giving each character "
                "distinctive speech patterns, vocabulary choices, or sentence rhythms."
            )
        
        # Check consistency for each character
        for char_name, analysis in character_analyses.items():
            consistency = analysis["consistency"]["consistency_score"]
            if consistency < CONSISTENCY_THRESHOLD:
                suggestions.append(
                    f"{char_name}'s voice is inconsistent across dialogue instances. "
                    f"Review dialogue to maintain consistent speech patterns."
                )
            
            # Check for generic dialogue
            if analysis["dialogue_count"] > 0:
                vocab_richness = analysis["voice_profile"]["vocabulary"]["vocabulary_richness"]
                if vocab_richness < 0.4:
                    suggestions.append(
                        f"{char_name}'s dialogue uses repetitive vocabulary. "
                        "Consider adding more varied word choices to reflect their unique voice."
                    )
        
        # Check for characters with very little dialogue
        for char_name, analysis in character_analyses.items():
            if analysis["dialogue_count"] < 2:
                suggestions.append(
                    f"{char_name} has very little dialogue. More dialogue instances "
                    "would help establish and maintain their distinctive voice."
                )
        
        if not suggestions:
            suggestions.append("Character voices are well-developed and consistent.")
        
        return suggestions
    
    def _empty_analysis_result(self) -> Dict:
        """Return empty analysis result structure."""
        return {
            "characters": {},
            "overall": {
                "total_dialogue_instances": 0,
                "characters_with_dialogue": 0,
                "voice_differentiation_score": 0.0,
                "suggestions": ["No story text provided for analysis."],
            }
        }


# Convenience function
def analyze_character_voices(story_text: str, character_info: Optional[Dict] = None) -> Dict:
    """
    Analyze character voices in a story.
    
    Args:
        story_text: Full story text
        character_info: Optional character info from premise
        
    Returns:
        Analysis dict with character voice profiles and consistency metrics
    """
    analyzer = CharacterVoiceAnalyzer()
    return analyzer.analyze_story(story_text, character_info)


# Singleton instance for convenience
_analyzer_instance = None

def get_voice_analyzer() -> CharacterVoiceAnalyzer:
    """Get singleton instance of CharacterVoiceAnalyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CharacterVoiceAnalyzer()
    return _analyzer_instance


class VoiceConsistencyChecker:
    """
    Checks voice consistency across draft stages (e.g., draft vs revised draft).
    
    Ensures character voices remain consistent from draft to revision,
    identifying any significant changes in speech patterns, vocabulary, or rhythm.
    """
    
    def __init__(self):
        self.analyzer = CharacterVoiceAnalyzer()
    
    def check_consistency_across_stages(
        self,
        draft_analysis: Dict,
        revised_analysis: Dict,
        character_info: Optional[Dict] = None
    ) -> Dict:
        """
        Compare voice profiles between draft and revised draft stages.
        
        Args:
            draft_analysis: Voice analysis from draft stage (from validate_story_voices)
            revised_analysis: Voice analysis from revised draft stage (from validate_story_voices)
            character_info: Optional character info from premise
            
        Returns:
            Dict with consistency comparison results:
            {
                "overall_consistency_score": float,  # 0-1, higher = more consistent
                "characters": {
                    "character_name": {
                        "consistency_score": float,
                        "profile_changes": Dict,  # Detailed changes in voice profile
                        "issues": List[str],  # Specific inconsistency issues
                        "improvements": List[str],  # Positive changes (if any)
                    }
                },
                "summary": {
                    "characters_checked": int,
                    "characters_with_issues": int,
                    "overall_status": str,  # "consistent", "minor_issues", "major_issues"
                },
                "suggestions": List[str],
            }
        """
        if not draft_analysis or not revised_analysis:
            return {
                "overall_consistency_score": 0.0,
                "characters": {},
                "summary": {
                    "characters_checked": 0,
                    "characters_with_issues": 0,
                    "overall_status": "insufficient_data",
                },
                "suggestions": ["Insufficient data to check consistency across stages."],
            }
        
        draft_characters = draft_analysis.get("characters", {})
        revised_characters = revised_analysis.get("characters", {})
        
        if not draft_characters and not revised_characters:
            return {
                "overall_consistency_score": 1.0,  # No dialogue = no inconsistency
                "characters": {},
                "summary": {
                    "characters_checked": 0,
                    "characters_with_issues": 0,
                    "overall_status": "no_dialogue",
                },
                "suggestions": ["No dialogue found in either stage."],
            }
        
        # Get all unique character names from both stages
        all_characters = set(draft_characters.keys()) | set(revised_characters.keys())
        
        character_comparisons = {}
        consistency_scores = []
        
        for char_name in all_characters:
            draft_char = draft_characters.get(char_name)
            revised_char = revised_characters.get(char_name)
            
            if not draft_char and not revised_char:
                continue
            
            # If character only appears in one stage, flag as issue
            if not draft_char:
                character_comparisons[char_name] = {
                    "consistency_score": 0.0,
                    "profile_changes": {},
                    "issues": [f"Character {char_name} appears in revised draft but not in original draft."],
                    "improvements": [],
                }
                consistency_scores.append(0.0)
                continue
            
            if not revised_char:
                character_comparisons[char_name] = {
                    "consistency_score": 0.0,
                    "profile_changes": {},
                    "issues": [f"Character {char_name} appears in original draft but not in revised draft."],
                    "improvements": [],
                }
                consistency_scores.append(0.0)
                continue
            
            # Compare voice profiles
            comparison = self._compare_character_profiles(char_name, draft_char, revised_char)
            character_comparisons[char_name] = comparison
            consistency_scores.append(comparison["consistency_score"])
        
        # Calculate overall consistency score
        overall_score = statistics.mean(consistency_scores) if consistency_scores else 1.0
        
        # Generate summary
        characters_with_issues = sum(
            1 for comp in character_comparisons.values()
            if comp["consistency_score"] < CONSISTENCY_THRESHOLD or comp["issues"]
        )
        
        if overall_score >= GOOD_CONSISTENCY_THRESHOLD:
            overall_status = "consistent"
        elif overall_score >= 0.6:
            overall_status = "minor_issues"
        else:
            overall_status = "major_issues"
        
        # Generate suggestions
        suggestions = self._generate_consistency_suggestions(character_comparisons, overall_score)
        
        return {
            "overall_consistency_score": round(overall_score, 3),
            "characters": character_comparisons,
            "summary": {
                "characters_checked": len(character_comparisons),
                "characters_with_issues": characters_with_issues,
                "overall_status": overall_status,
            },
            "suggestions": suggestions,
        }
    
    def _compare_character_profiles(
        self, char_name: str, draft_char: Dict, revised_char: Dict
    ) -> Dict:
        """
        Compare voice profiles for a single character between draft stages.
        
        Args:
            char_name: Character name
            draft_char: Character analysis from draft stage
            revised_char: Character analysis from revised draft stage
            
        Returns:
            Comparison dict with consistency metrics and issues
        """
        draft_profile = draft_char.get("voice_profile", {})
        revised_profile = revised_char.get("voice_profile", {})
        
        draft_consistency = draft_char.get("consistency", {})
        revised_consistency = revised_char.get("consistency", {})
        
        # Compare key voice metrics
        profile_changes = {}
        issues = []
        improvements = []
        
        # Vocabulary comparison
        draft_vocab = draft_profile.get("vocabulary", {})
        revised_vocab = revised_profile.get("vocabulary", {})
        
        vocab_richness_diff = abs(
            draft_vocab.get("vocabulary_richness", 0) - 
            revised_vocab.get("vocabulary_richness", 0)
        )
        avg_word_length_diff = abs(
            draft_vocab.get("avg_word_length", 0) - 
            revised_vocab.get("avg_word_length", 0)
        )
        
        if vocab_richness_diff > 0.15:
            issues.append(
                f"Vocabulary richness changed significantly "
                f"(draft: {draft_vocab.get('vocabulary_richness', 0):.2f}, "
                f"revised: {revised_vocab.get('vocabulary_richness', 0):.2f})"
            )
        elif vocab_richness_diff > 0.05:
            profile_changes["vocabulary_richness"] = {
                "draft": draft_vocab.get("vocabulary_richness", 0),
                "revised": revised_vocab.get("vocabulary_richness", 0),
                "change": vocab_richness_diff,
            }
        
        if avg_word_length_diff > 1.0:
            issues.append(
                f"Average word length changed significantly "
                f"(draft: {draft_vocab.get('avg_word_length', 0):.2f}, "
                f"revised: {revised_vocab.get('avg_word_length', 0):.2f})"
            )
        
        # Sentence structure comparison
        draft_sentence = draft_profile.get("sentence_structure", {})
        revised_sentence = revised_profile.get("sentence_structure", {})
        
        sentence_length_diff = abs(
            draft_sentence.get("avg_sentence_length", 0) - 
            revised_sentence.get("avg_sentence_length", 0)
        )
        
        if sentence_length_diff > 3.0:
            issues.append(
                f"Average sentence length changed significantly "
                f"(draft: {draft_sentence.get('avg_sentence_length', 0):.2f}, "
                f"revised: {revised_sentence.get('avg_sentence_length', 0):.2f})"
            )
        
        # Rhythm comparison
        draft_rhythm = draft_profile.get("rhythm", {})
        revised_rhythm = revised_profile.get("rhythm", {})
        
        contraction_diff = abs(
            draft_rhythm.get("contraction_ratio", 0) - 
            revised_rhythm.get("contraction_ratio", 0)
        )
        
        if contraction_diff > 0.2:
            issues.append(
                f"Contraction usage changed significantly "
                f"(draft: {draft_rhythm.get('contraction_ratio', 0):.2f}, "
                f"revised: {revised_rhythm.get('contraction_ratio', 0):.2f})"
            )
        
        # Dialect markers comparison
        draft_dialect = draft_profile.get("dialect_markers", {})
        revised_dialect = revised_profile.get("dialect_markers", {})
        
        draft_slang = set(draft_dialect.get("slang_terms", []))
        revised_slang = set(revised_dialect.get("slang_terms", []))
        
        if draft_slang != revised_slang:
            added_slang = revised_slang - draft_slang
            removed_slang = draft_slang - revised_slang
            if added_slang:
                issues.append(f"New slang terms added: {', '.join(added_slang)}")
            if removed_slang:
                issues.append(f"Slang terms removed: {', '.join(removed_slang)}")
        
        # Consistency score comparison
        draft_consistency_score = draft_consistency.get("consistency_score", 1.0)
        revised_consistency_score = revised_consistency.get("consistency_score", 1.0)
        
        # If revised version has better consistency, that's an improvement
        if revised_consistency_score > draft_consistency_score + 0.1:
            improvements.append(
                f"Voice consistency improved from {draft_consistency_score:.2f} to {revised_consistency_score:.2f}"
            )
        elif revised_consistency_score < draft_consistency_score - 0.1:
            issues.append(
                f"Voice consistency decreased from {draft_consistency_score:.2f} to {revised_consistency_score:.2f}"
            )
        
        # Calculate overall consistency score for this character
        # Based on how much the profile changed
        change_penalties = [
            vocab_richness_diff * 2,  # Weight vocabulary changes more
            avg_word_length_diff * 0.1,
            sentence_length_diff * 0.1,
            contraction_diff * 2,  # Weight rhythm changes more
            0.2 if draft_slang != revised_slang else 0.0,  # Slang changes
        ]
        
        total_penalty = sum(change_penalties)
        consistency_score = max(0.0, 1.0 - min(total_penalty, 1.0))
        
        return {
            "consistency_score": round(consistency_score, 3),
            "profile_changes": profile_changes,
            "issues": issues,
            "improvements": improvements,
        }
    
    def _generate_consistency_suggestions(
        self, character_comparisons: Dict, overall_score: float
    ) -> List[str]:
        """Generate suggestions based on consistency comparison results."""
        suggestions = []
        
        if overall_score < 0.6:
            suggestions.append(
                "Significant voice inconsistencies detected between draft and revision. "
                "Review character dialogue to ensure voices remain consistent."
            )
        elif overall_score < GOOD_CONSISTENCY_THRESHOLD:
            suggestions.append(
                "Minor voice inconsistencies detected. Review character dialogue "
                "to maintain consistent speech patterns across draft stages."
            )
        
        # Character-specific suggestions
        for char_name, comparison in character_comparisons.items():
            if comparison["consistency_score"] < CONSISTENCY_THRESHOLD:
                if comparison["issues"]:
                    suggestions.append(
                        f"{char_name}: {comparison['issues'][0]}"
                    )
        
        if not suggestions:
            suggestions.append("Character voices remain consistent across draft stages.")
        
        return suggestions


# Convenience function for checking consistency across stages
def check_voice_consistency_across_stages(
    draft_analysis: Dict,
    revised_analysis: Dict,
    character_info: Optional[Dict] = None
) -> Dict:
    """
    Check voice consistency between draft and revised draft stages.
    
    Args:
        draft_analysis: Voice analysis from draft stage
        revised_analysis: Voice analysis from revised draft stage
        character_info: Optional character info from premise
        
    Returns:
        Consistency comparison results
    """
    checker = VoiceConsistencyChecker()
    return checker.check_consistency_across_stages(draft_analysis, revised_analysis, character_info)

