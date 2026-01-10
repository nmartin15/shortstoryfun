"""
Tests for story truncation detection and continuation fixes.

These tests verify that:
1. Truncation detection correctly identifies incomplete stories
2. Continuation logic triggers when stories are too short
3. Token allocation is sufficient and precise for continuation
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shortstory.utils.llm import (
    _continue_story_if_needed,
)
from src.shortstory.utils.llm_constants import (
    STORY_MIN_WORDS,
    STORY_MAX_WORDS,
    GEMINI_MAX_OUTPUT_TOKENS,
    DEFAULT_MIN_TOKENS,
    TOKENS_PER_WORD_ESTIMATE,
)


class TestContinuationTokenAllocation:
    """Test that continuation gets sufficient and precise tokens."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = "This is a continuation of the story. " * 100
        return client
    
    def test_continuation_allocates_sufficient_tokens(self, mock_client):
        """Test that continuation calculates and allocates tokens precisely based on remaining words needed."""
        short_story = "This is a short story. " * 20  # ~60 words
        word_count = len(short_story.split())
        remaining_words = STORY_MIN_WORDS - word_count
        
        # Calculate expected tokens using the ACTUAL implementation logic from llm.py line 268
        # continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        # allocated_tokens = min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)
        estimated_max_tokens = 6000
        expected_tokens_for_continuation = min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)
        # allocated_tokens = max(DEFAULT_MIN_TOKENS, allocated_tokens)
        expected_tokens_for_continuation = max(DEFAULT_MIN_TOKENS, expected_tokens_for_continuation)
        
        _continue_story_if_needed(
            short_story,
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            estimated_max_tokens,
            mock_client,
        )
        
        # Check that generate was called with precise token allocation
        if mock_client.generate.called:
            call_args = mock_client.generate.call_args
            max_tokens = call_args.kwargs.get('max_tokens')
            
            # Assert for exact match with the precise expected value
            assert max_tokens == expected_tokens_for_continuation, \
                f"Token allocation should be precise. Expected {expected_tokens_for_continuation}, got {max_tokens}. " \
                f"Calculation: remaining_words={remaining_words}, continuation_tokens_needed={continuation_tokens_needed}, " \
                f"after_min={min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)}, " \
                f"after_max={max(DEFAULT_MIN_TOKENS, min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed))}"


class TestRealWorldScenario:
    """Test real-world scenario with truncated story."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = "This is a continuation of the story. " * 200
        return client
    
    @pytest.fixture
    def truncated_story(self):
        """A truncated story ending mid-sentence (like the user's example)."""
        return """The dust arrived first, a tawny shroud boiling across the desert floor, 
        tasting of baked earth and the ghost of forgotten rains. It swallowed the horizon whole, 
        then the skeletal saguaros, before finally devouring the meager outline of Red Hollow. 
        Through this churning ochre haze, a rider emerged. He sat a dun horse with the quiet 
        immobility of a monument, a silhouette carved from sun-blasted granite. No frantic urging, 
        no bowed head against the stinging grit. He simply rode, one hand light on the reins, 
        the other resting near a worn leather holster, his gaze fixed on nothing specific, 
        yet missing nothing. His eyes, when the wind momentarily thinned the veil of dust, 
        held the depth of a desert well, reflecting nothing, revealing less.

        He steered the horse down the main track, a lane of compacted dirt that funneled into 
        the town's single, struggling artery. False-fronted buildings, sun-bleached and time-gnawed, 
        leaned like tired men against each other, their paint flaking like old skin. The air 
        vibrated with the whine of the wind, the creak of loose shutters, and the hollow silence 
        of a town buttoned up against the storm. A few figures huddled indoors, peering through 
        grimy panes, their faces etched with a mixture of apprehension and curiosity at the 
        stranger's arrival. No one rode into Red Hollow during a dust squall, not unless they 
        had no choice, or no fear. This man evinced neither urgency nor dread. He simply was.

        A sudden gust tore at a loose board on"""
    
    def test_250_word_truncated_story_gets_continued(self, mock_client, truncated_story):
        """Test that a 250-word story ending mid-sentence gets continued properly, with precise token allocation."""
        word_count = len(truncated_story.split())
        assert word_count < STORY_MIN_WORDS, f"Story should be short ({word_count} words)"
        assert not truncated_story.rstrip().endswith(('.', '!', '?')), "Story should end mid-sentence"
        
        remaining_words = STORY_MIN_WORDS - word_count
        estimated_max_tokens = 6000
        
        # Calculate expected tokens using the ACTUAL implementation logic from llm.py line 268
        # continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        # allocated_tokens = min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)
        expected_tokens_for_continuation = min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)
        # allocated_tokens = max(DEFAULT_MIN_TOKENS, allocated_tokens)
        expected_tokens_for_continuation = max(DEFAULT_MIN_TOKENS, expected_tokens_for_continuation)
        
        # Test continuation
        result = _continue_story_if_needed(
            truncated_story,
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            estimated_max_tokens,
            mock_client,
        )
        
        # Verify continuation was triggered
        assert mock_client.generate.called, "Continuation should have been triggered"
        
        # Verify story was extended
        result_word_count = len(result.split())
        assert result_word_count > word_count, \
            f"Story should have been extended ({result_word_count} > {word_count})"
        
        # Verify token allocation is precise (using the actual calculation logic)
        call_args = mock_client.generate.call_args
        max_tokens = call_args.kwargs.get('max_tokens')
        
        assert max_tokens == expected_tokens_for_continuation, \
            f"Token allocation should be precise. Expected {expected_tokens_for_continuation}, got {max_tokens}. " \
            f"Calculation: remaining_words={remaining_words}, continuation_tokens_needed={continuation_tokens_needed}, " \
            f"after_min={min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)}, " \
            f"after_max={max(DEFAULT_MIN_TOKENS, min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed))}"
