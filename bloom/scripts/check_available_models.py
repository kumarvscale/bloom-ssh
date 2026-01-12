#!/usr/bin/env python3
"""
Check available models on the LiteLLM proxy.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
import asyncio


async def check_model(session: aiohttp.ClientSession, model: str, api_key: str, base_url: str) -> dict:
    """Test if a model is available on the proxy."""
    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK'"}],
        "max_tokens": 5,
        "temperature": 0.0,
    }
    
    try:
        async with session.post(url, json=data, headers=headers, timeout=30) as response:
            if response.status == 200:
                return {"model": model, "status": "available", "error": None}
            else:
                error = await response.text()
                return {"model": model, "status": "unavailable", "error": error[:100]}
    except Exception as e:
        return {"model": model, "status": "error", "error": str(e)[:100]}


async def main():
    # Load environment from .env file
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    api_key = os.getenv("LITELLM_API_KEY")
    base_url = os.getenv("LITELLM_BASE_URL")
    
    if not api_key or not base_url:
        print("Error: LITELLM_API_KEY and LITELLM_BASE_URL must be set in .env file")
        return
    
    # Models to check - Gemini variants
    models_to_check = [
        # Gemini 2.x
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-pro",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        # Gemini 3.x (if available)
        "gemini-3.0-flash",
        "gemini-3.0-pro",
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        # Common naming patterns
        "gemini-pro",
        "gemini-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    print(f"Checking models on: {base_url}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_model(session, model, api_key, base_url) for model in models_to_check]
        results = await asyncio.gather(*tasks)
    
    available = []
    for result in results:
        status_icon = "✅" if result["status"] == "available" else "❌"
        print(f"{status_icon} {result['model']}: {result['status']}")
        if result["status"] == "available":
            available.append(result["model"])
    
    print("\n" + "=" * 60)
    print("Available Gemini models:")
    for model in available:
        print(f"  - {model}")
    
    return available


if __name__ == "__main__":
    asyncio.run(main())

