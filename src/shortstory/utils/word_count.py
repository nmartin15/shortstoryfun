"""
Word count validation and enforcement.

Enforces the ≤ 7500 word limit while maximizing impact per word.
"""

from typing import Optional, Tuple

MAX_WORD_COUNT = 7500


class WordCountError(Exception):
    """Raised when word count exceeds maximum."""
    
    def __init__(self, word_count: int, max_words: int) -> None:
        """
        Initialize error with word count details.
        
        Args:
            word_count: Actual word count
            max_words: Maximum allowed word count
        """
        self.word_count = word_count
        self.max_words = max_words
        message = f"Word count {word_count} exceeds maximum of {max_words}"
        super().__init__(message)


class WordCountValidator:
    """
    Validates and enforces word count constraints.
    
    The philosophy is to maximize impact per word, not just stay under limit.
    """
    
    def __init__(self, max_words: int = MAX_WORD_COUNT) -> None:
        """
        Initialize validator.
        
        Args:
            max_words: Maximum allowed word count (default: 7500)
        """
        self.max_words = max_words
    
    def count_words(self, text: Optional[str]) -> int:
        """
        Count words in text.
        
        Uses whitespace splitting - treats punctuation as part of words.
        Empty strings and None return 0.
        
        Args:
            text: String to count words in (None and empty strings return 0)
        
        Returns:
            Word count as integer (0 for None or empty strings)
        
        Raises:
            TypeError: If text is not a string (after None/empty handling)
        """
        if text is None or text == "":
            return 0
        if not isinstance(text, str):
            raise TypeError(f"count_words() expects a string, got {type(text).__name__}")
        
        # Split on whitespace and filter out empty strings
        words = [w for w in text.split() if w.strip()]
        return len(words)
    
    def validate(self, text: str, raise_error: bool = True) -> Tuple[int, bool]:
        """
        Validate word count against maximum.
        
        Args:
            text: Text to validate
            raise_error: If True, raise WordCountError on violation
        
        Returns:
            Tuple of (word_count, is_valid)
        """
        word_count = self.count_words(text)
        is_valid = word_count <= self.max_words
        
        if not is_valid and raise_error:
            raise WordCountError(word_count, self.max_words)
        
        return word_count, is_valid
    
    def get_remaining_words(self, text: str) -> int:
        """
        Get remaining words available.
        
        Args:
            text: Current text
        
        Returns:
            Number of words remaining before hitting limit
        """
        word_count = self.count_words(text)
        remaining = max(0, self.max_words - word_count)
        return remaining
    
    def check_impact_ratio(self, text: str, target_words: Optional[int] = None) -> float:
        """
        Calculate impact ratio (words used vs. available).
        
        Higher ratio = more efficient use of word budget.
        
        Args:
            text: Text to analyze
            target_words: Target word count (default: max_words)
        
        Returns:
            Float between 0 and 1 representing efficiency
        """
        if target_words is None:
            target_words = self.max_words
        
        word_count = self.count_words(text)
        if target_words == 0:
            return 0.0
        
        # Efficiency: how close to target without exceeding
        if word_count > target_words:
            return 0.0  # Over budget = no efficiency
        
        return word_count / target_words
