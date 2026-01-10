python
# In test_story_generation_api.py
import requests

def test_story_generation():
        if response.status_code != 200:
        # ...

        
        # Extract just the story prose (after "## Story" header)
        story_text = data.get('story', '')
        if not story_text:
            story_prose = story_section_match.group(1).strip()
            _log_api_error(response) # Also log full response for non-success cases if not already 200
        else:
            # If no "## Story" header, try to extract from the end
            # Look for the actual story content (not metadata)
        # ...
            story_prose = story_text
        
        word_count = count_words(story_prose)
        api_max_words = data.get('max_words', 0) # Get max_words from API response
        
        print(f"\n✅ Story generated successfully!")
        print(f"   Story ID: {data.get('story_id', 'N/A')}")
        print(f"   Word count: {word_count:,} words / API Max: {api_max_words:,} words")
        print(f"   Total response length: {len(story_text):,} characters")
        print(f"   Story prose length: {len(story_prose):,} characters")
        
        # ... (markdown header check)

        # Check word count against API-provided max_words and constants
        # Use constants from llm_constants for consistent thresholds
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            FULL_LENGTH_STORY_THRESHOLD,
            INDUSTRY_MIN_WORDS
        )
        
        # Use industry minimum as the target for "full-length" stories
        # This aligns with the actual API constraints
        target_min_words = INDUSTRY_MIN_WORDS  # 3000 words from constants
        
        if word_count < STORY_MIN_WORDS:
            print(f"\n❌ FAIL: Story is too short ({word_count} words). Minimum required: {STORY_MIN_WORDS:,} words.")
            return False
        elif api_max_words > 0 and word_count > api_max_words:
            print(f"\n❌ FAIL: Story word count ({word_count}) exceeds API's reported max words ({api_max_words}).")
            return False
        elif word_count < target_min_words:
            print(f"\n⚠️  WARNING: Story is below full-length threshold ({word_count} words). Target minimum: {target_min_words:,} words.")
            # Don't fail, just warn - stories can be shorter if intentionally requested
        else:
            print(f"\n✅ Story length is good ({word_count:,} words). Target min: {target_min_words:,} words. API Max: {api_max_words:,} words.")

        # ... (rest of checks)