"""
Example: Using the Short Story Pipeline with Distinctive Voice

This demonstrates the full pipeline to create a short story with distinctive
character voices, showing how voice consistency is maintained across draft stages.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.voice_analyzer import analyze_character_voices


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_voice_analysis(analysis, stage_name):
    """Print voice analysis results for a stage."""
    print(f"\n--- Voice Analysis: {stage_name} ---")
    
    if not analysis.get("has_dialogue"):
        print("  No dialogue found in this stage.")
        return
    
    overall = analysis.get("overall", {})
    print(f"  Total dialogue instances: {overall.get('total_dialogue_instances', 0)}")
    print(f"  Characters with dialogue: {overall.get('characters_with_dialogue', 0)}")
    print(f"  Voice differentiation score: {overall.get('voice_differentiation_score', 0):.3f}")
    
    characters = analysis.get("characters", {})
    for char_name, char_data in characters.items():
        print(f"\n  Character: {char_name}")
        print(f"    Dialogue count: {char_data.get('dialogue_count', 0)}")
        
        consistency = char_data.get("consistency", {})
        print(f"    Consistency score: {consistency.get('consistency_score', 0):.3f}")
        print(f"    Distinctiveness: {char_data.get('distinctiveness', 0):.3f}")
        
        profile = char_data.get("voice_profile", {})
        vocab = profile.get("vocabulary", {})
        sentence = profile.get("sentence_structure", {})
        rhythm = profile.get("rhythm", {})
        
        print(f"    Vocabulary richness: {vocab.get('vocabulary_richness', 0):.3f}")
        print(f"    Avg sentence length: {sentence.get('avg_sentence_length', 0):.2f}")
        print(f"    Contraction ratio: {rhythm.get('contraction_ratio', 0):.3f}")
        
        if consistency.get("issues"):
            print(f"    Issues: {', '.join(consistency['issues'][:2])}")


def print_consistency_check(consistency_check):
    """Print voice consistency check results across stages."""
    print("\n--- Voice Consistency Across Draft Stages ---")
    
    summary = consistency_check.get("summary", {})
    print(f"  Characters checked: {summary.get('characters_checked', 0)}")
    print(f"  Characters with issues: {summary.get('characters_with_issues', 0)}")
    print(f"  Overall status: {summary.get('overall_status', 'unknown')}")
    print(f"  Overall consistency score: {consistency_check.get('overall_consistency_score', 0):.3f}")
    
    characters = consistency_check.get("characters", {})
    for char_name, char_data in characters.items():
        print(f"\n  Character: {char_name}")
        print(f"    Consistency score: {char_data.get('consistency_score', 0):.3f}")
        
        issues = char_data.get("issues", [])
        if issues:
            print(f"    Issues:")
            for issue in issues[:3]:
                print(f"      - {issue}")
        
        improvements = char_data.get("improvements", [])
        if improvements:
            print(f"    Improvements:")
            for improvement in improvements:
                print(f"      + {improvement}")
    
    suggestions = consistency_check.get("suggestions", [])
    if suggestions:
        print(f"\n  Suggestions:")
        for suggestion in suggestions:
            print(f"    - {suggestion}")


def main():
    """Example pipeline usage with distinctive voice demonstration."""
    print_section("Short Story Pipeline - Distinctive Voice Example")
    
    pipeline = ShortStoryPipeline(max_word_count=2000)  # Smaller limit for example
    
    # Stage 1: Premise capture with distinctive character voice
    print("\n[Stage 1] Capturing premise with distinctive character...")
    idea = "A lighthouse keeper who collects lost voices in glass jars"
    character = {
        "name": "Mara",
        "description": "A reclusive lighthouse keeper with a unique collection",
        "quirks": [
            "Never speaks above a whisper",
            "Counts everything in sevens",
            "Uses maritime metaphors in everyday speech"
        ],
        "contradictions": "Fiercely protective of her collection but terrified of human connection",
        "voice_markers": "Speaks in fragments, uses nautical terms, avoids contractions"
    }
    theme = "What happens to the stories we never tell?"
    
    premise = pipeline.capture_premise(idea, character, theme, validate=True)
    print(f"✓ Premise captured: {premise['idea']}")
    
    if premise.get("validation"):
        validation = premise["validation"]
        print(f"  Distinctiveness score: {validation['distinctiveness']['average_score']:.2f}")
        if validation.get("warnings"):
            print(f"  Warnings: {len(validation['warnings'])}")
    
    # Stage 2: Generate outline
    print("\n[Stage 2] Generating outline...")
    outline = pipeline.generate_outline(use_llm=False)  # Use template for demo
    print(f"✓ Outline generated with {len(outline.get('structure', []))} acts")
    
    # Stage 3: Scaffold voice development
    print("\n[Stage 3] Scaffolding voice development...")
    scaffold = pipeline.scaffold(use_llm=False)  # Use template for demo
    print("✓ Voice scaffold created")
    
    if scaffold.get("character_voices"):
        print("  Character voice profiles:")
        for char_name, voice_profile in scaffold["character_voices"].items():
            print(f"    {char_name}: {len(voice_profile.get('voice_markers', []))} voice markers")
    
    # Stage 4: Generate draft
    print("\n[Stage 4] Generating draft...")
    draft = pipeline.draft(use_llm=False)  # Use template for demo
    print(f"✓ Draft generated: {draft['word_count']} words")
    
    # Analyze voices in draft
    draft_voice_analysis = analyze_character_voices(
        draft["text"],
        character_info=character
    )
    print_voice_analysis(draft_voice_analysis, "Draft Stage")
    
    # Stage 5: Revise with voice consistency checking
    print("\n[Stage 5] Revising draft with voice consistency checking...")
    revised_draft = pipeline.revise(use_llm=False)  # Use template for demo
    print(f"✓ Draft revised: {revised_draft['word_count']} words")
    
    # Show revision analysis
    revisions = revised_draft.get("revisions", {})
    print(f"\n  Revision metrics:")
    print(f"    Distinctiveness score: {revisions.get('distinctiveness_score', 0):.2f}")
    print(f"    Cliche count: {revisions.get('cliche_count', 0)}")
    
    # Analyze voices in revised draft
    revised_voice_analysis = revisions.get("revised_voice_analysis", {})
    if revised_voice_analysis:
        print_voice_analysis(revised_voice_analysis, "Revised Draft Stage")
    
    # Show voice consistency check
    voice_consistency = revisions.get("voice_consistency_check")
    if voice_consistency:
        print_consistency_check(voice_consistency)
    
    # Final summary
    print_section("Final Story Summary")
    print(f"\nStory: {idea}")
    print(f"Character: {character['name']}")
    print(f"Theme: {theme}")
    print(f"Final word count: {revised_draft['word_count']} words")
    print(f"\nStory preview (first 300 characters):")
    print(f"  {revised_draft['text'][:300]}...")
    
    # Show voice development summary
    if voice_consistency:
        summary = voice_consistency.get("summary", {})
        print(f"\nVoice Consistency Summary:")
        print(f"  Status: {summary.get('overall_status', 'unknown')}")
        print(f"  Score: {voice_consistency.get('overall_consistency_score', 0):.3f}")
        print(f"  Characters checked: {summary.get('characters_checked', 0)}")
        print(f"  Characters with issues: {summary.get('characters_with_issues', 0)}")


def example_full_pipeline():
    """Alternative: Run full pipeline in one call."""
    print_section("Full Pipeline - Single Call Example")
    
    pipeline = ShortStoryPipeline(max_word_count=2000)
    
    idea = "A clockmaker who repairs time itself, one broken moment at a time"
    character = {
        "name": "Elias",
        "description": "An elderly clockmaker with an unusual specialty",
        "quirks": [
            "Speaks in precise, measured sentences",
            "Never uses contractions",
            "References time in all conversations"
        ],
        "contradictions": "Obsessed with precision but lives in chaos",
        "voice_markers": "Formal speech, no contractions, time-related metaphors"
    }
    theme = "Can broken moments be truly repaired, or only replaced?"
    
    print("\nRunning full pipeline...")
    try:
        revised_draft = pipeline.run_full_pipeline(idea, character, theme, genre=None)
        
        print(f"✓ Pipeline complete!")
        print(f"  Word count: {revised_draft['word_count']}")
        
        # Show voice consistency if available
        revisions = revised_draft.get("revisions", {})
        voice_consistency = revisions.get("voice_consistency_check")
        if voice_consistency:
            print(f"  Voice consistency score: {voice_consistency.get('overall_consistency_score', 0):.3f}")
            print(f"  Status: {voice_consistency.get('summary', {}).get('overall_status', 'unknown')}")
        
    except Exception as e:
        print(f"  Pipeline error: {e}")
        print("  (This may occur if LLM is not configured)")


if __name__ == "__main__":
    # Run the detailed step-by-step example
    main()
    
    # Optionally run the full pipeline example
    # Uncomment to try:
    # example_full_pipeline()

