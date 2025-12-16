"""
Word count validation and enforcement.

Enforces the ≤ 7500 word limit while maximizing impact per word.
"""

MAX_WORD_COUNT = 7500


class WordCountError(Exception):
    """Raised when word count exceeds maximum."""
    pass


class WordCountValidator:
    """
    Validates and enforces word count constraints.
    
    The philosophy is to maximize impact per word, not just stay under limit.
    """
    
    def __init__(self, max_words=MAX_WORD_COUNT):
        """
        Initialize validator.
        
        Args:
            max_words: Maximum allowed word count (default: 7500)
        """
        self.max_words = max_words
    
    def count_words(self, text):
        """
        Count words in text.
        
        Args:
            text: String to count words in
        
        Returns:
            Word count as integer
        """
        if not text or not isinstance(text, str):
            return 0
        # Simple word count - split on whitespace
        words = text.split()
        return len(words)
    
    def validate(self, text, raise_error=True):
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
            raise WordCountError(
                f"Word count {word_count} exceeds maximum of {self.max_words}"
            )
        
        return word_count, is_valid
    
    def get_remaining_words(self, text):
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
    
    def check_impact_ratio(self, text, target_words=None):
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

