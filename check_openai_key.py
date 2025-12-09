#!/usr/bin/env python3
"""
Quick script to check if OpenAI API key is valid.
"""

import os
import requests

api_key = os.environ.get('OPENAI_API_KEY')

if not api_key:
    print("=" * 80)
    print("❌ ERROR: OPENAI_API_KEY environment variable is not set!")
    print("=" * 80)
    print()
    print("To set it:")
    print("  Windows PowerShell: $env:OPENAI_API_KEY='sk-your-key-here'")
    print("  Windows CMD: set OPENAI_API_KEY=sk-your-key-here")
    print("  Linux/Mac: export OPENAI_API_KEY='sk-your-key-here'")
    exit(1)

print("=" * 80)
print("🔍 Checking OpenAI API Key...")
print("=" * 80)
print()
print(f"API Key (first 10 chars): {api_key[:10]}...")
print()

# Test the API key with a simple request
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Say 'test' if you can read this."}
    ],
    "max_tokens": 10
}

try:
    print("Sending test request to OpenAI API...")
    response = requests.post(url, headers=headers, json=data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS: API key is valid!")
        print(f"Response: {result['choices'][0]['message']['content']}")
        print()
        print("Your OpenAI API key is working correctly.")
    elif response.status_code == 401:
        print("❌ ERROR: 401 Unauthorized")
        print()
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_msg = error_data['error'].get('message', 'Unknown error')
                print(f"Error message: {error_msg}")
                print()
                if 'Invalid API key' in error_msg or 'Incorrect API key' in error_msg:
                    print("Possible causes:")
                    print("  1. API key is incorrect or mistyped")
                    print("  2. API key has been revoked")
                    print("  3. API key format is wrong (should start with 'sk-')")
                elif 'expired' in error_msg.lower():
                    print("Possible causes:")
                    print("  1. API key has expired")
                    print("  2. Account subscription has ended")
        except:
            print("Could not parse error response")
        print()
        print("To fix this:")
        print("  1. Go to https://platform.openai.com/api-keys")
        print("  2. Check if your API key is still active")
        print("  3. Create a new API key if needed")
        print("  4. Make sure you copy the full key (starts with 'sk-')")
        print("  5. Set it again: $env:OPENAI_API_KEY='sk-your-new-key-here'")
    elif response.status_code == 429:
        print("⚠️  WARNING: Rate limit exceeded")
        print("Your API key is valid but you've hit the rate limit.")
        print("Wait a few minutes and try again.")
    else:
        print(f"❌ ERROR: Unexpected status code {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Response: {response.text[:200]}")
    
except requests.exceptions.RequestException as e:
    print(f"❌ ERROR: Network error - {e}")
    print("Check your internet connection and try again.")

print()
print("=" * 80)

