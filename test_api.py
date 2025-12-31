#!/usr/bin/env python3
"""
Test the web API endpoints with improved validation and error handling.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, Tuple

BASE_URL = "http://localhost:5000"


class APIValidationError(Exception):
    """Custom exception for API validation errors."""
    pass


def validate_health_response(response: requests.Response) -> Dict[str, Any]:
    """
    Validate health endpoint response.
    
    Args:
        response: HTTP response object
        
    Returns:
        Parsed JSON response
        
    Raises:
        APIValidationError: If response is invalid
        requests.exceptions.HTTPError: If HTTP error occurred
    """
    response.raise_for_status()
    
    if response.status_code != 200:
        raise APIValidationError(f"Expected status 200, got {response.status_code}")
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise APIValidationError(f"Invalid JSON response: {e}")
    
    if not isinstance(data, dict):
        raise APIValidationError(f"Expected dict response, got {type(data).__name__}")
    
    if "status" not in data:
        raise APIValidationError("Response missing 'status' field")
    
    if data.get("status") != "ok":
        raise APIValidationError(f"Expected status 'ok', got '{data.get('status')}'")
    
    return data


def validate_genres_response(response: requests.Response) -> Dict[str, Any]:
    """
    Validate genres endpoint response.
    
    Args:
        response: HTTP response object
        
    Returns:
        Parsed JSON response with genres list
        
    Raises:
        APIValidationError: If response is invalid
        requests.exceptions.HTTPError: If HTTP error occurred
    """
    response.raise_for_status()
    
    if response.status_code != 200:
        raise APIValidationError(f"Expected status 200, got {response.status_code}")
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise APIValidationError(f"Invalid JSON response: {e}")
    
    if not isinstance(data, dict):
        raise APIValidationError(f"Expected dict response, got {type(data).__name__}")
    
    if "genres" not in data:
        raise APIValidationError("Response missing 'genres' field")
    
    genres = data.get("genres", [])
    if not isinstance(genres, list):
        raise APIValidationError(f"Expected genres to be a list, got {type(genres).__name__}")
    
    if len(genres) == 0:
        raise APIValidationError("Genres list is empty")
    
    # Validate each genre is a string
    for genre in genres:
        if not isinstance(genre, str):
            raise APIValidationError(f"Expected genre to be string, got {type(genre).__name__}")
        if len(genre.strip()) == 0:
            raise APIValidationError("Found empty genre name")
    
    return data


def validate_story_response(response: requests.Response) -> Dict[str, Any]:
    """
    Validate story generation endpoint response.
    
    Args:
        response: HTTP response object
        
    Returns:
        Parsed JSON response with story data
        
    Raises:
        APIValidationError: If response is invalid
        requests.exceptions.HTTPError: If HTTP error occurred
    """
    if response.status_code != 200:
        # Try to get error details
        try:
            error_data = response.json()
            error_msg = error_data.get("error", response.text)
        except (json.JSONDecodeError, ValueError):
            error_msg = response.text
        
        raise APIValidationError(
            f"Story generation failed with status {response.status_code}: {error_msg}"
        )
    
    response.raise_for_status()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise APIValidationError(f"Invalid JSON response: {e}")
    
    if not isinstance(data, dict):
        raise APIValidationError(f"Expected dict response, got {type(data).__name__}")
    
    # Validate required fields
    required_fields = ["success", "story_id", "story", "word_count", "max_words"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise APIValidationError(f"Response missing required fields: {', '.join(missing_fields)}")
    
    # Validate field types
    if not isinstance(data.get("success"), bool):
        raise APIValidationError("Field 'success' must be a boolean")
    
    if not isinstance(data.get("story_id"), str):
        raise APIValidationError("Field 'story_id' must be a string")
    
    if len(data.get("story_id", "").strip()) == 0:
        raise APIValidationError("Field 'story_id' cannot be empty")
    
    if not isinstance(data.get("story"), str):
        raise APIValidationError("Field 'story' must be a string")
    
    if len(data.get("story", "").strip()) == 0:
        raise APIValidationError("Field 'story' cannot be empty")
    
    if not isinstance(data.get("word_count"), int):
        raise APIValidationError("Field 'word_count' must be an integer")
    
    if data.get("word_count", 0) < 0:
        raise APIValidationError("Field 'word_count' cannot be negative")
    
    if not isinstance(data.get("max_words"), int):
        raise APIValidationError("Field 'max_words' must be an integer")
    
    if data.get("max_words", 0) <= 0:
        raise APIValidationError("Field 'max_words' must be positive")
    
    if data.get("word_count", 0) > data.get("max_words", 0):
        raise APIValidationError(
            f"Word count ({data.get('word_count')}) exceeds max_words ({data.get('max_words')})"
        )
    
    # Validate optional fields if present
    if "premise" in data and not isinstance(data["premise"], dict):
        raise APIValidationError("Field 'premise' must be a dict if present")
    
    if "outline" in data and not isinstance(data["outline"], dict):
        raise APIValidationError("Field 'outline' must be a dict if present")
    
    return data


def test_health() -> bool:
    """
    Test health endpoint with validation.
    
    Returns:
        True if test passes, False otherwise
    """
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = validate_health_response(response)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {data}\n")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}\n")
        return False
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Request timeout: {e}\n")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP error: {e}\n")
        return False
    except APIValidationError as e:
        print(f"   ❌ Validation error: {e}\n")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}\n")
        return False


def test_genres() -> bool:
    """
    Test genres endpoint with validation.
    
    Returns:
        True if test passes, False otherwise
    """
    print("📚 Testing genres endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/genres", timeout=5)
        data = validate_genres_response(response)
        genres = data.get("genres", [])
        print(f"   Status: {response.status_code}")
        print(f"   Available genres ({len(genres)}): {', '.join(genres)}\n")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}\n")
        return False
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Request timeout: {e}\n")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP error: {e}\n")
        return False
    except APIValidationError as e:
        print(f"   ❌ Validation error: {e}\n")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}\n")
        return False


def test_generate_story() -> Tuple[bool, Optional[str]]:
    """
    Test story generation endpoint with validation.
    
    Returns:
        Tuple of (success: bool, story_id: Optional[str])
    """
    print("✨ Testing story generation...")
    
    payload = {
        "idea": "A lighthouse keeper who collects lost voices in glass jars",
        "character": {
            "name": "Mara",
            "description": "A lighthouse keeper with an unusual collection",
            "quirks": ["Never speaks above a whisper"],
            "contradictions": "Fiercely protective but terrified of connection"
        },
        "theme": "What happens to the stories we never tell?",
        "genre": "Literary"
    }
    
    print(f"   Sending request with idea: {payload['idea']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # Story generation may take longer
        )
        
        data = validate_story_response(response)
        
        print(f"   Status: {response.status_code}")
        print(f"   ✅ Story generated!")
        print(f"   Story ID: {data.get('story_id')}")
        print(f"   Word count: {data.get('word_count')} / {data.get('max_words')}")
        print(f"   Story preview (first 200 chars):")
        story = data.get('story', '')
        print(f"   {story[:200]}...\n")
        return True, data.get('story_id')
        
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {e}\n")
        return False, None
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Request timeout: {e}\n")
        return False, None
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP error: {e}\n")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}\n")
        return False, None
    except APIValidationError as e:
        print(f"   ❌ Validation error: {e}\n")
        return False, None
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}\n")
        return False, None


def test_generate_story_validation() -> bool:
    """
    Test story generation with invalid input to verify validation.
    
    Returns:
        True if validation works correctly, False otherwise
    """
    print("🔍 Testing story generation validation...")
    
    # Test with missing idea
    try:
        payload = {
            "character": {"name": "Test"},
            "theme": "Test theme",
            "genre": "General Fiction"
        }
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("   ✅ Validation correctly rejected missing idea\n")
            return True
        else:
            print(f"   ❌ Expected status 400 for missing idea, got {response.status_code}\n")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}\n")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}\n")
        return False


if __name__ == "__main__":
    print("🧪 Testing Short Story Pipeline API\n")
    print("=" * 60)
    
    # Check if server is running
    if not test_health():
        print("❌ Server is not running or health check failed!")
        print("   Start it with: python app.py")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    tests_failed = 0
    
    if test_genres():
        tests_passed += 1
    else:
        tests_failed += 1
    
    success, story_id = test_generate_story()
    if success:
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_generate_story_validation():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("=" * 60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    
    if tests_failed == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

