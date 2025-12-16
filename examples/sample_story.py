"""
Example: Using the Short Story Pipeline

This demonstrates how to use the pipeline to create a short story
with distinctive voice and memorable characters.
"""

from src.shortstory.pipeline import ShortStoryPipeline


def main():
    """Example pipeline usage."""
    pipeline = ShortStoryPipeline()
    
    # Stage 1: Premise capture with validation
    idea = "A lighthouse keeper who collects lost voices in glass jars"
    character = {
        "name": "Mara",
        "quirks": ["Never speaks above a whisper", "Counts everything in sevens"],
        "contradictions": "Fiercely protective but terrified of connection",
        "voice_markers": "Uses maritime metaphors, speaks in fragments"
    }
    theme = "What happens to the stories we never tell?"
    
    print("Capturing premise with distinctiveness validation...")
    premise = pipeline.capture_premise(idea, character, theme, validate=True)
    print(f"✓ Premise captured: {premise['idea']}")
    
    # Show validation results
    if premise.get("validation"):
        validation = premise["validation"]
        print(f"  Distinctiveness score: {validation['distinctiveness']['average_score']:.2f}")
        if validation["warnings"]:
            print(f"  Warnings: {len(validation['warnings'])}")
        if validation["errors"]:
            print(f"  Errors: {validation['errors']}")
    
    # Demonstrate word count validation
    print("\nTesting word count validation...")
    test_text = "This is a test sentence with exactly ten words here."
    word_count = pipeline.word_validator.count_words(test_text)
    remaining = pipeline.word_validator.get_remaining_words(test_text)
    print(f"  Test text: {word_count} words")
    print(f"  Remaining budget: {remaining} words")
    
    # Run full pipeline (when other stages are implemented)
    # print("\nRunning full pipeline...")
    # revised_draft = pipeline.run_full_pipeline(idea, character, theme)
    # print(f"✓ Story complete: {revised_draft['word_count']} words")


if __name__ == "__main__":
    main()

