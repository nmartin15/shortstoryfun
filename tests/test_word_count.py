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
    """Tests that MAX_WORD_COUNT constant is set correctly."""
    assert MAX_WORD_COUNT == 7500


def test_word_count_basic():
    """Tests basic word counting functionality."""
    validator = WordCountValidator()
    text = "This is a test sentence with seven words."
    # Actual count: This, is, a, test, sentence, with, seven, words = 8 words
    assert validator.count_words(text) == 8


def test_word_count_empty():
    """Tests word counting with empty text and None values."""
    validator = WordCountValidator()
    assert validator.count_words("") == 0
    assert validator.count_words(None) == 0


def test_word_count_invalid_type():
    """Tests that count_words raises TypeError for invalid input types."""
    validator = WordCountValidator()
    with pytest.raises(TypeError, match="count_words\\(\\) expects a string"):
        validator.count_words(123)
    with pytest.raises(TypeError, match="count_words\\(\\) expects a string"):
        validator.count_words([])
    with pytest.raises(TypeError, match="count_words\\(\\) expects a string"):
        validator.count_words({})
    with pytest.raises(TypeError, match="count_words\\(\\) expects a string"):
        validator.count_words(True)


def test_word_count_validation_under_limit():
    """Tests validation when word count is under the limit."""
    validator = WordCountValidator(max_words=100)
    text = "This is a short text with only ten words total here."
    # Actual count: This, is, a, short, text, with, only, ten, words, total, here = 11 words
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 11
    assert is_valid is True


def test_word_count_validation_over_limit():
    """Tests validation when word count exceeds the limit."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 9
    assert is_valid is False


def test_word_count_validation_raises_error():
    """Tests that validation raises WordCountError when over limit and raise_error=True."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    with pytest.raises(WordCountError):
        validator.validate(text, raise_error=True)


def test_get_remaining_words():
    """Tests calculation of remaining words before hitting the limit."""
    validator = WordCountValidator(max_words=100)
    text = "This has ten words total in this sentence here."
    # Actual count: This, has, ten, words, total, in, this, sentence, here = 9 words
    remaining = validator.get_remaining_words(text)
    assert remaining == 91  # 100 - 9


def test_check_impact_ratio():
    """Tests impact ratio calculation for word efficiency."""
    validator = WordCountValidator(max_words=100)
    text = "This has ten words total in this sentence here."
    # Actual count: This, has, ten, words, total, in, this, sentence, here = 9 words
    ratio = validator.check_impact_ratio(text)
    assert ratio == 0.09  # 9/100


def test_check_impact_ratio_over_budget():
    """Tests impact ratio calculation when word count exceeds the budget."""
    validator = WordCountValidator(max_words=5)
    text = "This is a longer text that exceeds the limit."
    ratio = validator.check_impact_ratio(text)
    assert ratio == 0.0  # Over budget = no efficiency

