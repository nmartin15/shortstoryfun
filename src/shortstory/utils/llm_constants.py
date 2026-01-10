"""
Constants for LLM story generation.

This module centralizes all magic numbers and configuration values
used in story generation, revision, and token calculation.
"""

# Story Word Count Limits
# These define the acceptable range for generated story narratives (prose only, not metadata)

# Minimum word count for a professional short story (narrative prose only)
STORY_MIN_WORDS = 4000

# Maximum word count for story narrative (capped to ensure quality)
STORY_MAX_WORDS = 6500

# Default maximum words parameter (can be overridden by user)
STORY_DEFAULT_MAX_WORDS = 7500

# Word count threshold for considering a story "full-length"
# Stories at or above this threshold get maximum token allocation
FULL_LENGTH_STORY_THRESHOLD = 3000

# Industry standard word count range for short stories
INDUSTRY_MIN_WORDS = 3000
INDUSTRY_MAX_WORDS = 7500

# Target word count calculation
# When calculating target word count, use this ratio of max words
TARGET_WORD_COUNT_RATIO = 0.75  # e.g., 6500 * 0.75 = 4875 words

# Token Limits for Gemini API
# Maximum output tokens supported by Gemini models
GEMINI_MAX_OUTPUT_TOKENS = 8192

# Minimum tokens to request for full-length stories
# This ensures enough space for 3000-5000 word stories
MIN_TOKENS_FOR_FULL_STORY = 6000

# Default minimum tokens for shorter stories
DEFAULT_MIN_TOKENS = 4000

# Token Estimation
# Estimated tokens per word (used for calculating token needs from word count)
TOKENS_PER_WORD_ESTIMATE = 1.5

# Response overhead tokens (for formatting, special tokens, etc.)
RESPONSE_OVERHEAD_TOKENS = 100

# Token Buffer Multipliers
# Multiplier for token estimation buffer (to avoid truncation)
TOKEN_BUFFER_MULTIPLIER = 1.05
TOKEN_BUFFER_ADDITION = 10

# Character-based token estimation
# Rough estimate: 1 token ≈ 4 characters (accounts for punctuation)
CHARS_PER_TOKEN_ESTIMATE = 4.0

# Word-based token estimation
# Average tokens per word for English text
TOKENS_PER_WORD_CHAR_ESTIMATE = 1.4

# Word count expansion multiplier
# When expanding stories, use this multiplier for token calculation
WORD_COUNT_EXPANSION_MULTIPLIER = 1.2

# Standard Story Structure Template
# Consistent 5-part structure for all stories (maximizes learnability)
# Each story follows this architecture regardless of genre

# A. Opening section
OPENING_MIN_WORDS = 500
OPENING_MAX_WORDS = 800
OPENING_TARGET_WORDS = 650  # Midpoint of range

# B. Rising Action section
RISING_ACTION_MIN_WORDS = 1200
RISING_ACTION_MAX_WORDS = 1800
RISING_ACTION_TARGET_WORDS = 1500  # Midpoint of range

# C. Midpoint Shift section
MIDPOINT_SHIFT_MIN_WORDS = 300
MIDPOINT_SHIFT_MAX_WORDS = 600
MIDPOINT_SHIFT_TARGET_WORDS = 450  # Midpoint of range

# D. Climax section
CLIMAX_MIN_WORDS = 800
CLIMAX_MAX_WORDS = 1200
CLIMAX_TARGET_WORDS = 1000  # Midpoint of range

# E. Resolution section
RESOLUTION_MIN_WORDS = 400
RESOLUTION_MAX_WORDS = 700
RESOLUTION_TARGET_WORDS = 550  # Midpoint of range

# Total structure word count range
STRUCTURE_TOTAL_MIN_WORDS = (
    OPENING_MIN_WORDS +
    RISING_ACTION_MIN_WORDS +
    MIDPOINT_SHIFT_MIN_WORDS +
    CLIMAX_MIN_WORDS +
    RESOLUTION_MIN_WORDS
)  # 3,200 words

STRUCTURE_TOTAL_MAX_WORDS = (
    OPENING_MAX_WORDS +
    RISING_ACTION_MAX_WORDS +
    MIDPOINT_SHIFT_MAX_WORDS +
    CLIMAX_MAX_WORDS +
    RESOLUTION_MAX_WORDS
)  # 5,100 words

STRUCTURE_TOTAL_TARGET_WORDS = (
    OPENING_TARGET_WORDS +
    RISING_ACTION_TARGET_WORDS +
    MIDPOINT_SHIFT_TARGET_WORDS +
    CLIMAX_TARGET_WORDS +
    RESOLUTION_TARGET_WORDS
)  # 4,150 words

