#!/usr/bin/env python3
"""Test script to find the import error source."""
import sys
import traceback

# Try to patch importlib.metadata before any imports
try:
    import importlib_metadata
    import importlib.metadata as stdlib_metadata
    # Patch stdlib with backport if needed
    if not hasattr(stdlib_metadata, 'packages_distributions'):
        if hasattr(importlib_metadata, 'packages_distributions'):
            stdlib_metadata.packages_distributions = importlib_metadata.packages_distributions
            print("Patched importlib.metadata.packages_distributions")
except Exception as e:
    print(f"Warning: Could not patch importlib.metadata: {e}")

# Now try importing the app
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    import os
    from flask import Flask
    from flask_limiter import Limiter
    print("All imports successful!")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

