"""
Example usage of the Character Voice Analyzer

This demonstrates how to use the voice analyzer to analyze character dialogue
in a story and check for voice consistency and distinctiveness.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.shortstory.voice_analyzer import analyze_character_voices, get_voice_analyzer
from src.shortstory.utils.validation import validate_story_voices


def example_basic_usage():
    """Basic example of analyzing character voices."""
    story_text = '''
    Alice walked into the room. "The magnificent, extraordinary individual 
    demonstrated remarkable capabilities," she said with confidence.
    
    Bob looked up from his work. "I dunno," he muttered. "Gonna go now. Yeah."
    
    "What are you thinking about?" Alice asked.
    
    Bob replied: "Nothing much. Just stuff."
    '''
    
    # Analyze the story
    result = analyze_character_voices(story_text)
    
    print("=== Character Voice Analysis ===\n")
    print(f"Total dialogue instances: {result['overall']['total_dialogue_instances']}")
    print(f"Characters with dialogue: {result['overall']['characters_with_dialogue']}")
    print(f"Voice differentiation score: {result['overall']['voice_differentiation_score']:.2f}\n")
    
    # Print character analyses
    for char_name, char_data in result['characters'].items():
        print(f"--- {char_name} ---")
        print(f"  Dialogue count: {char_data['dialogue_count']}")
        print(f"  Consistency score: {char_data['consistency']['consistency_score']:.2f}")
        print(f"  Distinctiveness: {char_data['distinctiveness']:.2f}")
        
        # Voice profile
        profile = char_data['voice_profile']
        print(f"  Vocabulary richness: {profile['vocabulary']['vocabulary_richness']:.2f}")
        print(f"  Avg sentence length: {profile['sentence_structure']['avg_sentence_length']:.1f}")
        print(f"  Contraction ratio: {profile['rhythm']['contraction_ratio']:.2f}")
        print()
    
    # Print suggestions
    print("=== Suggestions ===")
    for suggestion in result['overall']['suggestions']:
        print(f"  - {suggestion}")


def example_with_validation():
    """Example using the validation integration."""
    story_text = '''
    "Hello," said John. "How are you?"
    "I'm fine," Mary replied. "Thanks for asking."
    "That's good," John said. "I'm glad to hear it."
    '''
    
    # Use the validation function
    validation_result = validate_story_voices(story_text)
    
    print("=== Voice Validation ===\n")
    print(f"Has dialogue: {validation_result['has_dialogue']}")
    print(f"Differentiation score: {validation_result['voice_differentiation_score']:.2f}\n")
    
    if validation_result['consistency_issues']:
        print("Consistency issues:")
        for issue in validation_result['consistency_issues']:
            print(f"  - {issue}")
        print()
    
    print("Suggestions:")
    for suggestion in validation_result['suggestions']:
        print(f"  - {suggestion}")


def example_detailed_analysis():
    """Example showing detailed analysis using the analyzer directly."""
    analyzer = get_voice_analyzer()
    
    story_text = '''
    The professor spoke carefully: "The methodology requires meticulous 
    examination of the underlying principles and their theoretical foundations."
    
    The student responded: "Yeah, I get it. But like, what does that mean?"
    '''
    
    result = analyzer.analyze_story(story_text)
    
    print("=== Detailed Analysis ===\n")
    
    for char_name, char_data in result['characters'].items():
        print(f"Character: {char_name}\n")
        
        # Show dialogue instances
        print("Dialogue instances:")
        for i, instance in enumerate(char_data['dialogue_instances'], 1):
            print(f"  {i}. \"{instance['text']}\"")
        print()
        
        # Show consistency details
        consistency = char_data['consistency']
        print("Consistency metrics:")
        print(f"  Overall: {consistency['consistency_score']:.2f}")
        print(f"  Vocabulary: {consistency['vocabulary_consistency']:.2f}")
        print(f"  Sentence structure: {consistency['sentence_structure_consistency']:.2f}")
        print(f"  Rhythm: {consistency['rhythm_consistency']:.2f}")
        print()
        
        if consistency['issues']:
            print("Issues:")
            for issue in consistency['issues']:
                print(f"  - {issue}")
            print()


if __name__ == "__main__":
    print("=" * 50)
    print("Character Voice Analyzer Examples")
    print("=" * 50)
    print()
    
    print("\n1. Basic Usage")
    print("-" * 50)
    example_basic_usage()
    
    print("\n\n2. With Validation Integration")
    print("-" * 50)
    example_with_validation()
    
    print("\n\n3. Detailed Analysis")
    print("-" * 50)
    example_detailed_analysis()

