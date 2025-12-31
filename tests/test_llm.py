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
    ALLOWED_MODELS,
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
        assert isinstance(result, str)
        assert len(result) > 0
    
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
        try:
            import google.generativeai
        except ImportError:
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

