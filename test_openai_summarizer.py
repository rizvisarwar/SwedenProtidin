#!/usr/bin/env python3
"""
Quick test script for OpenAI summarizer.
Tests the summarizer with a sample Swedish news article.
"""

import os
import sys

# Add newsbot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'newsbot'))

from summarizer import create_summarizer

# Sample Swedish news article text
sample_text = """
Energidryckproducenten Celsius växer så det knakar. Från 2022 till 2023 ökade omsättningen med nästan 100 miljoner kronor. 
Nu kommer nästa glädjebesked. Framgångssagan fortsätter för Celsius som fortsatte att växa under 2024.

Företaget har etablerat sig starkt på den svenska marknaden och ser nu möjligheter att expandera internationellt. 
VD:n uttrycker stor optimism för framtiden och menar att tillväxten kommer att fortsätta.

Analytiker pekar på att konsumenternas intresse för hälsosamma energidrycker har ökat markant, vilket gynnar Celsius. 
Produkten har positionerat sig som ett alternativ till traditionella energidrycker med fokus på naturliga ingredienser.
"""

def test_openai_summarizer():
    """Test OpenAI summarizer with sample text."""
    
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("\nTo get an API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Sign up or log in")
        print("3. Create a new API key")
        print("4. Set it as environment variable:")
        print("   PowerShell: $env:OPENAI_API_KEY='sk-your-key-here'")
        print("   CMD: set OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print("✅ OpenAI API key found")
    print(f"📝 Testing with sample Swedish news article...")
    print(f"📄 Original text length: {len(sample_text)} characters\n")
    print("=" * 60)
    print("ORIGINAL TEXT:")
    print("=" * 60)
    print(sample_text)
    print("\n")
    
    try:
        # Create OpenAI summarizer
        print("🤖 Creating OpenAI summarizer...")
        summarizer = create_summarizer("openai", api_key=api_key)
        
        # Generate summary
        print("✨ Generating summary...")
        summary = summarizer.summarize(sample_text, max_sentences=3)
        
        print("=" * 60)
        print("OPENAI SUMMARY:")
        print("=" * 60)
        print(summary)
        print("\n")
        
        print("✅ Test successful!")
        print(f"📊 Summary length: {len(summary)} characters")
        print(f"📈 Compression ratio: {len(summary)/len(sample_text)*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenAI Summarizer")
    print("=" * 60)
    print()
    
    success = test_openai_summarizer()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ OpenAI summarizer is working correctly!")
        print("You can now use it in the bot by setting config.json to:")
        print('  "type": "openai"')
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed. Please check the error messages above.")
        print("=" * 60)
        sys.exit(1)
