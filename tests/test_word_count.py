"""
Tests for word count validation.
"""

import pytest
from src.shortstory.utils.word_count import (
    WordCountValidator,
    WordCountError,
    MAX_WORD_COUNT,
)


def test_max_word_count_constant():
    """Test that MAX_WORD_COUNT is set correctly."""
    assert MAX_WORD_COUNT == 7500


def test_word_count_basic():
    """Test basic word counting."""
    validator = WordCountValidator()
    text = "This is a test sentence with seven words."
    assert validator.count_words(text) == 7


def test_word_count_empty():
    """Test word counting with empty text."""
    validator = WordCountValidator()
    assert validator.count_words("") == 0
    assert validator.count_words(None) == 0


def test_word_count_validation_under_limit():
    """Test validation when under word limit."""
    validator = WordCountValidator(max_words=100)
    text = "This is a short text with only ten words total here."
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 10
    assert is_valid is True


def test_word_count_validation_over_limit():
    """Test validation when over word limit."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 9
    assert is_valid is False


def test_word_count_validation_raises_error():
    """Test that validation raises error when over limit."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    with pytest.raises(WordCountError):
        validator.validate(text, raise_error=True)


def test_get_remaining_words():
    """Test calculation of remaining words."""
    validator = WordCountValidator(max_words=100)
    text = "This has ten words total in this sentence here."
    remaining = validator.get_remaining_words(text)
    assert remaining == 90  # 100 - 10


def test_check_impact_ratio():
    """Test impact ratio calculation."""
    validator = WordCountValidator(max_words=100)
    text = "This has ten words total in this sentence here."
    ratio = validator.check_impact_ratio(text)
    assert ratio == 0.1  # 10/100


def test_check_impact_ratio_over_budget():
    """Test impact ratio when over budget."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    ratio = validator.check_impact_ratio(text)
    assert ratio == 0.0  # Over budget = no efficiency

