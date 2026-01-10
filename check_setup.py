#!/usr/bin/env python3
"""
Setup verification script for Short Story Pipeline.

Checks if Google Gemini API is configured correctly.
"""

import sys
import os
import logging

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed yet, that's okay


def check_api_key() -> tuple[bool, str]:
    """Check if Google API key is set."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return True, "GOOGLE_API_KEY is set"
    return False, "GOOGLE_API_KEY not set"


def check_python_dependencies() -> tuple[bool, str]:
    """Check if Python dependencies are installed."""
    try:
        import google.generativeai
        return True, "google-generativeai package is installed"
    except ImportError:
        return False, "google-generativeai package not installed. Run: pip install -r requirements.txt"


def check_api_connection() -> tuple[bool, str]:
    """Check if we can connect to Google API."""
    # Configure logging for this script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        from src.shortstory.utils.llm import get_default_client
        client = get_default_client()
        is_available = client.check_availability()
        
        if is_available:
            return True, f"API connection successful (model: {client.model_name})"
        else:
            logger.warning("API key set but model availability check returned False")
            return False, "API key set but connection failed. Check your API key."
    except ValueError as e:
        logger.error(f"API configuration error: {e}", exc_info=True)
        return False, f"API configuration error: {e}"
    except ImportError as e:
        logger.error(f"Import error: {e}", exc_info=True)
        return False, f"Import error: {e}. Ensure dependencies are installed."
    except ConnectionError as e:
        logger.error(f"Network connection error: {e}", exc_info=True)
        return False, f"Network connection error: {e}. Check your internet connection."
    except TimeoutError as e:
        logger.error(f"API request timeout: {e}", exc_info=True)
        return False, f"API request timeout: {e}. The API may be temporarily unavailable."
    except Exception as e:
        # Log full exception details with context for debugging
        logger.exception(
            f"API connection failed - Error type: {type(e).__name__}, "
            f"Error message: {str(e)}"
        )
        return False, f"Connection error: {e}"


def main() -> int:
    """
    Run all setup checks.
    
    Performs comprehensive setup verification including:
    - Google API key configuration check
    - Python dependencies installation check
    - API connection test (if key and dependencies are available)
    
    Returns:
        int: Exit code - 0 if all checks pass, 1 if any check fails.
    """
    print("🔍 Checking Short Story Pipeline Setup...\n")
    
    all_checks_passed = True
    
    # Check 1: API key
    print("1. Checking Google API key...")
    key_ok, msg = check_api_key()
    if key_ok:
        print(f"   ✅ {msg}\n")
    else:
        print(f"   ❌ {msg}")
        print("   📝 To get an API key:")
        print("      1. Go to https://makersuite.google.com/app/apikey")
        print("      2. Click 'Create API Key'")
        print("      3. Set: export GOOGLE_API_KEY=your_key_here\n")
        all_checks_passed = False
    
    # Check 2: Python dependencies
    print("2. Checking Python dependencies...")
    deps_ok, msg = check_python_dependencies()
    if deps_ok:
        print(f"   ✅ {msg}\n")
    else:
        print(f"   ❌ {msg}\n")
        all_checks_passed = False
    
    # Check 3: API connection (only if key is set)
    if key_ok and deps_ok:
        print("3. Checking API connection...")
        conn_ok, msg = check_api_connection()
        if conn_ok:
            print(f"   ✅ {msg}\n")
        else:
            print(f"   ⚠️  {msg}\n")
            all_checks_passed = False
    
    # Summary
    print("=" * 50)
    if all_checks_passed:
        print("✅ All checks passed! Setup is complete.")
        print("   You can now run: python app.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("   See SETUP_GOOGLE.md for detailed instructions.")
    print("=" * 50)
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())
