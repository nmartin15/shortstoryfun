#!/usr/bin/env python3
"""
Test script to verify story generation API works correctly.
Tests for full-length stories, no markdown headers, and proper formatting.
"""

import requests
import json
import re
import sys

API_BASE = "http://localhost:5001/api"

def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())

def check_for_markdown_headers(text):
    """Check if text contains markdown headers."""
    # Check for markdown headers like ## Setup, ## Complication, etc.
    markdown_header_pattern = r'^#+\s+\w+'
    lines = text.split('\n')
    headers_found = []
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        if re.match(markdown_header_pattern, line.strip()):
            headers_found.append((i+1, line.strip()))
    return headers_found

def test_story_generation():
    """Test story generation endpoint."""
    print("=" * 60)
    print("Testing Story Generation API")
    print("=" * 60)
    
    # Test data
    test_data = {
        "idea": "A lighthouse keeper who collects lost voices in glass jars",
        "character": {
            "name": "Mara",
            "description": "A lighthouse keeper who never speaks above a whisper. She's fiercely protective of those she loves but terrified of forming deep connections."
        },
        "theme": "What happens to the stories we never tell?",
        "genre": "General Fiction"
    }
    
    print(f"\n📝 Generating story with:")
    print(f"   Idea: {test_data['idea']}")
    print(f"   Character: {test_data['character']['name']}")
    print(f"   Theme: {test_data['theme']}")
    print(f"   Genre: {test_data['genre']}")
    
    try:
        print("\n⏳ Sending request to API...")
        response = requests.post(
            f"{API_BASE}/generate",
            json=test_data,
            timeout=300  # 5 minute timeout for long stories
        )
        
        if response.status_code != 200:
            print(f"❌ API returned error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        data = response.json()
        
        if not data.get('success', True):
            print(f"❌ Generation failed: {data.get('error', 'Unknown error')}")
            return False
        
        # Extract story text
        story_text = data.get('story', '')
        if not story_text:
            print("❌ No story text in response")
            return False
        
        # Extract just the story prose (after "## Story" header)
        story_section_match = re.search(r'## Story\s*\n\s*\n(.*?)(?=\n\*\*Constraints|\Z)', story_text, re.DOTALL)
        if story_section_match:
            story_prose = story_section_match.group(1).strip()
        else:
            # If no "## Story" header, try to extract from the end
            # Look for the actual story content (not metadata)
            story_prose = story_text
        
        word_count = count_words(story_prose)
        
        print(f"\n✅ Story generated successfully!")
        print(f"   Story ID: {data.get('story_id', 'N/A')}")
        print(f"   Word count: {word_count:,} words")
        print(f"   Total response length: {len(story_text):,} characters")
        print(f"   Story prose length: {len(story_prose):,} characters")
        
        # Check for markdown headers in story prose
        headers = check_for_markdown_headers(story_prose)
        if headers:
            print(f"\n⚠️  WARNING: Found markdown headers in story:")
            for line_num, header in headers:
                print(f"   Line {line_num}: {header}")
        else:
            print(f"\n✅ No markdown headers found in story prose")
        
        # Check word count
        if word_count < 1000:
            print(f"\n❌ FAIL: Story is too short ({word_count} words). Expected at least 2,000 words.")
            return False
        elif word_count < 2000:
            print(f"\n⚠️  WARNING: Story is shorter than target ({word_count} words). Expected 2,000+ words.")
        else:
            print(f"\n✅ Story length is good ({word_count:,} words)")
        
        # Check if story appears complete (ends with punctuation)
        if story_prose and not story_prose.rstrip().endswith(('.', '!', '?', '"', "'")):
            print(f"\n⚠️  WARNING: Story may be incomplete (doesn't end with punctuation)")
            print(f"   Last 100 chars: ...{story_prose[-100:]}")
        else:
            print(f"\n✅ Story appears complete")
        
        # Show preview
        print(f"\n📖 Story preview (first 500 characters):")
        print("-" * 60)
        preview = story_prose[:500].replace('\n', ' ')
        print(preview + "..." if len(story_prose) > 500 else preview)
        print("-" * 60)
        
        # Check for common issues
        issues = []
        if word_count < 2000:
            issues.append(f"Story too short ({word_count} words)")
        if headers:
            issues.append(f"Contains markdown headers")
        if not story_prose.strip():
            issues.append("Story prose is empty")
        
        if issues:
            print(f"\n⚠️  Issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"\n✅ All checks passed!")
            return True
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to API at {API_BASE}")
        print("   Make sure the Flask app is running on port 5001")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timed out (took longer than 5 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_story_generation()
    sys.exit(0 if success else 1)

