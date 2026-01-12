#!/usr/bin/env python3
"""
Quick test script for Scale's LiteLLM proxy.

This script tests the integration with Scale's internal LiteLLM proxy
at https://litellm.ml.scaleinternal.com

Usage:
    python tests/test_scale_litellm.py
    
Environment variables (optional - defaults provided):
    LITELLM_API_KEY: Your Scale LiteLLM API key
    LITELLM_BASE_URL: The Scale LiteLLM proxy URL
"""

import os
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Default Scale LiteLLM configuration
DEFAULT_LITELLM_BASE_URL = "https://litellm.ml.scaleinternal.com"


def setup_environment():
    """Set up environment variables from .env file if not already set."""
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    if not os.getenv("LITELLM_API_KEY"):
        raise ValueError("LITELLM_API_KEY not set. Please configure it in .env file")
    
    if not os.getenv("LITELLM_BASE_URL") and not os.getenv("LLM_URL"):
        os.environ["LITELLM_BASE_URL"] = DEFAULT_LITELLM_BASE_URL
        print(f"Using default LITELLM_BASE_URL: {DEFAULT_LITELLM_BASE_URL}")


def test_raw_http_call():
    """Test raw HTTP call to verify connectivity (matches user's example)."""
    import aiohttp
    import asyncio
    
    print("\n" + "=" * 60)
    print("TEST: Raw HTTP Call (aiohttp)")
    print("=" * 60)
    
    async def make_call():
        url = os.getenv("LITELLM_BASE_URL", DEFAULT_LITELLM_BASE_URL) + "/chat/completions"
        api_key = os.getenv("LITELLM_API_KEY")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Say exactly: RAW_HTTP_SUCCESS"},
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": 50,
        }
        
        print(f"   URL: {url}")
        print(f"   Model: {data['model']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                response_data = await response.json()
                content = response_data["choices"][0]["message"]["content"]
                return content
    
    try:
        content = asyncio.run(make_call())
        print(f"   Response: {content}")
        print("✅ PASSED: Raw HTTP call successful")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_bloom_litellm_chat():
    """Test Bloom's litellm_chat function with proxy."""
    from bloom.utils import litellm_chat, parse_message, is_using_litellm_proxy
    
    print("\n" + "=" * 60)
    print("TEST: Bloom litellm_chat() with Proxy")
    print("=" * 60)
    
    print(f"   Proxy enabled: {is_using_litellm_proxy()}")
    
    try:
        response = litellm_chat(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "Say exactly: BLOOM_LITELLM_SUCCESS"}],
            max_tokens=50,
            temperature=0.0
        )
        
        parsed = parse_message(response)
        content = parsed["content"]
        
        print(f"   Response: {content}")
        print("✅ PASSED: Bloom litellm_chat successful")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_different_models():
    """Test different models through the proxy."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: Multiple Models Through Proxy")
    print("=" * 60)
    
    models_to_test = [
        "gpt-4o",
        "gpt-4o-mini",
        # Add more models as needed
    ]
    
    results = {}
    
    for model in models_to_test:
        print(f"\n   Testing: {model}")
        try:
            response = litellm_chat(
                model_id=model,
                messages=[{"role": "user", "content": f"Say: MODEL_TEST_{model.upper().replace('-', '_')}"}],
                max_tokens=50,
                temperature=0.0
            )
            
            parsed = parse_message(response)
            content = parsed["content"]
            
            print(f"   Response: {content[:80]}...")
            results[model] = True
            print(f"   ✅ {model}: SUCCESS")
            
        except Exception as e:
            print(f"   ❌ {model}: FAILED - {e}")
            results[model] = False
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n   Results: {passed}/{total} models successful")
    return passed == total


def test_anthropic_through_proxy():
    """Test Anthropic models through proxy (may fail if not available)."""
    from bloom.utils import litellm_chat, parse_message
    
    print("\n" + "=" * 60)
    print("TEST: Anthropic Model Through Proxy (Optional)")
    print("=" * 60)
    
    # Try different Claude model names
    models_to_try = [
        "claude-sonnet-4-20250514",
        "anthropic/claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
    ]
    
    for model in models_to_try:
        print(f"\n   Trying: {model}")
        try:
            response = litellm_chat(
                model_id=model,
                messages=[{"role": "user", "content": "Say: CLAUDE_SUCCESS"}],
                max_tokens=50,
                temperature=0.0
            )
            
            parsed = parse_message(response)
            content = parsed["content"]
            
            print(f"   Response: {content}")
            print(f"   ✅ {model}: SUCCESS")
            return True
            
        except Exception as e:
            print(f"   ⚠️  {model}: {type(e).__name__}: {str(e)[:80]}")
    
    print("\n   ⚠️  No Claude models available on this proxy")
    return False  # Not a failure, just optional


def main():
    """Run all tests."""
    print("=" * 60)
    print("Scale LiteLLM Proxy Integration Tests")
    print("=" * 60)
    
    setup_environment()
    
    tests = [
        ("Raw HTTP Call", test_raw_http_call),
        ("Bloom litellm_chat", test_bloom_litellm_chat),
        ("Multiple Models", test_different_models),
    ]
    
    optional_tests = [
        ("Anthropic Models", test_anthropic_through_proxy),
    ]
    
    passed = 0
    failed = 0
    
    # Run required tests
    for name, test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            failed += 1
    
    # Run optional tests
    print("\n" + "-" * 60)
    print("OPTIONAL TESTS")
    print("-" * 60)
    
    for name, test in optional_tests:
        try:
            test()
        except Exception as e:
            print(f"   {name}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   Required tests: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All required tests passed!")
        print("   Bloom is ready to use with Scale LiteLLM proxy.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

