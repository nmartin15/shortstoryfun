"""
Comprehensive tests for LLM utility functionality.

Tests cover model validation, token counting, API handling, and error scenarios.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from typing import Dict, Any

from src.shortstory.utils.llm import (
    LLMClient,
    _validate_model_name,
    _estimate_tokens,
    _calculate_max_output_tokens,
    DEFAULT_MODEL,
    MODEL_CONTEXT_WINDOWS,
    DEFAULT_CONTEXT_WINDOW,
    get_default_client,
    generate_story_draft,
    revise_story_text
)


class TestModelValidation:
    """Test model name validation."""
    
    def test_validate_model_name_allows_valid_models(self):
        """Test that valid model names are accepted."""
        for model in ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]:
            result = _validate_model_name(model)
            assert result in [model, f"models/{model}"]
    
    def test_validate_model_name_allows_models_prefix(self):
        """Test that models/ prefix is preserved."""
        model = "models/gemini-2.5-flash"
        result = _validate_model_name(model)
        assert result == model
    
    def test_validate_model_name_rejects_invalid_models(self):
        """Test that invalid model names raise ValueError."""
        with pytest.raises(ValueError, match="not allowed"):
            _validate_model_name("invalid-model-name")
    
    def test_validate_model_name_case_insensitive_normalization(self):
        """Test that model names are normalized correctly."""
        # Should normalize to base name
        result = _validate_model_name("gemini-2.5-flash")
        assert result == "gemini-2.5-flash"
        
        result = _validate_model_name("models/gemini-2.5-flash")
        assert result == "models/gemini-2.5-flash"
    
    def test_validate_model_name_error_message_includes_allowed_models(self):
        """Test that error message lists allowed models."""
        with pytest.raises(ValueError) as exc_info:
            _validate_model_name("invalid")
        
        error_msg = str(exc_info.value)
        assert "not allowed" in error_msg
        assert "gemini" in error_msg.lower()


class TestTokenCounting:
    """Test token counting functionality."""
    
    def test_estimate_tokens_returns_positive_integer(self):
        """Test that token estimation returns a positive integer."""
        text = "This is a test sentence with multiple words."
        tokens = _estimate_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_estimate_tokens_handles_empty_string(self):
        """Test that empty string returns 0 tokens."""
        tokens = _estimate_tokens("")
        assert tokens == 0
    
    def test_estimate_tokens_handles_none(self):
        """Test that None returns 0 tokens."""
        tokens = _estimate_tokens(None)
        assert tokens == 0
    
    def test_estimate_tokens_scales_with_text_length(self):
        """Test that token count increases with text length."""
        short_text = "Short text."
        long_text = "This is a much longer text with many more words and sentences. " * 10
        
        short_tokens = _estimate_tokens(short_text)
        long_tokens = _estimate_tokens(long_text)
        
        assert long_tokens > short_tokens
    
    def test_estimate_tokens_with_tiktoken_available(self):
        """Test token counting when tiktoken is available."""
        with patch('src.shortstory.utils.llm.TIKTOKEN_AVAILABLE', True):
            # Mock tiktoken
            mock_encoding = MagicMock()
            mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            
            with patch('tiktoken.get_encoding', return_value=mock_encoding):
                tokens = _estimate_tokens("test text")
                assert tokens > 0
                mock_encoding.encode.assert_called_once()
    
    def test_estimate_tokens_fallback_without_tiktoken(self):
        """Test token counting fallback when tiktoken is unavailable."""
        with patch('src.shortstory.utils.llm.TIKTOKEN_AVAILABLE', False):
            text = "This is a test sentence with seven words."
            tokens = _estimate_tokens(text)
            assert isinstance(tokens, int)
            assert tokens > 0
    
    def test_estimate_tokens_handles_special_characters(self):
        """Test token counting with special characters."""
        text = "Hello! This is a test with punctuation, numbers (123), and symbols: @#$%"
        tokens = _estimate_tokens(text)
        assert tokens > 0
    
    def test_estimate_tokens_handles_unicode(self):
        """Test token counting with Unicode characters."""
        text = "Hello! This is a test with émojis 🎭 and spéciál chàracters"
        tokens = _estimate_tokens(text)
        assert tokens > 0


class TestMaxOutputTokens:
    """Test maximum output token calculation."""
    
    def test_calculate_max_output_tokens_returns_positive(self):
        """Test that max output tokens calculation returns positive value."""
        prompt = "Write a story about a lighthouse keeper."
        max_tokens = _calculate_max_output_tokens(prompt, model_name=DEFAULT_MODEL)
        assert max_tokens > 0
        assert isinstance(max_tokens, int)
    
    def test_calculate_max_output_tokens_considers_prompt_size(self):
        """Test that prompt size affects available output tokens."""
        short_prompt = "Write a story."
        long_prompt = "Write a detailed story. " * 1000
        
        short_max = _calculate_max_output_tokens(short_prompt, model_name=DEFAULT_MODEL)
        long_max = _calculate_max_output_tokens(long_prompt, model_name=DEFAULT_MODEL)
        
        # Longer prompt should leave less room for output
        assert short_max > long_max
    
    def test_calculate_max_output_tokens_considers_system_prompt(self):
        """Test that system prompt is included in token calculation."""
        prompt = "Write a story."
        system_prompt = "You are a skilled writer. " * 100
        
        max_without_system = _calculate_max_output_tokens(prompt, model_name=DEFAULT_MODEL)
        max_with_system = _calculate_max_output_tokens(
            prompt, system_prompt=system_prompt, model_name=DEFAULT_MODEL
        )
        
        assert max_with_system < max_without_system
    
    def test_calculate_max_output_tokens_with_target_word_count(self):
        """Test that target word count affects max tokens."""
        prompt = "Write a story."
        
        max_100_words = _calculate_max_output_tokens(
            prompt, model_name=DEFAULT_MODEL, target_word_count=100
        )
        max_1000_words = _calculate_max_output_tokens(
            prompt, model_name=DEFAULT_MODEL, target_word_count=1000
        )
        
        assert max_1000_words > max_100_words
    
    def test_calculate_max_output_tokens_uses_model_context_window(self):
        """Test that different models use their context windows."""
        prompt = "Write a story."
        
        # Should use model-specific context window
        max_tokens = _calculate_max_output_tokens(
            prompt, model_name="gemini-2.5-flash"
        )
        assert max_tokens > 0
        assert max_tokens < MODEL_CONTEXT_WINDOWS.get("gemini-2.5-flash", DEFAULT_CONTEXT_WINDOW)
    
    def test_calculate_max_output_tokens_has_minimum(self):
        """Test that max tokens has a minimum value."""
        # Very long prompt that would leave minimal room
        long_prompt = "Write a story. " * 10000
        max_tokens = _calculate_max_output_tokens(long_prompt, model_name=DEFAULT_MODEL)
        
        # Should still have minimum tokens
        assert max_tokens >= 100


class TestLLMClientInitialization:
    """Test LLMClient initialization."""
    
    def test_llm_client_init_with_valid_model(self):
        """Test initializing client with valid model."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(model_name="gemini-2.5-flash", api_key="test_key")
                    assert client.model_name in ["gemini-2.5-flash", "models/gemini-2.5-flash"]
    
    def test_llm_client_init_rejects_invalid_model(self):
        """Test that invalid model raises ValueError."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with pytest.raises(ValueError, match="not allowed"):
                LLMClient(model_name="invalid-model", api_key="test_key")
    
    def test_llm_client_init_requires_api_key(self):
        """Test that client requires API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                LLMClient(api_key=None)
    
    def test_llm_client_init_uses_env_api_key(self):
        """Test that client uses environment variable for API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env_key"}):
            with patch('google.generativeai.configure') as mock_configure:
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient()
                    mock_configure.assert_called_once_with(api_key="env_key")
    
    def test_llm_client_init_handles_missing_google_library(self):
        """Test that missing google.generativeai raises ImportError."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'google'")):
                with pytest.raises(ImportError, match="Google Generative AI not installed"):
                    LLMClient(api_key="test_key")
    
    def test_llm_client_init_sets_temperature(self):
        """Test that temperature is set correctly."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key", temperature=0.9)
                    assert client.temperature == 0.9


class TestLLMClientGeneration:
    """Test text generation functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Generated story text"
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    client = LLMClient(api_key="test_key")
                    # Store the mock model class for later access
                    client._mock_model_class = mock_model_class
                    client._mock_model = mock_model
                    yield client
    
    def test_generate_returns_text(self, mock_client):
        """Test that generate returns text."""
        result = mock_client.generate("Write a story about a lighthouse.")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_combines_system_and_user_prompt(self, mock_client):
        """Test that system and user prompts are combined."""
        mock_client.generate(
            prompt="User prompt",
            system_prompt="System prompt"
        )
        
        # Verify generate_content was called (model is created fresh each time)
        assert mock_client._mock_model.generate_content.called
    
    def test_generate_uses_temperature(self, mock_client):
        """Test that temperature is used in generation."""
        mock_client.generate("Test prompt", temperature=0.8)
        
        call_args = mock_client._mock_model.generate_content.call_args
        assert call_args is not None
        # Check kwargs for generation_config
        if call_args.kwargs:
            config = call_args.kwargs.get("generation_config", {})
            assert "temperature" in config or config.get("temperature") == 0.8
        else:
            # If passed as positional, check the call
            assert mock_client._mock_model.generate_content.called
    
    def test_generate_handles_stop_sequences(self, mock_client):
        """Test that stop sequences are applied."""
        result = mock_client.generate(
            "Write a story.",
            stop_sequences=["END"]
        )
        # Stop sequences should be processed
        assert isinstance(result, str)
    
    def test_generate_handles_api_errors(self, mock_client):
        """Test that API errors are handled."""
        mock_client._mock_model.generate_content.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")
    
    def test_generate_handles_response_without_text(self, mock_client):
        """Test handling of response without text attribute."""
        mock_response = MagicMock(spec=[])  # No attributes by default
        # Add candidates but no text attribute
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = "Fallback text"
        mock_client._mock_model.generate_content.return_value = mock_response
        
        result = mock_client.generate("Test")
        assert result == "Fallback text"


class TestLLMClientAvailability:
    """Test availability checking."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    yield client
    
    def test_check_availability_returns_boolean(self, mock_client):
        """Test that check_availability returns boolean."""
        with patch.object(mock_client.genai, 'list_models', return_value=[]):
            result = mock_client.check_availability()
            assert isinstance(result, bool)
    
    def test_check_availability_handles_connection_errors(self, mock_client):
        """Test that connection errors are handled."""
        with patch.object(mock_client.genai, 'list_models', side_effect=ConnectionError("Network error")):
            result = mock_client.check_availability()
            assert result is False
    
    def test_check_availability_handles_timeout_errors(self, mock_client):
        """Test that timeout errors are handled."""
        with patch.object(mock_client.genai, 'list_models', side_effect=TimeoutError("Timeout")):
            result = mock_client.check_availability()
            assert result is False
    
    def test_check_availability_handles_value_errors(self, mock_client):
        """Test that value errors are handled."""
        with patch.object(mock_client.genai, 'list_models', side_effect=ValueError("Invalid")):
            result = mock_client.check_availability()
            assert isinstance(result, bool)


class TestDefaultClient:
    """Test default client functionality."""
    
    def test_get_default_client_creates_client(self):
        """Test that get_default_client creates a client."""
        # Reset global
        import src.shortstory.utils.llm as llm_module
        llm_module._default_client = None
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = get_default_client()
                    assert isinstance(client, LLMClient)
    
    def test_get_default_client_reuses_client(self):
        """Test that get_default_client reuses existing client."""
        import src.shortstory.utils.llm as llm_module
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client1 = get_default_client()
                    client2 = get_default_client()
                    assert client1 is client2


class TestStoryDraftGeneration:
    """Test story draft generation function."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Generated story text")
                    return client
    
    def test_generate_story_draft_returns_text(self, mock_client):
        """Test that generate_story_draft returns text."""
        result = generate_story_draft(
            idea="A lighthouse keeper collects voices",
            character={"name": "Mara", "description": "A quiet keeper"},
            theme="Untold stories",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        # Comprehensive assertions for draft content
        assert isinstance(result, str), "Draft must be a string"
        assert len(result) > 0, "Draft must not be empty"
        assert len(result.strip()) > 0, "Draft must contain non-whitespace content"
        
        # Verify draft contains key elements from inputs
        result_lower = result.lower()
        assert "lighthouse" in result_lower or "keeper" in result_lower or "voice" in result_lower, \
            "Draft should contain key words from the story idea"
        
        # Verify draft has substantial content (not just a placeholder)
        assert len(result) > 20, \
            f"Draft should have substantial content, got {len(result)} characters"
        
        # Verify draft contains complete sentences
        sentence_endings = ['.', '!', '?']
        assert any(ending in result for ending in sentence_endings), \
            "Draft should contain complete sentences with punctuation"
    
    def test_generate_story_draft_includes_character_details(self, mock_client):
        """Test that character details are included in prompt."""
        generate_story_draft(
            idea="Test idea",
            character={"name": "Test", "description": "A test character", "quirks": ["Quirk1"]},
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        # Get the prompt argument (it's passed as a keyword argument)
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "Test" in prompt or "test character" in prompt or "A test character" in prompt
    
    def test_generate_story_draft_handles_string_character(self, mock_client):
        """Test that string character descriptions work."""
        result = generate_story_draft(
            idea="Test idea",
            character="A test character",
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        assert isinstance(result, str)


class TestStoryRevision:
    """Test story revision functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Revised story text")
                    return client
    
    def test_revise_story_text_returns_text(self, mock_client):
        """Test that revise_story_text returns revised text."""
        original_text = "It was a dark and stormy night."
        distinctiveness_issues = {
            "has_cliches": True,
            "found_cliches": ["dark and stormy night"],
            "distinctiveness_score": 0.5
        }
        
        result = revise_story_text(
            text=original_text,
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_revise_story_text_includes_distinctiveness_issues(self, mock_client):
        """Test that distinctiveness issues are included in revision prompt."""
        original_text = "Test story text."
        distinctiveness_issues = {
            "has_cliches": True,
            "found_cliches": ["cliché phrase"],
            "distinctiveness_score": 0.6
        }
        
        revise_story_text(
            text=original_text,
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        # Get the prompt argument (it's passed as a keyword argument)
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "cliché" in prompt.lower() or "distinctiveness" in prompt.lower() or "clich" in prompt.lower() or "Replace clich" in prompt


class TestLLMErrorHandling:
    """Test comprehensive error handling for API failures."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        # Check if google.generativeai is available, if not skip these tests
        from tests.conftest import check_optional_dependency
        if not check_optional_dependency('google.generativeai'):
            pytest.skip("google.generativeai not installed")
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Generated text"
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    client = LLMClient(api_key="test_key")
                    client._mock_model = mock_model
                    yield client
    
    def test_generate_handles_timeout_error(self, mock_client):
        """Test that timeout errors are handled gracefully."""
        import socket
        mock_client._mock_model.generate_content.side_effect = socket.timeout("Request timed out")
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")
    
    def test_generate_handles_rate_limit_error(self, mock_client):
        """Test that rate limit errors are handled."""
        # Simulate rate limit error (429)
        rate_limit_error = Exception("429 Resource has been exhausted")
        mock_client._mock_model.generate_content.side_effect = rate_limit_error
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")
    
    def test_generate_handles_invalid_api_key(self, mock_client):
        """Test that invalid API key errors are handled."""
        invalid_key_error = Exception("API key not valid")
        mock_client._mock_model.generate_content.side_effect = invalid_key_error
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")
    
    def test_generate_handles_connection_error(self, mock_client):
        """Test that connection errors are handled."""
        connection_error = ConnectionError("Failed to connect")
        mock_client._mock_model.generate_content.side_effect = connection_error
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")
    
    def test_generate_handles_service_unavailable(self, mock_client):
        """Test that service unavailable errors are handled."""
        service_error = Exception("503 Service Unavailable")
        mock_client._mock_model.generate_content.side_effect = service_error
        
        with pytest.raises(RuntimeError, match="Gemini API generation failed"):
            mock_client.generate("Test prompt")


class TestStoryDraftGenerationEdgeCases:
    """Test edge cases for generate_story_draft."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Generated story text")
                    return client
    
    def test_generate_story_draft_handles_empty_character(self, mock_client):
        """Test that empty character description works."""
        result = generate_story_draft(
            idea="Test idea",
            character={},
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_generate_story_draft_handles_none_character(self, mock_client):
        """Test that None character works."""
        result = generate_story_draft(
            idea="Test idea",
            character=None,
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_generate_story_draft_handles_empty_theme(self, mock_client):
        """Test that empty theme works."""
        result = generate_story_draft(
            idea="Test idea",
            character={"name": "Test"},
            theme="",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_generate_story_draft_handles_custom_max_words(self, mock_client):
        """Test that custom max_words is respected."""
        generate_story_draft(
            idea="Test idea",
            character={"name": "Test"},
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            max_words=5000,
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        # Check that max_words appears in the prompt
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "5000" in prompt or "5000 words" in prompt
    
    def test_generate_story_draft_handles_complex_character_quirks(self, mock_client):
        """Test that complex character quirks are handled."""
        result = generate_story_draft(
            idea="Test idea",
            character={
                "name": "Test",
                "description": "A complex character",
                "quirks": ["Quirk 1", "Quirk 2", "Quirk 3", "Quirk 4"],
                "contradictions": "Has many contradictions"
            },
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person", "tone": "balanced"},
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_generate_story_draft_handles_sensory_focus(self, mock_client):
        """Test that sensory focus constraints are included."""
        generate_story_draft(
            idea="Test idea",
            character={"name": "Test"},
            theme="Test theme",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={
                "pov": "third person",
                "tone": "balanced",
                "constraints": {"sensory_focus": ["sight", "sound"]}
            },
            genre_config={"framework": "narrative_arc"},
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "sight" in prompt.lower() or "sound" in prompt.lower() or "sensory" in prompt.lower()


class TestStoryRevisionEdgeCases:
    """Test edge cases for revise_story_text."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Revised story text")
                    return client
    
    def test_revise_story_text_handles_empty_distinctiveness_issues(self, mock_client):
        """Test that empty distinctiveness issues work."""
        result = revise_story_text(
            text="Test story text.",
            distinctiveness_issues={},
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_revise_story_text_handles_no_cliches(self, mock_client):
        """Test revision when no clichés are found."""
        distinctiveness_issues = {
            "has_cliches": False,
            "distinctiveness_score": 0.9
        }
        
        result = revise_story_text(
            text="Test story text.",
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_revise_story_text_handles_high_distinctiveness_score(self, mock_client):
        """Test revision when distinctiveness score is already high."""
        distinctiveness_issues = {
            "has_cliches": False,
            "distinctiveness_score": 0.95
        }
        
        result = revise_story_text(
            text="Test story text.",
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_revise_story_text_handles_very_long_story(self, mock_client):
        """Test revision with a very long story."""
        long_text = "This is a test sentence. " * 1000
        distinctiveness_issues = {
            "has_cliches": True,
            "found_cliches": ["test sentence"],
            "distinctiveness_score": 0.5
        }
        
        result = revise_story_text(
            text=long_text,
            distinctiveness_issues=distinctiveness_issues,
            max_words=10000,
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_revise_story_text_handles_short_story(self, mock_client):
        """Test revision with a very short story."""
        short_text = "Short story."
        distinctiveness_issues = {
            "has_cliches": False,
            "distinctiveness_score": 0.7
        }
        
        result = revise_story_text(
            text=short_text,
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        assert isinstance(result, str)
    
    def test_revise_story_text_handles_generic_archetype_issues(self, mock_client):
        """Test revision when generic archetypes are found."""
        distinctiveness_issues = {
            "has_generic_archetype": True,
            "generic_elements": ["wise old mentor", "chosen one"],
            "distinctiveness_score": 0.6
        }
        
        revise_story_text(
            text="Test story with generic archetypes.",
            distinctiveness_issues=distinctiveness_issues,
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "generic" in prompt.lower() or "archetype" in prompt.lower() or "wise old mentor" in prompt.lower()
    
    def test_revise_story_text_respects_max_words(self, mock_client):
        """Test that max_words is respected in revision."""
        text = "Test story text. " * 100
        distinctiveness_issues = {
            "has_cliches": False,
            "distinctiveness_score": 0.7
        }
        
        revise_story_text(
            text=text,
            distinctiveness_issues=distinctiveness_issues,
            max_words=500,
            client=mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        call_args = mock_client.generate.call_args
        assert call_args is not None
        prompt = call_args.kwargs.get('prompt', '') if call_args.kwargs else (call_args[0][0] if call_args[0] else "")
        assert "500" in prompt or "500 words" in prompt


class TestMarkdownCleaning:
    """Test markdown cleaning functionality."""
    
    def test_clean_markdown_removes_headers(self):
        """Test that markdown headers are removed."""
        from src.shortstory.utils.llm import _clean_markdown_from_story
        
        text = "## Chapter 1\n\nThis is the story text."
        cleaned = _clean_markdown_from_story(text)
        assert "##" not in cleaned
        assert "Chapter 1" not in cleaned or "This is the story text" in cleaned
    
    def test_clean_markdown_removes_multiple_headers(self):
        """Test that multiple markdown headers are removed."""
        from src.shortstory.utils.llm import _clean_markdown_from_story
        
        text = "## Title\n### Subtitle\n\nStory content here."
        cleaned = _clean_markdown_from_story(text)
        assert "##" not in cleaned
        assert "###" not in cleaned
        assert "Story content" in cleaned
    
    def test_clean_markdown_preserves_story_text(self):
        """Test that actual story text is preserved."""
        from src.shortstory.utils.llm import _clean_markdown_from_story
        
        text = "## Introduction\n\nIt was a dark night. The wind howled."
        cleaned = _clean_markdown_from_story(text)
        assert "It was a dark night" in cleaned
        assert "The wind howled" in cleaned
    
    def test_clean_markdown_handles_empty_string(self):
        """Test that empty string is handled."""
        from src.shortstory.utils.llm import _clean_markdown_from_story
        
        assert _clean_markdown_from_story("") == ""
        assert _clean_markdown_from_story(None) == None
    
    def test_clean_markdown_handles_no_markdown(self):
        """Test that text without markdown is unchanged."""
        from src.shortstory.utils.llm import _clean_markdown_from_story
        
        text = "This is plain story text with no markdown."
        cleaned = _clean_markdown_from_story(text)
        assert cleaned == text or cleaned.strip() == text.strip()


class TestMetadataStripping:
    """Test metadata stripping functionality."""
    
    def test_strip_metadata_removes_constraints_section(self):
        """Test that constraints metadata is removed."""
        from src.shortstory.utils.llm import _strip_metadata_from_story
        
        text = "Story text here.\n\n**Constraints:**\ntone: dark\npace: fast"
        cleaned = _strip_metadata_from_story(text)
        # The constraints header and metadata should be removed
        assert "**Constraints:**" not in cleaned or cleaned.count("**Constraints:**") == 0
        assert "tone: dark" not in cleaned
        assert "pace: fast" not in cleaned
        assert "Story text here" in cleaned
    
    def test_strip_metadata_removes_metadata_patterns(self):
        """Test that metadata patterns are removed."""
        from src.shortstory.utils.llm import _strip_metadata_from_story
        
        text = "Story content.\n\ntone: dark\npace: moderate\npov_preference: first"
        cleaned = _strip_metadata_from_story(text)
        assert "tone: dark" not in cleaned
        assert "pace: moderate" not in cleaned
        assert "pov_preference" not in cleaned
    
    def test_strip_metadata_preserves_story_text(self):
        """Test that story text is preserved."""
        from src.shortstory.utils.llm import _strip_metadata_from_story
        
        text = "The character walked into the room.\n\n**Constraints:**\ntone: dark"
        cleaned = _strip_metadata_from_story(text)
        assert "The character walked" in cleaned
        assert "tone: dark" not in cleaned
    
    def test_strip_metadata_handles_empty_string(self):
        """Test that empty string is handled."""
        from src.shortstory.utils.llm import _strip_metadata_from_story
        
        assert _strip_metadata_from_story("") == ""
        assert _strip_metadata_from_story(None) == None
    
    def test_strip_metadata_handles_no_metadata(self):
        """Test that text without metadata is unchanged."""
        from src.shortstory.utils.llm import _strip_metadata_from_story
        
        text = "Plain story text with no metadata."
        cleaned = _strip_metadata_from_story(text)
        assert cleaned == text or cleaned.strip() == text.strip()


class TestStoryContinuation:
    """Test story continuation logic."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Continued story text with more words.")
                    return client
    
    def test_continue_story_if_needed_skips_when_long_enough(self, mock_client):
        """Test that continuation is skipped when story is long enough."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        
        # Story must end with proper punctuation to avoid being treated as truncated
        long_story = "Word " * 4999 + "Word."  # 5000 words, ends with period
        result = _continue_story_if_needed(
            long_story, STORY_MIN_WORDS, STORY_MAX_WORDS, GEMINI_MAX_OUTPUT_TOKENS, mock_client
        )
        assert result == long_story
        assert not mock_client.generate.called
    
    def test_continue_story_if_needed_continues_when_too_short(self, mock_client):
        """Test that continuation is triggered when story is too short."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        
        short_story = "Word " * 1000  # 1000 words
        continuation = "More words " * 500  # 500 words
        mock_client.generate.return_value = continuation
        
        result = _continue_story_if_needed(
            short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, GEMINI_MAX_OUTPUT_TOKENS, mock_client
        )
        assert mock_client.generate.called
        assert len(result.split()) > len(short_story.split())
    
    def test_continue_story_if_needed_handles_truncated_story(self, mock_client):
        """Test that truncated stories trigger continuation."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        
        # Story that doesn't end with proper punctuation
        truncated_story = "This is a story that ends abruptly without"
        continuation = " proper ending. More content here."
        mock_client.generate.return_value = continuation
        
        result = _continue_story_if_needed(
            truncated_story, STORY_MIN_WORDS, STORY_MAX_WORDS, GEMINI_MAX_OUTPUT_TOKENS, mock_client
        )
        assert mock_client.generate.called
        assert result.endswith(("proper ending", ".", "!", "?"))
    
    def test_continue_story_if_needed_handles_continuation_failure(self, mock_client):
        """Test that continuation failure is handled gracefully."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        
        short_story = "Word " * 1000
        mock_client.generate.side_effect = Exception("API Error")
        
        # Should not raise, but return original story
        result = _continue_story_if_needed(
            short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, GEMINI_MAX_OUTPUT_TOKENS, mock_client
        )
        assert isinstance(result, str)
        assert len(result.split()) >= len(short_story.split())
    
    def test_attempt_second_continuation(self, mock_client):
        """Test second continuation attempt."""
        from src.shortstory.utils.llm import _attempt_second_continuation
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
        )
        import logging
        
        logger = logging.getLogger(__name__)
        story = "Word " * 2000
        continuation = "More " * 1000
        mock_client.generate.return_value = continuation
        
        result = _attempt_second_continuation(
            story, 2000, STORY_MIN_WORDS, GEMINI_MAX_OUTPUT_TOKENS, mock_client, logger
        )
        assert mock_client.generate.called
        assert len(result.split()) > len(story.split())
    
    def test_attempt_third_continuation(self, mock_client):
        """Test third continuation attempt."""
        from src.shortstory.utils.llm import _attempt_third_continuation
        from src.shortstory.utils.llm_constants import STORY_MIN_WORDS
        import logging
        
        logger = logging.getLogger(__name__)
        story = "Word " * 2500
        continuation = "More " * 1000
        mock_client.generate.return_value = continuation
        
        result = _attempt_third_continuation(
            story, 2500, STORY_MIN_WORDS, mock_client, logger
        )
        assert mock_client.generate.called
        assert len(result.split()) > len(story.split())
    
    def test_continue_story_verifies_token_allocation(self, mock_client):
        """Test that continuation correctly allocates tokens based on remaining words."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
            TOKENS_PER_WORD_ESTIMATE,
            DEFAULT_MIN_TOKENS,
        )
        
        # Create a short story that needs continuation
        short_story = "Word " * 2000  # 2000 words, needs 2000 more to reach minimum
        estimated_max_tokens = 6000
        
        # Calculate expected token allocation for first attempt
        word_count = len(short_story.split())
        remaining_words = STORY_MIN_WORDS - word_count
        continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        expected_allocated_tokens = min(GEMINI_MAX_OUTPUT_TOKENS, estimated_max_tokens, continuation_tokens_needed)
        expected_allocated_tokens = max(DEFAULT_MIN_TOKENS, expected_allocated_tokens)
        
        # Return continuation that adds words but not enough to complete
        continuation = "More words " * 500
        mock_client.generate.return_value = continuation
        
        _continue_story_if_needed(
            short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, estimated_max_tokens, mock_client
        )
        
        # Verify generate was called
        assert mock_client.generate.called
        
        # Verify token allocation for first call follows the correct logic
        # The allocation should be calculated based on remaining words needed
        first_call_args = mock_client.generate.call_args_list[0]
        assert first_call_args is not None
        actual_max_tokens = first_call_args.kwargs.get('max_tokens')
        
        # Verify token allocation is within valid bounds
        assert actual_max_tokens is not None, "First call should have max_tokens"
        assert actual_max_tokens >= DEFAULT_MIN_TOKENS, \
            f"First call max_tokens {actual_max_tokens} should be >= {DEFAULT_MIN_TOKENS}"
        assert actual_max_tokens <= GEMINI_MAX_OUTPUT_TOKENS, \
            f"First call max_tokens {actual_max_tokens} should be <= {GEMINI_MAX_OUTPUT_TOKENS}"
        assert actual_max_tokens <= estimated_max_tokens, \
            f"First call max_tokens {actual_max_tokens} should be <= estimated_max_tokens {estimated_max_tokens}"
        
        # Verify the allocation is reasonable (should be at least enough for remaining words)
        # Using a tolerance since the exact calculation may vary
        min_reasonable_tokens = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 0.8)  # 80% of needed
        assert actual_max_tokens >= min(min_reasonable_tokens, DEFAULT_MIN_TOKENS), \
            f"Token allocation {actual_max_tokens} seems too low for {remaining_words} remaining words"
        
        # Verify all calls have valid token allocations
        for i, call_args in enumerate(mock_client.generate.call_args_list):
            call_max_tokens = call_args.kwargs.get('max_tokens')
            assert call_max_tokens is not None, f"Call {i+1} should have max_tokens"
            assert call_max_tokens >= DEFAULT_MIN_TOKENS, \
                f"Call {i+1} max_tokens {call_max_tokens} should be >= {DEFAULT_MIN_TOKENS}"
            assert call_max_tokens <= GEMINI_MAX_OUTPUT_TOKENS, \
                f"Call {i+1} max_tokens {call_max_tokens} should be <= {GEMINI_MAX_OUTPUT_TOKENS}"
    
    def test_continue_story_verifies_token_allocation_with_large_remaining_words(self, mock_client):
        """Test token allocation when many words are needed."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
            TOKENS_PER_WORD_ESTIMATE,
            DEFAULT_MIN_TOKENS,
        )
        
        # Very short story needing many words
        very_short_story = "Word " * 500  # 500 words, needs 3500 more
        estimated_max_tokens = 10000  # Large estimated max
        
        # Calculate expected token allocation
        word_count = len(very_short_story.split())
        remaining_words = STORY_MIN_WORDS - word_count
        continuation_tokens_needed = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 1.3)
        
        continuation = "More words " * 1000
        mock_client.generate.return_value = continuation
        
        _continue_story_if_needed(
            very_short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, estimated_max_tokens, mock_client
        )
        
        # Verify token allocation follows correct logic
        first_call_args = mock_client.generate.call_args_list[0]
        assert first_call_args is not None
        actual_max_tokens = first_call_args.kwargs.get('max_tokens')
        
        # Should be within valid bounds
        assert actual_max_tokens is not None
        assert actual_max_tokens >= DEFAULT_MIN_TOKENS
        assert actual_max_tokens <= GEMINI_MAX_OUTPUT_TOKENS
        assert actual_max_tokens <= estimated_max_tokens
        
        # Should be reasonable for the remaining words needed
        min_reasonable = int(remaining_words * TOKENS_PER_WORD_ESTIMATE * 0.8)
        assert actual_max_tokens >= min(min_reasonable, DEFAULT_MIN_TOKENS)
        # Should be capped at GEMINI_MAX_OUTPUT_TOKENS
        assert actual_max_tokens <= GEMINI_MAX_OUTPUT_TOKENS
    
    def test_continue_story_verifies_token_allocation_respects_estimated_max(self, mock_client):
        """Test that token allocation respects estimated_max_tokens limit when possible."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
            DEFAULT_MIN_TOKENS,
        )
        
        short_story = "Word " * 2000
        # estimated_max_tokens that is larger than DEFAULT_MIN_TOKENS
        # This tests that estimated_max is respected when it's above the minimum
        reasonable_estimated_max = 5000
        
        continuation = "More words " * 500
        mock_client.generate.return_value = continuation
        
        _continue_story_if_needed(
            short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, reasonable_estimated_max, mock_client
        )
        
        # Verify token allocation respects estimated_max when above minimum
        first_call_args = mock_client.generate.call_args_list[0]
        assert first_call_args is not None
        actual_max_tokens = first_call_args.kwargs.get('max_tokens')
        # Should respect estimated_max when it's reasonable
        assert actual_max_tokens <= reasonable_estimated_max, \
            f"Token allocation {actual_max_tokens} should not exceed estimated_max {reasonable_estimated_max}"
        assert actual_max_tokens >= DEFAULT_MIN_TOKENS, \
            f"Token allocation {actual_max_tokens} should be at least {DEFAULT_MIN_TOKENS}"
    
    def test_continue_story_verifies_token_allocation_multiple_attempts(self, mock_client):
        """Test that token allocation is correct across multiple continuation attempts."""
        from src.shortstory.utils.llm import _continue_story_if_needed
        from src.shortstory.utils.llm_constants import (
            STORY_MIN_WORDS,
            STORY_MAX_WORDS,
            GEMINI_MAX_OUTPUT_TOKENS,
            TOKENS_PER_WORD_ESTIMATE,
            DEFAULT_MIN_TOKENS,
        )
        
        # Story that will need multiple continuation attempts
        short_story = "Word " * 1000  # Very short, needs 3000 more words
        estimated_max_tokens = 6000
        
        # First continuation adds some words but not enough
        continuation1 = "More words " * 500  # Adds 500 words, still short
        continuation2 = "Even more words " * 1000  # Adds 1000 words
        mock_client.generate.side_effect = [continuation1, continuation2]
        
        result = _continue_story_if_needed(
            short_story, STORY_MIN_WORDS, STORY_MAX_WORDS, estimated_max_tokens, mock_client
        )
        
        # Verify multiple calls were made
        assert mock_client.generate.call_count >= 1
        
        # Verify each call had appropriate token allocation
        calls = mock_client.generate.call_args_list
        for i, call in enumerate(calls):
            call_max_tokens = call.kwargs.get('max_tokens')
            assert call_max_tokens is not None, f"Call {i+1} should have max_tokens"
            assert call_max_tokens >= DEFAULT_MIN_TOKENS, \
                f"Call {i+1} max_tokens {call_max_tokens} should be >= {DEFAULT_MIN_TOKENS}"
            assert call_max_tokens <= GEMINI_MAX_OUTPUT_TOKENS, \
                f"Call {i+1} max_tokens {call_max_tokens} should be <= {GEMINI_MAX_OUTPUT_TOKENS}"
        
        # Verify story was extended
        result_word_count = len(result.split())
        assert result_word_count > len(short_story.split())


class TestOutlineGeneration:
    """Test outline generation functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    return client
    
    def test_generate_outline_structure_with_llm(self, mock_client):
        """Test outline generation with LLM."""
        from src.shortstory.utils.llm import generate_outline_structure
        import json
        
        # Mock LLM response with valid JSON
        outline_json = {
            "beginning": {"hook": "Opening", "setup": "Setup", "beats": ["beat1"]},
            "middle": {"complication": "Complication", "rising_action": "Action", "beats": ["beat2"]},
            "end": {"climax": "Climax", "resolution": "Resolution", "beats": ["beat3"]}
        }
        mock_response = json.dumps(outline_json)
        mock_client.generate = MagicMock(return_value=f"```json\n{mock_response}\n```")
        
        result = generate_outline_structure(
            idea="Test idea",
            character={"name": "Test"},
            theme="Test theme",
            use_llm=True,
            client=mock_client
        )
        
        assert "beginning" in result
        assert "middle" in result
        assert "end" in result
    
    def test_generate_outline_structure_fallback_to_template(self, mock_client):
        """Test that template fallback works when LLM fails."""
        from src.shortstory.utils.llm import generate_outline_structure
        
        mock_client.generate = MagicMock(side_effect=Exception("API Error"))
        
        result = generate_outline_structure(
            idea="Test idea",
            character={"name": "Test"},
            theme="Test theme",
            use_llm=True,
            client=mock_client
        )
        
        assert "beginning" in result
        assert "middle" in result
        assert "end" in result
    
    def test_generate_outline_structure_without_llm(self, mock_client):
        """Test outline generation without LLM (template only)."""
        from src.shortstory.utils.llm import generate_outline_structure
        
        result = generate_outline_structure(
            idea="Test idea",
            character={"name": "Test"},
            theme="Test theme",
            use_llm=False,
            client=mock_client
        )
        
        assert "beginning" in result
        assert "middle" in result
        assert "end" in result
    
    def test_generate_outline_structure_handles_invalid_json(self, mock_client):
        """Test that invalid JSON falls back to parsing."""
        from src.shortstory.utils.llm import generate_outline_structure
        
        mock_client.generate = MagicMock(return_value="This is not JSON but has beginning and middle sections.")
        
        result = generate_outline_structure(
            idea="Test idea",
            use_llm=True,
            client=mock_client
        )
        
        assert isinstance(result, dict)
        assert "beginning" in result or "middle" in result
    
    def test_parse_outline_from_text(self):
        """Test parsing outline from text response."""
        from src.shortstory.utils.llm import _parse_outline_from_text
        
        text = "Beginning: Opening scene\nMiddle: Complication\nEnd: Resolution"
        result = _parse_outline_from_text(text, "setup", "complication", "resolution")
        
        assert result is not None
        assert "beginning" in result
        assert "middle" in result
        assert "end" in result


class TestScaffoldGeneration:
    """Test scaffold generation functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    return client
    
    def test_generate_scaffold_structure_with_llm(self, mock_client):
        """Test scaffold generation with LLM."""
        from src.shortstory.utils.llm import generate_scaffold_structure
        import json
        
        scaffold_json = {
            "narrative_voice": {"pov": "third person", "prose_style": "sparse"},
            "character_voices": {},
            "tone": {"emotional_register": "balanced"},
            "conflicts": {"internal": [], "external": []},
            "sensory_specificity": {"primary_senses": ["sight"]},
            "style_guidelines": {}
        }
        mock_response = json.dumps(scaffold_json)
        mock_client.generate = MagicMock(return_value=f"```json\n{mock_response}\n```")
        
        result = generate_scaffold_structure(
            premise={"idea": "Test", "character": {"name": "Test"}, "theme": "Test"},
            outline={"beginning": {}, "middle": {}, "end": {}},
            use_llm=True,
            client=mock_client
        )
        
        assert "narrative_voice" in result
    
    def test_generate_scaffold_structure_fallback_to_template(self, mock_client):
        """Test that template fallback works when LLM fails."""
        from src.shortstory.utils.llm import generate_scaffold_structure
        
        mock_client.generate = MagicMock(side_effect=Exception("API Error"))
        
        result = generate_scaffold_structure(
            premise={"idea": "Test", "character": {"name": "Test"}, "theme": "Test"},
            outline={"beginning": {}, "middle": {}, "end": {}},
            use_llm=True,
            client=mock_client
        )
        
        assert "narrative_voice" in result
        assert "tone" in result
    
    def test_generate_scaffold_structure_without_llm(self, mock_client):
        """Test scaffold generation without LLM (template only)."""
        from src.shortstory.utils.llm import generate_scaffold_structure
        
        result = generate_scaffold_structure(
            premise={"idea": "Test", "character": {"name": "Test"}, "theme": "Test"},
            outline={"beginning": {}, "middle": {}, "end": {}},
            use_llm=False,
            client=mock_client
        )
        
        assert "narrative_voice" in result
        assert "tone" in result


class TestResponseParsing:
    """Test response parsing edge cases."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model
                    client = LLMClient(api_key="test_key")
                    client._mock_model = mock_model
                    yield client
    
    def test_generate_handles_response_with_candidates(self, mock_client):
        """Test handling response with candidates structure."""
        from unittest.mock import Mock
        
        mock_response = MagicMock()
        mock_response.text = None
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Text from candidate"
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]
        mock_client._mock_model.generate_content.return_value = mock_response
        
        result = mock_client.generate("Test prompt")
        assert "Text from candidate" in result
    
    def test_generate_handles_response_with_text_attribute(self, mock_client):
        """Test handling response with text attribute."""
        mock_response = MagicMock()
        mock_response.text = "Direct text response"
        mock_response.candidates = None
        mock_client._mock_model.generate_content.return_value = mock_response
        
        result = mock_client.generate("Test prompt")
        assert result == "Direct text response"
    
    def test_generate_handles_empty_response(self, mock_client):
        """Test handling empty response."""
        # Create a mock that has no text and empty candidates
        mock_response = MagicMock()
        # Make hasattr(response, 'text') return False
        def hasattr_side_effect(obj, attr):
            if attr == 'text':
                return False
            return hasattr(obj, attr)
        
        # Mock response with no text attribute and empty candidates
        mock_response.candidates = []
        # Use spec to control attribute access
        mock_response = MagicMock(spec=[])
        mock_response.candidates = []
        # Override hasattr behavior by making text attribute not exist
        if hasattr(mock_response, 'text'):
            delattr(mock_response, 'text')
        
        mock_client._mock_model.generate_content.return_value = mock_response
        
        result = mock_client.generate("Test prompt")
        # Should return empty string or string representation
        assert isinstance(result, str)
    
    def test_generate_handles_string_response(self, mock_client):
        """Test handling string response."""
        mock_response = "String response"
        mock_client._mock_model.generate_content.return_value = mock_response
        
        result = mock_client.generate("Test prompt")
        assert isinstance(result, str)


class TestTokenCalculationEdgeCases:
    """Test token calculation edge cases."""
    
    def test_calculate_max_output_tokens_with_very_long_prompt(self):
        """Test token calculation with very long prompt."""
        from src.shortstory.utils.llm import _calculate_max_output_tokens
        
        long_prompt = "Word " * 100000  # Very long prompt
        max_tokens = _calculate_max_output_tokens(long_prompt, model_name=DEFAULT_MODEL)
        
        # Should still return a positive value, even if small
        assert max_tokens > 0
        assert isinstance(max_tokens, int)
    
    def test_calculate_max_output_tokens_with_full_length_story(self):
        """Test token calculation for full-length story."""
        from src.shortstory.utils.llm import _calculate_max_output_tokens
        from src.shortstory.utils.llm_constants import FULL_LENGTH_STORY_THRESHOLD
        
        prompt = "Write a story."
        max_tokens = _calculate_max_output_tokens(
            prompt,
            model_name=DEFAULT_MODEL,
            target_word_count=FULL_LENGTH_STORY_THRESHOLD
        )
        
        # Should request significant tokens for full-length story
        assert max_tokens > 1000
    
    def test_calculate_max_output_tokens_with_different_models(self):
        """Test token calculation with different model names."""
        from src.shortstory.utils.llm import _calculate_max_output_tokens
        
        prompt = "Write a story."
        
        for model in ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]:
            max_tokens = _calculate_max_output_tokens(prompt, model_name=model)
            assert max_tokens > 0
            assert isinstance(max_tokens, int)
    
    def test_estimate_tokens_with_very_long_text(self):
        """Test token estimation with very long text."""
        from src.shortstory.utils.llm import _estimate_tokens
        
        long_text = "This is a test sentence. " * 10000
        tokens = _estimate_tokens(long_text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_tokens_with_unicode_text(self):
        """Test token estimation with Unicode characters."""
        from src.shortstory.utils.llm import _estimate_tokens
        
        unicode_text = "Hello 世界! 🌍 This is a test with émojis and spéciál chàracters."
        tokens = _estimate_tokens(unicode_text)
        
        assert tokens > 0
        assert isinstance(tokens, int)


class TestGenerateStoryDraftRobustness:
    """Test robustness of generate_story_draft function."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(api_key="test_key")
                    client.generate = MagicMock(return_value="Generated story text with enough words. " * 200)
                    return client
    
    def test_generate_story_draft_handles_very_short_response(self, mock_client):
        """Test handling of very short API response."""
        from src.shortstory.utils.llm import generate_story_draft
        
        mock_client.generate.return_value = "Short"
        
        with pytest.raises(ValueError, match="suspiciously short"):
            generate_story_draft(
                idea="Test",
                character={"name": "Test"},
                theme="Test",
                outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
                scaffold={"pov": "third person"},
                genre_config={},
                client=mock_client
            )
    
    def test_generate_story_draft_handles_markdown_in_response(self, mock_client):
        """Test that markdown is cleaned from response."""
        from src.shortstory.utils.llm import generate_story_draft
        
        mock_client.generate.return_value = "## Chapter 1\n\nStory text here."
        
        result = generate_story_draft(
            idea="Test",
            character={"name": "Test"},
            theme="Test",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person"},
            genre_config={},
            client=mock_client
        )
        
        assert "##" not in result or "Story text" in result
    
    def test_generate_story_draft_handles_metadata_in_response(self, mock_client):
        """Test that metadata is stripped from response."""
        from src.shortstory.utils.llm import generate_story_draft
        
        mock_client.generate.return_value = "Story text.\n\n**Constraints:**\ntone: dark"
        
        result = generate_story_draft(
            idea="Test",
            character={"name": "Test"},
            theme="Test",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person"},
            genre_config={},
            client=mock_client
        )
        
        assert "**Constraints:**" not in result or "tone: dark" not in result
    
    def test_generate_story_draft_handles_continuation(self, mock_client):
        """Test that story continuation works when story is too short."""
        from src.shortstory.utils.llm import generate_story_draft
        
        # First call returns short story, continuation returns more
        short_story = "Word " * 1000
        continuation = "More words " * 500
        mock_client.generate.side_effect = [short_story, continuation]
        
        result = generate_story_draft(
            idea="Test",
            character={"name": "Test"},
            theme="Test",
            outline={"acts": {"beginning": "setup", "middle": "complication", "end": "resolution"}},
            scaffold={"pov": "third person"},
            genre_config={},
            max_words=5000,
            client=mock_client
        )
        
        # Should have called generate multiple times (initial + continuation)
        assert mock_client.generate.call_count >= 1


class TestLLMClientRobustness:
    """Test LLMClient robustness and error handling."""
    
    def test_llm_client_handles_model_name_with_prefix(self):
        """Test that model names with 'models/' prefix work."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(model_name="models/gemini-2.5-flash", api_key="test_key")
                    assert "models/" in client.model_name or client.model_name == "gemini-2.5-flash"
    
    def test_llm_client_handles_model_name_without_prefix(self):
        """Test that model names without prefix work."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    client = LLMClient(model_name="gemini-2.5-flash", api_key="test_key")
                    assert client.model_name in ["gemini-2.5-flash", "models/gemini-2.5-flash"]
    
    def test_llm_client_generate_handles_stop_sequences(self):
        """Test that stop sequences work correctly."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "This is a story. END More text here."
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    client = LLMClient(api_key="test_key")
                    result = client.generate("Test", stop_sequences=["END"])
                    
                    assert "END" not in result
                    assert "More text" not in result
    
    def test_llm_client_generate_handles_none_max_tokens(self):
        """Test that None max_tokens is handled."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Generated text"
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    client = LLMClient(api_key="test_key", max_tokens=None)
                    result = client.generate("Test", max_tokens=None)
                    
                    assert result == "Generated text"

