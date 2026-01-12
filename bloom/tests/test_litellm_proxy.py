#!/usr/bin/env python3
"""
Tests for LiteLLM proxy integration.

These tests verify that Bloom can correctly use a custom LiteLLM proxy endpoint
instead of direct provider API calls.

To run these tests with your LiteLLM proxy:

    # Set environment variables
    export LITELLM_API_KEY=your_api_key
    export LITELLM_BASE_URL=https://your-litellm-proxy.com
    
    # Run tests
    pytest tests/test_litellm_proxy.py -v

To run without a proxy (uses mocked responses):
    pytest tests/test_litellm_proxy.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any


class TestLiteLLMProxyConfig:
    """Tests for LiteLLM proxy configuration functions."""
    
    def test_get_litellm_proxy_config_not_set(self):
        """Test that proxy config returns None when env vars are not set."""
        from bloom.utils import get_litellm_proxy_config
        
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing env vars
            os.environ.pop("LITELLM_API_KEY", None)
            os.environ.pop("LITELLM_BASE_URL", None)
            os.environ.pop("LLM_URL", None)
            
            api_base, api_key = get_litellm_proxy_config()
            assert api_base is None
            assert api_key is None
    
    def test_get_litellm_proxy_config_with_litellm_base_url(self):
        """Test proxy config with LITELLM_BASE_URL."""
        from bloom.utils import get_litellm_proxy_config
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key-123",
            "LITELLM_BASE_URL": "https://litellm.example.com"
        }, clear=False):
            api_base, api_key = get_litellm_proxy_config()
            assert api_base == "https://litellm.example.com"
            assert api_key == "test-key-123"
    
    def test_get_litellm_proxy_config_with_llm_url(self):
        """Test proxy config with LLM_URL (alternative env var)."""
        from bloom.utils import get_litellm_proxy_config
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key-456",
            "LLM_URL": "https://llm.example.com"
        }, clear=False):
            # Make sure LITELLM_BASE_URL is not set
            os.environ.pop("LITELLM_BASE_URL", None)
            
            api_base, api_key = get_litellm_proxy_config()
            assert api_base == "https://llm.example.com"
            assert api_key == "test-key-456"
    
    def test_get_litellm_proxy_config_strips_chat_completions(self):
        """Test that /chat/completions suffix is stripped from URL."""
        from bloom.utils import get_litellm_proxy_config
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key",
            "LITELLM_BASE_URL": "https://litellm.example.com/chat/completions"
        }, clear=False):
            api_base, api_key = get_litellm_proxy_config()
            assert api_base == "https://litellm.example.com"
            assert api_key == "test-key"
    
    def test_is_using_litellm_proxy_true(self):
        """Test is_using_litellm_proxy returns True when configured."""
        from bloom.utils import is_using_litellm_proxy
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key",
            "LITELLM_BASE_URL": "https://litellm.example.com"
        }, clear=False):
            assert is_using_litellm_proxy() is True
    
    def test_is_using_litellm_proxy_false(self):
        """Test is_using_litellm_proxy returns False when not configured."""
        from bloom.utils import is_using_litellm_proxy
        
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LITELLM_API_KEY", None)
            os.environ.pop("LITELLM_BASE_URL", None)
            os.environ.pop("LLM_URL", None)
            
            assert is_using_litellm_proxy() is False


class TestModelTransformation:
    """Tests for model ID transformation for proxy use."""
    
    def test_transform_model_with_provider_prefix(self):
        """Test transforming model with provider prefix."""
        from bloom.utils import transform_model_for_proxy
        
        # anthropic/claude -> openai/claude
        result = transform_model_for_proxy("anthropic/claude-sonnet-4")
        assert result == "openai/claude-sonnet-4"
        
        # openai/gpt-4o should stay as-is
        result = transform_model_for_proxy("openai/gpt-4o")
        assert result == "openai/gpt-4o"
    
    def test_transform_model_without_prefix(self):
        """Test transforming model without provider prefix."""
        from bloom.utils import transform_model_for_proxy
        
        result = transform_model_for_proxy("gpt-4o")
        assert result == "openai/gpt-4o"
        
        result = transform_model_for_proxy("claude-sonnet-4")
        assert result == "openai/claude-sonnet-4"


class TestValidateApiKeys:
    """Tests for API key validation with proxy support."""
    
    def test_validate_api_keys_proxy_mode(self):
        """Test that validation passes in proxy mode without provider keys."""
        from bloom.utils import validate_api_keys
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key",
            "LITELLM_BASE_URL": "https://litellm.example.com"
        }, clear=False):
            config = {
                "understanding": {"model": "anthropic/claude-sonnet-4"},
                "rollout": {"model": "openai/gpt-4o", "target": "anthropic/claude-3-opus"}
            }
            
            is_valid, error = validate_api_keys(config)
            assert is_valid is True
            assert error is None
    
    def test_validate_api_keys_partial_proxy_config_missing_url(self):
        """Test validation fails with only LITELLM_API_KEY set."""
        from bloom.utils import validate_api_keys
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-key"
        }, clear=False):
            os.environ.pop("LITELLM_BASE_URL", None)
            os.environ.pop("LLM_URL", None)
            
            config = {"understanding": {"model": "gpt-4o"}}
            
            is_valid, error = validate_api_keys(config)
            assert is_valid is False
            assert "LITELLM_BASE_URL is missing" in error
    
    def test_validate_api_keys_partial_proxy_config_missing_key(self):
        """Test validation fails with only LITELLM_BASE_URL set."""
        from bloom.utils import validate_api_keys
        
        with patch.dict(os.environ, {
            "LITELLM_BASE_URL": "https://litellm.example.com"
        }, clear=False):
            os.environ.pop("LITELLM_API_KEY", None)
            
            config = {"understanding": {"model": "gpt-4o"}}
            
            is_valid, error = validate_api_keys(config)
            assert is_valid is False
            assert "LITELLM_API_KEY is missing" in error


class TestLiteLLMChatWithProxy:
    """Tests for litellm_chat function with proxy configuration."""
    
    @pytest.fixture
    def mock_completion(self):
        """Create a mock completion response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I'm an AI assistant."
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.__getitem__ = lambda self, key: {"choices": self.choices}[key]
        return mock_response
    
    def test_litellm_chat_uses_proxy_config(self, mock_completion):
        """Test that litellm_chat uses proxy config when set."""
        from bloom.utils import litellm_chat
        
        with patch.dict(os.environ, {
            "LITELLM_API_KEY": "test-proxy-key",
            "LITELLM_BASE_URL": "https://litellm.example.com"
        }, clear=False):
            with patch("bloom.utils.completion_with_retries") as mock_completion_fn:
                mock_completion_fn.return_value = mock_completion
                
                litellm_chat(
                    model_id="anthropic/claude-sonnet-4",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=100
                )
                
                # Verify the call was made with proxy config
                call_kwargs = mock_completion_fn.call_args.kwargs
                assert call_kwargs.get("api_base") == "https://litellm.example.com"
                assert call_kwargs.get("api_key") == "test-proxy-key"
                
                # Verify model was transformed for proxy
                assert mock_completion_fn.call_args.kwargs.get("model") == "openai/claude-sonnet-4"
    
    def test_litellm_chat_without_proxy(self, mock_completion):
        """Test that litellm_chat works without proxy config."""
        from bloom.utils import litellm_chat
        
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LITELLM_API_KEY", None)
            os.environ.pop("LITELLM_BASE_URL", None)
            os.environ.pop("LLM_URL", None)
            
            with patch("bloom.utils.completion_with_retries") as mock_completion_fn:
                mock_completion_fn.return_value = mock_completion
                
                litellm_chat(
                    model_id="anthropic/claude-sonnet-4",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=100
                )
                
                # Verify no proxy config was passed
                call_kwargs = mock_completion_fn.call_args.kwargs
                assert "api_base" not in call_kwargs or call_kwargs.get("api_base") is None
                
                # Verify model was NOT transformed
                assert mock_completion_fn.call_args.kwargs.get("model") == "anthropic/claude-sonnet-4"


# Integration test - only runs if LITELLM_API_KEY and LITELLM_BASE_URL are set
@pytest.mark.skipif(
    not (os.getenv("LITELLM_API_KEY") and (os.getenv("LITELLM_BASE_URL") or os.getenv("LLM_URL"))),
    reason="LiteLLM proxy not configured (set LITELLM_API_KEY and LITELLM_BASE_URL)"
)
class TestLiteLLMProxyIntegration:
    """Integration tests that actually call the LiteLLM proxy."""
    
    def test_basic_completion(self):
        """Test a basic completion call through the proxy."""
        from bloom.utils import litellm_chat, parse_message
        
        response = litellm_chat(
            model_id="gpt-4o",  # Will be transformed to openai/gpt-4o for proxy
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        assert parsed["content"] is not None
        assert len(parsed["content"]) > 0
        print(f"✅ Got response: {parsed['content'][:100]}")
    
    def test_completion_with_system_prompt(self):
        """Test completion with system prompt through the proxy."""
        from bloom.utils import litellm_chat, parse_message
        
        response = litellm_chat(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "What's 2+2?"}],
            system_prompt="You are a math tutor. Always answer with just the number.",
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        assert parsed["content"] is not None
        assert "4" in parsed["content"]
        print(f"✅ Got response: {parsed['content']}")
    
    def test_claude_model_through_proxy(self):
        """Test calling a Claude model through the proxy."""
        from bloom.utils import litellm_chat, parse_message
        
        response = litellm_chat(
            model_id="anthropic/claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Say 'test successful' and nothing else."}],
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        assert parsed["content"] is not None
        print(f"✅ Claude response: {parsed['content'][:100]}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

