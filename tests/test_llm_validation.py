"""
Tests for LLM validation and security.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from src.shortstory.utils.llm import LLMClient, _validate_model_name, get_default_client, FALLBACK_ALLOWED_MODELS, DEFAULT_MODEL


class TestModelNameValidation:
    """Test model name validation functionality."""
    
    def test_validate_model_name_valid(self):
        """Test that valid model names pass validation."""
        valid_models = ["gemini-2.5-flash", "gemini-1.5-pro", "models/gemini-2.5-flash"]
        
        for model in valid_models:
            result = _validate_model_name(model, FALLBACK_ALLOWED_MODELS)
            assert result.startswith("models/")
            assert result.replace("models/", "") in FALLBACK_ALLOWED_MODELS
    
    def test_validate_model_name_invalid(self):
        """Test that invalid model names raise ValueError."""
        invalid_models = ["malicious-model", "invalid-model", "models/invalid-model"]
        
        for model in invalid_models:
            with pytest.raises(ValueError, match="not allowed|Invalid model"):
                _validate_model_name(model, FALLBACK_ALLOWED_MODELS)
    
    def test_validate_model_name_normalizes_prefix(self):
        """Test that model names are normalized with 'models/' prefix."""
        model_without_prefix = "gemini-2.5-flash"
        model_with_prefix = "models/gemini-2.5-flash"
        
        result1 = _validate_model_name(model_without_prefix, FALLBACK_ALLOWED_MODELS)
        result2 = _validate_model_name(model_with_prefix, FALLBACK_ALLOWED_MODELS)
        
        assert result1 == result2
        assert result1.startswith("models/")


class TestLLMClientInitialization:
    """Test LLMClient initialization and validation integration."""
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_model_name_on_init(self, mock_genai):
        """Test that LLMClient validates model name during initialization."""
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
            Mock(name="models/gemini-1.5-pro"),
        ]
        
        # Test with valid model name - should succeed
        client = LLMClient(model_name="gemini-2.5-flash")
        assert client.model_name == "models/gemini-2.5-flash"
        mock_genai.configure.assert_called_once_with(api_key="test-key")
        mock_genai.GenerativeModel.assert_called_once_with("models/gemini-2.5-flash")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    @patch('src.shortstory.utils.llm._validate_model_name')
    def test_llm_client_calls_validate_model_name_during_init(self, mock_validate, mock_genai):
        """Test that LLMClient actually calls _validate_model_name during initialization.
        
        This integration test verifies that the validation function is called
        as part of the LLMClient initialization path, not just tested in isolation.
        """
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
            Mock(name="models/gemini-1.5-pro"),
        ]
        
        # Configure mock_validate to return normalized model name
        mock_validate.return_value = "models/gemini-2.5-flash"
        
        # Initialize client - this should call _validate_model_name
        client = LLMClient(model_name="gemini-2.5-flash")
        
        # Verify _validate_model_name was called with correct arguments
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args
        assert call_args[0][0] == "gemini-2.5-flash", "Should validate the provided model name"
        assert isinstance(call_args[0][1], list), "Should pass available_models list"
        
        # Verify client was initialized with validated model name
        assert client.model_name == "models/gemini-2.5-flash"
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    @patch('src.shortstory.utils.llm._validate_model_name')
    def test_llm_client_validation_error_propagates_from_init(self, mock_validate, mock_genai):
        """Test that validation errors during LLMClient init are properly raised.
        
        This verifies that if _validate_model_name raises ValueError,
        the LLMClient constructor also raises ValueError, ensuring validation
        is not bypassed.
        """
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        
        # Configure mock_validate to raise ValueError for invalid model
        mock_validate.side_effect = ValueError("Model 'malicious-model' is not allowed")
        
        # Initialize client with invalid model - should raise ValueError
        with pytest.raises(ValueError, match="not allowed|malicious-model"):
            LLMClient(model_name="malicious-model")
        
        # Verify _validate_model_name was called
        mock_validate.assert_called_once()
        assert "malicious-model" in str(mock_validate.call_args[0][0])
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_raises_error_for_invalid_model(self, mock_genai):
        """Test that LLMClient raises ValueError for invalid model names."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
            Mock(name="models/gemini-1.5-pro"),
        ]
        
        # Test with invalid model name - should raise ValueError
        with pytest.raises(ValueError, match="not allowed|Invalid model") as excinfo:
            LLMClient(model_name="malicious-model")
        
        assert "malicious-model" in str(excinfo.value).lower() or "not allowed" in str(excinfo.value).lower()
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_uses_fallback_on_api_failure(self, mock_genai):
        """Test that LLMClient uses fallback models when API call fails."""
        # Setup mock genai to raise exception on list_models
        mock_genai.list_models.side_effect = Exception("API error")
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Should use fallback list and still validate
        client = LLMClient(model_name="gemini-2.5-flash")
        assert client.model_name == "models/gemini-2.5-flash"
        
        # Invalid model should still fail even with fallback
        with pytest.raises(ValueError, match="not allowed|Invalid model"):
            LLMClient(model_name="malicious-model")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_requires_api_key(self, mock_genai):
        """Test that LLMClient requires GOOGLE_API_KEY."""
        # Remove API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                LLMClient()


class TestGetDefaultClient:
    """Test get_default_client function."""
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key", "LLM_MODEL": "gemini-1.5-pro"})
    @patch('src.shortstory.utils.llm.genai')
    def test_get_default_client_uses_env_var(self, mock_genai):
        """Test that get_default_client uses LLM_MODEL environment variable."""
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-1.5-pro"),
        ]
        
        # Clear the global default client
        import src.shortstory.utils.llm as llm_module
        llm_module._default_client = None
        
        client = get_default_client()
        assert client.model_name == "models/gemini-1.5-pro"
        mock_genai.GenerativeModel.assert_called_with("models/gemini-1.5-pro")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True)
    @patch('src.shortstory.utils.llm.genai')
    def test_get_default_client_uses_default_model(self, mock_genai):
        """Test that get_default_client uses DEFAULT_MODEL when LLM_MODEL not set."""
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name=f"models/{DEFAULT_MODEL}"),
        ]
        
        # Clear the global default client
        import src.shortstory.utils.llm as llm_module
        llm_module._default_client = None
        
        # Remove LLM_MODEL if it exists
        if "LLM_MODEL" in os.environ:
            del os.environ["LLM_MODEL"]
        
        client = get_default_client()
        assert client.model_name == f"models/{DEFAULT_MODEL}"
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_get_default_client_validates_model_from_env(self, mock_genai):
        """Test that get_default_client validates model name from environment."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        
        # Clear the global default client
        import src.shortstory.utils.llm as llm_module
        llm_module._default_client = None
        
        # Set invalid model in environment
        with patch.dict(os.environ, {"LLM_MODEL": "malicious-model"}):
            # Should raise ValueError during initialization
            with pytest.raises(ValueError, match="not allowed|Invalid model"):
                get_default_client()
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_handles_genai_configure_error(self, mock_genai):
        """Test that LLMClient handles errors during genai.configure."""
        # Setup mock genai to raise error on configure
        mock_genai.configure.side_effect = Exception("Configuration error")
        
        # Should raise an error or handle gracefully
        with pytest.raises(Exception):
            LLMClient(model_name="gemini-2.5-flash")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_handles_generative_model_error(self, mock_genai):
        """Test that LLMClient handles errors during GenerativeModel creation."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        mock_genai.GenerativeModel.side_effect = Exception("Model creation error")
        
        # Should raise an error
        with pytest.raises(Exception):
            LLMClient(model_name="gemini-2.5-flash")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_all_fallback_models(self, mock_genai):
        """Test that LLMClient validates against all fallback models when API fails."""
        # Setup mock genai to fail on list_models
        mock_genai.list_models.side_effect = Exception("API error")
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test that all fallback models are valid
        for model in FALLBACK_ALLOWED_MODELS:
            # Clear the global default client
            import src.shortstory.utils.llm as llm_module
            llm_module._default_client = None
            
            client = LLMClient(model_name=model)
            assert client.model_name == f"models/{model}"
        
        # Test that non-fallback models are rejected even when API fails
        with pytest.raises(ValueError, match="not allowed|Invalid model"):
            LLMClient(model_name="malicious-model")


class TestLLMClientComprehensiveValidation:
    """Comprehensive validation tests for LLMClient."""
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_model_with_special_characters(self, mock_genai):
        """Test that LLMClient rejects model names with special characters."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        
        # Test various injection attempts
        malicious_models = [
            "gemini-2.5-flash; rm -rf /",
            "gemini-2.5-flash' OR '1'='1",
            "gemini-2.5-flash<script>alert('xss')</script>",
            "../../etc/passwd",
            "gemini-2.5-flash\nDROP TABLE models;",
        ]
        
        for malicious_model in malicious_models:
            with pytest.raises(ValueError, match="not allowed|Invalid model"):
                LLMClient(model_name=malicious_model)
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_model_case_sensitivity(self, mock_genai):
        """Test that LLMClient handles case sensitivity correctly."""
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
            Mock(name="models/GEMINI-2.5-FLASH"),  # Different case
        ]
        
        # Valid model should work (case-insensitive matching)
        client = LLMClient(model_name="GEMINI-2.5-FLASH")
        assert client.model_name == "models/gemini-2.5-flash" or client.model_name == "models/GEMINI-2.5-FLASH"
        
        # Invalid model with similar name should fail
        with pytest.raises(ValueError, match="not allowed|Invalid model"):
            LLMClient(model_name="gemini-2.5-flash-image")  # Image model doesn't exist
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_model_with_empty_string(self, mock_genai):
        """Test that LLMClient rejects empty model names."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        
        # Empty string should fail validation
        with pytest.raises(ValueError, match="not allowed|Invalid model|empty"):
            LLMClient(model_name="")
        
        # Whitespace-only should also fail
        with pytest.raises(ValueError, match="not allowed|Invalid model"):
            LLMClient(model_name="   ")
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_model_with_very_long_name(self, mock_genai):
        """Test that LLMClient handles very long model names correctly."""
        # Setup mock genai
        mock_genai.list_models.return_value = [
            Mock(name="models/gemini-2.5-flash"),
        ]
        
        # Very long model name should fail validation
        long_model_name = "a" * 1000
        with pytest.raises(ValueError, match="not allowed|Invalid model"):
            LLMClient(model_name=long_model_name)
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('src.shortstory.utils.llm.genai')
    def test_llm_client_validates_all_environment_models(self, mock_genai):
        """Test that get_default_client validates all possible environment model values."""
        # Setup mock genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            Mock(name=f"models/{model}") for model in FALLBACK_ALLOWED_MODELS
        ]
        
        # Clear the global default client
        import src.shortstory.utils.llm as llm_module
        
        # Test each allowed model from environment
        for model in FALLBACK_ALLOWED_MODELS:
            llm_module._default_client = None
            with patch.dict(os.environ, {"LLM_MODEL": model}):
                client = get_default_client()
                assert client.model_name == f"models/{model}"
        
        # Test invalid model from environment
        llm_module._default_client = None
        with patch.dict(os.environ, {"LLM_MODEL": "invalid-model"}):
            with pytest.raises(ValueError, match="not allowed|Invalid model"):
                get_default_client()