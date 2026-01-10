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


def test_word_count_complex_punctuation_and_whitespace():
    """Tests word counting with complex punctuation and whitespace."""
    validator = WordCountValidator()
    
    # Multiple spaces, leading/trailing spaces, mixed punctuation
    text1 = "  Hello  world! How's it going? (Fine, thanks.)  "
    # Split result: ['Hello', 'world!', "How's", 'it', 'going?', '(Fine,', 'thanks.)']
    assert validator.count_words(text1) == 7  # Hello, world!, How's, it, going?, (Fine,, thanks.)
    
    # Hyphenated words
    text2 = "This is a well-structured document."
    # Split result: ['This', 'is', 'a', 'well-structured', 'document.']
    assert validator.count_words(text2) == 5  # This, is, a, well-structured, document.
    
    # Numbers and symbols as words
    text3 = "Code 123 often uses $ymbols."
    # Split result: ['Code', '123', 'often', 'uses', '$ymbols.']
    assert validator.count_words(text3) == 5  # Code, 123, often, uses, $ymbols.
    
    # Empty string with spaces
    text4 = "   "
    assert validator.count_words(text4) == 0
    
    # Text with newlines and tabs
    text5 = "Line1\nLine2\tLine3"
    # Split result: ['Line1', 'Line2', 'Line3']
    assert validator.count_words(text5) == 3  # Line1, Line2, Line3


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


def test_word_count_unicode_characters():
    """Tests word counting with Unicode characters."""
    validator = WordCountValidator()
    # Unicode text with various characters
    text = "Hello 世界 café naïve résumé"
    # Should count: Hello, 世界, café, naïve, résumé = 5 words
    assert validator.count_words(text) == 5


def test_word_count_mixed_unicode_ascii():
    """Tests word counting with mixed Unicode and ASCII."""
    validator = WordCountValidator()
    text = "The café serves 咖啡 and tea"
    # Should count: The, café, serves, 咖啡, and, tea = 6 words
    assert validator.count_words(text) == 6


def test_word_count_very_long_text():
    """Tests word counting with very long text (performance edge case)."""
    validator = WordCountValidator()
    # Create a very long text (10000 words)
    long_text = "word " * 10000
    assert validator.count_words(long_text) == 10000


def test_word_count_at_limit():
    """Tests word count validation exactly at the limit."""
    validator = WordCountValidator(max_words=10)
    text = "one two three four five six seven eight nine ten"
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 10
    assert is_valid is True  # At limit should be valid


def test_word_count_one_over_limit():
    """Tests word count validation one word over the limit."""
    validator = WordCountValidator(max_words=10)
    text = "one two three four five six seven eight nine ten eleven"
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert word_count == 11
    assert is_valid is False


def test_word_count_zero_max_words():
    """Tests edge case with zero max_words."""
    validator = WordCountValidator(max_words=0)
    text = "any text"
    word_count, is_valid = validator.validate(text, raise_error=False)
    assert is_valid is False
    # Empty text should be valid with zero max
    word_count_empty, is_valid_empty = validator.validate("", raise_error=False)
    assert is_valid_empty is True


def test_get_remaining_words_at_limit():
    """Tests remaining words calculation when at limit."""
    validator = WordCountValidator(max_words=10)
    text = "one two three four five six seven eight nine ten"
    remaining = validator.get_remaining_words(text)
    assert remaining == 0


def test_get_remaining_words_over_limit():
    """Tests remaining words calculation when over limit."""
    validator = WordCountValidator(max_words=10)
    text = "one two three four five six seven eight nine ten eleven"
    remaining = validator.get_remaining_words(text)
    assert remaining == 0  # Should not go negative
