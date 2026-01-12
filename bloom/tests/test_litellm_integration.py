#!/usr/bin/env python3
"""
Integration tests for LiteLLM proxy.

This script tests actual API calls to your LiteLLM proxy.
Run this manually after setting up your environment variables.

Usage:
    # Configure your LiteLLM proxy credentials in .env file
    # See .env.example for the template
    
    # Run the tests
    python tests/test_litellm_integration.py
    
    # Or with pytest
    pytest tests/test_litellm_integration.py -v -s
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_environment():
    """Check if LiteLLM proxy is configured."""
    api_key = os.getenv("LITELLM_API_KEY")
    api_base = os.getenv("LITELLM_BASE_URL") or os.getenv("LLM_URL")
    
    if not api_key:
        print("❌ LITELLM_API_KEY environment variable not set")
        print("   Set it with: export LITELLM_API_KEY=your_api_key")
        return False
    
    if not api_base:
        print("❌ LITELLM_BASE_URL (or LLM_URL) environment variable not set")
        print("   Set it with: export LITELLM_BASE_URL=https://your-litellm-proxy.com")
        return False
    
    print(f"✅ LiteLLM Proxy configured:")
    print(f"   API Base: {api_base}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    return True


def test_proxy_config():
    """Test that proxy configuration is correctly detected."""
    from bloom.utils import get_litellm_proxy_config, is_using_litellm_proxy
    
    print("\n" + "=" * 60)
    print("TEST: Proxy Configuration Detection")
    print("=" * 60)
    
    api_base, api_key = get_litellm_proxy_config()
    using_proxy = is_using_litellm_proxy()
    
    print(f"   get_litellm_proxy_config() -> api_base={api_base}, api_key={'*' * 10 if api_key else None}")
    print(f"   is_using_litellm_proxy() -> {using_proxy}")
    
    assert using_proxy, "Expected is_using_litellm_proxy() to return True"
    assert api_base is not None, "Expected api_base to be set"
    assert api_key is not None, "Expected api_key to be set"
    
    print("✅ PASSED: Proxy configuration correctly detected")
    return True


def test_model_transformation():
    """Test model ID transformation for proxy."""
    from bloom.utils import transform_model_for_proxy
    
    print("\n" + "=" * 60)
    print("TEST: Model ID Transformation")
    print("=" * 60)
    
    test_cases = [
        ("anthropic/claude-sonnet-4", "openai/claude-sonnet-4"),
        ("openai/gpt-4o", "openai/gpt-4o"),
        ("gpt-4o", "openai/gpt-4o"),
        ("claude-3-opus", "openai/claude-3-opus"),
        ("google/gemini-pro", "openai/gemini-pro"),
    ]
    
    for input_model, expected_output in test_cases:
        result = transform_model_for_proxy(input_model)
        status = "✅" if result == expected_output else "❌"
        print(f"   {status} {input_model} -> {result} (expected: {expected_output})")
        assert result == expected_output, f"Expected {expected_output}, got {result}"
    
    print("✅ PASSED: All model transformations correct")
    return True


def test_basic_gpt_call():
    """Test a basic GPT-4o call through the proxy."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: Basic GPT-4o Call")
    print("=" * 60)
    
    print("   Calling GPT-4o with a simple prompt...")
    
    try:
        response = litellm_chat(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "Respond with exactly: LITELLM_PROXY_TEST_SUCCESS"}],
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        content = parsed["content"]
        
        print(f"   Response: {content}")
        
        assert content is not None, "Expected non-null content"
        assert len(content) > 0, "Expected non-empty content"
        
        print("✅ PASSED: GPT-4o call successful")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        raise


def test_gpt_with_system_prompt():
    """Test GPT call with system prompt."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: GPT-4o with System Prompt")
    print("=" * 60)
    
    print("   Calling GPT-4o with system prompt...")
    
    try:
        response = litellm_chat(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            system_prompt="You are a geography expert. Answer in exactly one word.",
            max_tokens=20,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        content = parsed["content"]
        
        print(f"   Response: {content}")
        
        assert content is not None, "Expected non-null content"
        assert "paris" in content.lower(), f"Expected 'Paris' in response, got: {content}"
        
        print("✅ PASSED: System prompt handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        raise


def test_claude_model():
    """Test calling Claude model through the proxy."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: Claude Model Call")
    print("=" * 60)
    
    print("   Calling Claude (will be routed through proxy)...")
    
    try:
        # Try with explicit anthropic prefix first
        response = litellm_chat(
            model_id="anthropic/claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Say exactly: CLAUDE_TEST_SUCCESS"}],
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        content = parsed["content"]
        
        print(f"   Response: {content}")
        
        assert content is not None, "Expected non-null content"
        
        print("✅ PASSED: Claude model call successful")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        print("   Note: This might fail if Claude models are not available on your proxy")
        raise


def test_tool_calling():
    """Test function/tool calling through the proxy."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: Tool/Function Calling")
    print("=" * 60)
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g., San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    print("   Calling GPT-4o with tool definition...")
    
    try:
        response = litellm_chat(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
            tools=tools,
            tool_choice="auto",
            max_tokens=200,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        
        print(f"   Content: {parsed['content']}")
        print(f"   Tool calls: {parsed['tool_calls']}")
        
        # The model should either make a tool call or respond with text
        assert parsed["content"] is not None or parsed["tool_calls"] is not None, \
            "Expected either content or tool_calls"
        
        if parsed["tool_calls"]:
            print("   ✓ Model made a tool call")
            tool_call = parsed["tool_calls"][0]
            assert tool_call["function"]["name"] == "get_weather", \
                f"Expected get_weather, got {tool_call['function']['name']}"
        
        print("✅ PASSED: Tool calling works correctly")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        raise


def test_api_key_validation():
    """Test that API key validation works with proxy mode."""
    from bloom.utils import validate_api_keys
    
    print("\n" + "=" * 60)
    print("TEST: API Key Validation (Proxy Mode)")
    print("=" * 60)
    
    # With proxy configured, validation should pass regardless of provider keys
    config = {
        "understanding": {"model": "anthropic/claude-sonnet-4"},
        "ideation": {"model": "openai/gpt-4o"},
        "rollout": {
            "model": "anthropic/claude-opus-4",
            "target": "openai/gpt-4-turbo"
        },
        "judgment": {"model": "google/gemini-pro"}
    }
    
    print("   Validating config with multiple providers...")
    
    is_valid, error = validate_api_keys(config)
    
    if is_valid:
        print("   ✓ Validation passed (proxy mode - no provider keys needed)")
        print("✅ PASSED: API key validation works in proxy mode")
        return True
    else:
        print(f"   ✗ Validation failed: {error}")
        raise AssertionError(f"Expected validation to pass in proxy mode, got error: {error}")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("LiteLLM Proxy Integration Tests")
    print("=" * 60)
    
    if not check_environment():
        print("\n❌ Tests aborted: Environment not configured")
        return False
    
    tests = [
        test_proxy_config,
        test_model_transformation,
        test_api_key_validation,
        test_basic_gpt_call,
        test_gpt_with_system_prompt,
    ]
    
    # Optional tests that might fail depending on proxy configuration
    optional_tests = [
        ("Claude Model", test_claude_model),
        ("Tool Calling", test_tool_calling),
    ]
    
    passed = 0
    failed = 0
    
    # Run required tests
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test failed: {str(e)}")
    
    # Run optional tests
    for name, test in optional_tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n⚠️  Optional test '{name}' failed: {str(e)}")
            print("   (This may be expected depending on your proxy configuration)")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

