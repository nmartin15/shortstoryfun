#!/usr/bin/env python3
"""
Quick test script for story generation.

Tests the pipeline directly without the web interface.
"""

from dotenv import load_dotenv
load_dotenv()

from src.shortstory.pipeline import ShortStoryPipeline  # noqa: E402

def test_story_generation():
    """Test generating a short story."""
    print("🧪 Testing Story Generation Pipeline\n")
    
    # Create pipeline
    pipeline = ShortStoryPipeline()
    
    # Test inputs
    idea = "A lighthouse keeper who collects lost voices in glass jars"
    character = {
        "name": "Mara",
        "description": "A lighthouse keeper with an unusual collection",
        "quirks": ["Never speaks above a whisper", "Counts everything in threes"],
        "contradictions": "Fiercely protective but terrified of connection"
    }
    theme = "What happens to the stories we never tell?"
    genre = "Literary"
    
    print(f"📝 Story Idea: {idea}")
    print(f"👤 Character: {character['name']}")
    print(f"🎭 Theme: {theme}")
    print(f"📚 Genre: {genre}\n")
    print("Generating story...\n")
    
    try:
        # Run the pipeline
        from src.shortstory.genres import get_genre_config
        pipeline.genre = genre
        pipeline.genre_config = get_genre_config(genre)
        
        pipeline.capture_premise(idea, character, theme, validate=True)  # Enable validation for proper testing
        pipeline.generate_outline(genre=genre)
        pipeline.scaffold(genre=genre)  # Sets internal state needed for drafting
        
        print("✅ Premise captured")
        print("✅ Outline generated")
        print("✅ Scaffold created")
        print("\n📖 Generating draft with LLM...\n")
        
        draft = pipeline.draft(use_llm=True)
        print(f"✅ Draft generated ({draft['word_count']} words)\n")
        
        print("🔧 Revising story...\n")
        revised = pipeline.revise(use_llm=True)
        print(f"✅ Revision complete ({revised['word_count']} words)\n")
        
        print("=" * 60)
        print("GENERATED STORY:")
        print("=" * 60)
        print(revised['text'])
        print("=" * 60)
        print(f"\n📊 Final word count: {revised['word_count']} / {pipeline.word_validator.max_words}")
        print("✅ Test completed successfully!")
        
    except ValueError as e:
        # Validation errors - specific handling
        print(f"❌ Validation Error: {e}")
        print("   This usually means the premise or story parameters are invalid.")
        import traceback
        traceback.print_exc()
        return False
    except RuntimeError as e:
        # LLM API errors - specific handling
        print(f"❌ LLM API Error: {e}")
        print("   Check your GOOGLE_API_KEY and API connection.")
        import traceback
        traceback.print_exc()
        return False
    except ImportError as e:
        # Missing dependencies - specific handling
        print(f"❌ Import Error: {e}")
        print("   Ensure all dependencies are installed: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        # Catch-all for unexpected errors - log full details
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
        print("   This is an unexpected error. Please report it with the traceback below.")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_story_generation()

