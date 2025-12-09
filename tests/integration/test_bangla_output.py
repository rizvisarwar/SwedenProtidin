#!/usr/bin/env python3
"""
Test script to preview Bangla summaries and titles without posting to Facebook.
Shows what will be posted so you can verify the quality before actual posting.

Features:
- Preview Bangla text without posting
- Save output to file
- Show detailed statistics
- Character count analysis
- Full text display
"""

import sys
import os
import argparse
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Compatibility fix for Python 3.13+ where cgi module was removed
# googletrans may try to import cgi.parse_header, so we provide a shim
def _create_parse_header():
    """Create parse_header function for cgi compatibility."""
    def parse_header(line):
        """Parse a Content-Type like header."""
        if ';' in line:
            main, params = line.split(';', 1)
            main = main.strip()
            param_dict = {}
            for param in params.split(';'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    param_dict[key.strip()] = value.strip().strip('"\'')
            return main, param_dict
        return line.strip(), {}
    return parse_header

try:
    import cgi
    # cgi exists but may be deprecated - that's fine
    # Ensure parse_header exists (some Python versions may not have it accessible)
    if not hasattr(cgi, 'parse_header'):
        cgi.parse_header = _create_parse_header()
    # Also ensure it's callable (in case of access issues)
    if not callable(getattr(cgi, 'parse_header', None)):
        cgi.parse_header = _create_parse_header()
except ImportError:
    # Create a minimal cgi module shim for compatibility (Python 3.13+)
    import sys
    from urllib.parse import parse_qs, unquote
    
    class cgi:
        @staticmethod
        def parse_qs(qs, keep_blank_values=False, strict_parsing=False):
            return parse_qs(qs, keep_blank_values=keep_blank_values, strict_parsing=strict_parsing)
        
        @staticmethod
        def unquote(s):
            return unquote(s)
        
        @staticmethod
        def parse_header(line):
            """Parse a Content-Type like header."""
            if ';' in line:
                main, params = line.split(';', 1)
                main = main.strip()
                param_dict = {}
                for param in params.split(';'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        param_dict[key.strip()] = value.strip().strip('"\'')
                return main, param_dict
            return line.strip(), {}
    
    sys.modules['cgi'] = cgi
    # Also set parse_header as a module-level function for compatibility
    cgi.parse_header = _create_parse_header()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'newsbot'))

# scrape_news will be imported after API key check
from googletrans import Translator
import json

# Initialize translator
translator = Translator()

def translate_text(text, dest='bn'):
    """Translate text to Bangla using googletrans."""
    if not text or not text.strip():
        return ""
    
    try:
        text = ' '.join(text.split())
        if len(text) > 8000:
            text = text[:8000]
        
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception as e:
        print(f"⚠️  Translation failed: {e}")
        return text

def count_bangla_chars(text):
    """Count Bangla characters in text."""
    if not text:
        return 0
    # Count Bengali Unicode range: U+0980 to U+09FF
    bangla_count = sum(1 for char in text if '\u0980' <= char <= '\u09FF')
    return bangla_count

def analyze_text_quality(title_bn, summary_bn):
    """Analyze text quality metrics."""
    metrics = {
        'title_length': len(title_bn) if title_bn else 0,
        'title_bangla_chars': count_bangla_chars(title_bn) if title_bn else 0,
        'summary_length': len(summary_bn) if summary_bn else 0,
        'summary_bangla_chars': count_bangla_chars(summary_bn) if summary_bn else 0,
        'summary_sentences': summary_bn.count('।') + summary_bn.count('.') if summary_bn else 0,
        'summary_words': len(summary_bn.split()) if summary_bn else 0,
    }
    return metrics

def format_output(articles, output_lang, save_to_file=False, show_stats=True, show_full=True):
    """Format and display output."""
    output_lines = []
    
    def add_line(text=""):
        output_lines.append(text)
        if not save_to_file:
            print(text)
    
    add_line("=" * 80)
    add_line("🧪 Testing Bangla Text Generation")
    add_line("=" * 80)
    add_line(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    add_line()
    
    # Statistics
    total_articles = len(articles)
    articles_with_summary = sum(1 for a in articles if a.get('summary_sv'))
    
    if show_stats:
        add_line("📊 STATISTICS")
        add_line("-" * 80)
        add_line(f"   Total articles scraped: {total_articles}")
        add_line(f"   Articles with summaries: {articles_with_summary}")
        add_line(f"   Summarizer: OpenAI (output_language: {output_lang})")
        add_line()
    
    # Process each article
    add_line("=" * 80)
    add_line("📄 BANGLA TEXT PREVIEW")
    add_line("=" * 80)
    add_line()
    
    all_metrics = []
    
    for i, article in enumerate(articles, 1):
        add_line()
        add_line("=" * 80)
        add_line(f"ARTICLE {i} of {total_articles}")
        add_line("=" * 80)
        
        # Get article data
        title_sv = article.get('title_sv', '')
        summary_sv = article.get('summary_sv', '')
        content_sv = article.get('content_sv', '')  # Scraped content sent to OpenAI
        url = article.get('url', '')
        category = article.get('category', 'Unknown')
        
        if not title_sv:
            add_line("⚠️  No title found, skipping...")
            continue
        
        add_line(f"\n📂 Category: {category}")
        add_line(f"🔗 URL: {url}")
        
        # Original title
        add_line(f"\n📝 Original Swedish Title:")
        add_line(f"   {title_sv}")
        add_line(f"   (Length: {len(title_sv)} characters)")
        
        # Show scraped content that was sent to OpenAI
        if content_sv:
            add_line(f"\n📄 Scraped Content (Sent to OpenAI for Summarization):")
            add_line(f"   {'-'*76}")
            # Show first 1000 characters of the scraped content
            content_preview = content_sv[:1000] if len(content_sv) > 1000 else content_sv
            # Split into lines for better readability
            content_lines = content_preview.split('\n')
            for line in content_lines[:10]:  # Show first 10 lines
                if line.strip():
                    add_line(f"   {line.strip()}")
            if len(content_sv) > 1000:
                add_line(f"   ... (truncated, total length: {len(content_sv)} characters)")
            add_line(f"   {'-'*76}")
            add_line(f"   Total scraped content length: {len(content_sv)} characters")
            add_line(f"   Total words: {len(content_sv.split())} words")
            add_line()
        else:
            add_line(f"\n⚠️  No scraped content found (content_sv not available)")
            add_line()
        
        # Translate title to Bangla
        add_line(f"\n🌐 Translated Bangla Title:")
        title_bn = translate_text(title_sv, dest='bn')
        add_line(f"   {title_bn}")
        add_line(f"   (Length: {len(title_bn)} characters, Bangla chars: {count_bangla_chars(title_bn)})")
        
        # Show summary (generated from the scraped content above)
        if summary_sv:
            add_line(f"\n📄 Summary (Generated by OpenAI from scraped content above):")
            add_line(f"   Language: {'Bangla (generated directly by OpenAI)' if output_lang == 'bn' else 'Swedish (will be translated)'}")
            
            if output_lang != 'bn':
                add_line(f"\n   Original Swedish Summary:")
                add_line(f"   {summary_sv}")
                add_line(f"\n   Translated to Bangla:")
                summary_bn = translate_text(summary_sv, dest='bn')
                add_line(f"   {summary_bn}")
            else:
                summary_bn = summary_sv  # Already in Bangla
                add_line(f"\n   Bangla Summary (Generated by OpenAI):")
                add_line(f"   {summary_bn}")
            
            # Text quality metrics
            metrics = analyze_text_quality(title_bn, summary_bn)
            all_metrics.append(metrics)
            
            if show_stats:
                add_line(f"\n   📊 Text Quality Metrics:")
                add_line(f"      Summary length: {metrics['summary_length']} characters")
                add_line(f"      Bangla characters: {metrics['summary_bangla_chars']} ({metrics['summary_bangla_chars']/max(metrics['summary_length'],1)*100:.1f}%)")
                add_line(f"      Words: {metrics['summary_words']}")
                add_line(f"      Sentences: {metrics['summary_sentences']}")
        else:
            add_line(f"\n⚠️  No summary generated")
            summary_bn = ""
        
        # Show what would be posted
        add_line(f"\n📱 What would be posted to Facebook:")
        add_line(f"   {'-'*76}")
        if summary_bn:
            if show_full:
                add_line(f"   {summary_bn}")
            else:
                # Show truncated version
                truncated = summary_bn[:200] + "..." if len(summary_bn) > 200 else summary_bn
                add_line(f"   {truncated}")
            add_line()
        add_line(f"   🔗 সূত্র: {url}")
        add_line(f"   {'-'*76}")
    
    # Overall statistics
    if show_stats and all_metrics:
        add_line()
        add_line("=" * 80)
        add_line("📊 OVERALL STATISTICS")
        add_line("=" * 80)
        avg_summary_len = sum(m['summary_length'] for m in all_metrics) / len(all_metrics)
        avg_bangla_pct = sum(m['summary_bangla_chars']/max(m['summary_length'],1)*100 for m in all_metrics) / len(all_metrics)
        avg_words = sum(m['summary_words'] for m in all_metrics) / len(all_metrics)
        avg_sentences = sum(m['summary_sentences'] for m in all_metrics) / len(all_metrics)
        
        add_line(f"   Average summary length: {avg_summary_len:.0f} characters")
        add_line(f"   Average Bangla character percentage: {avg_bangla_pct:.1f}%")
        add_line(f"   Average words per summary: {avg_words:.1f}")
        add_line(f"   Average sentences per summary: {avg_sentences:.1f}")
        add_line()
    
    add_line("=" * 80)
    add_line("✅ Preview complete!")
    add_line("=" * 80)
    add_line()
    add_line("💡 Tips:")
    add_line("   - Check the Bangla text quality and readability")
    add_line("   - Verify that summaries are engaging and natural")
    add_line("   - Make sure titles are properly translated")
    add_line("   - If quality is good, the bot is ready to post!")
    add_line()
    
    return output_lines

def main():
    parser = argparse.ArgumentParser(description='Test Bangla text generation without posting to Facebook')
    parser.add_argument('--save', '-s', action='store_true', help='Save output to file')
    parser.add_argument('--output', '-o', type=str, default='tests/output/bangla_test_output.txt', help='Output file name (default: tests/output/bangla_test_output.txt)')
    parser.add_argument('--no-stats', action='store_true', help='Hide statistics')
    parser.add_argument('--truncate', action='store_true', help='Show truncated summaries (first 200 chars)')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Limit number of articles to show (default: 5)')
    
    args = parser.parse_args()
    
    # Load config to check summarizer settings
    config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'newsbot', 'config.json')
    output_lang = "sv"
    summarizer_type = "sumy"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            summarizer_config = config.get("summarizer", {})
            output_lang = summarizer_config.get("output_language", "sv")
            summarizer_type = summarizer_config.get("type", "sumy")
            if not args.no_stats:
                print(f"📋 Config: Summarizer type = {summarizer_type}")
                print(f"📋 Config: Output language = {output_lang}")
                if output_lang == "bn":
                    print("✅ Summaries will be generated directly in Bangla by OpenAI")
                else:
                    print("⚠️  Summaries will be in Swedish, then translated to Bangla")
                print()
    except Exception as e:
        print(f"⚠️  Could not read config: {e}")
        print()
    
    # Check for OpenAI API key if using OpenAI summarizer
    if summarizer_type == "openai":
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("=" * 80)
            print("❌ ERROR: OpenAI API key not found!")
            print("=" * 80)
            print()
            print("The bot is configured to use OpenAI summarizer, but OPENAI_API_KEY")
            print("environment variable is not set.")
            print()
            print("To fix this:")
            print("1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
            print("2. Set the environment variable:")
            print()
            print("   Windows PowerShell:")
            print("   $env:OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("   Windows CMD:")
            print("   set OPENAI_API_KEY=sk-your-key-here")
            print()
            print("   Linux/Mac:")
            print("   export OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("3. Run the test script again")
            print()
            print("=" * 80)
            return
    
    # Import scrape_news after API key check
    try:
        from scrape_news import scrape_news
    except ValueError as e:
        if "OpenAI API key required" in str(e):
            print("=" * 80)
            print("ERROR: OpenAI API key not found!")
            print("=" * 80)
            print()
            print("The summarizer requires an OpenAI API key.")
            print()
            print("To fix this:")
            print("1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
            print("2. Set the environment variable:")
            print()
            print("   Windows PowerShell:")
            print("   $env:OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("   Windows CMD:")
            print("   set OPENAI_API_KEY=sk-your-key-here")
            print()
            print("   Linux/Mac:")
            print("   export OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("3. Run the test script again")
            print()
            print("=" * 80)
            return
        else:
            raise
    
    # Scrape articles
    print("Scraping articles...")
    print("-" * 80)
    try:
        data = scrape_news()
        articles = data.get('articles', [])
        print(f"✅ Scraped {len(articles)} articles")
        print()
    except ValueError as e:
        if "OpenAI API key required" in str(e):
            print("=" * 80)
            print("❌ ERROR: OpenAI API key not found!")
            print("=" * 80)
            print()
            print("The summarizer requires an OpenAI API key.")
            print()
            print("To fix this:")
            print("1. Get your OpenAI API key from: https://platform.openai.com/api-keys")
            print("2. Set the environment variable:")
            print()
            print("   Windows PowerShell:")
            print("   $env:OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("   Windows CMD:")
            print("   set OPENAI_API_KEY=sk-your-key-here")
            print()
            print("   Linux/Mac:")
            print("   export OPENAI_API_KEY='sk-your-key-here'")
            print()
            print("3. Run the test script again")
            print()
            print("=" * 80)
        else:
            print(f"❌ Error scraping: {e}")
        return
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not articles:
        print("⚠️  No articles found!")
        return
    
    # Limit articles
    articles = articles[:args.limit]
    
    # Format and display output
    output_lines = format_output(
        articles, 
        output_lang, 
        save_to_file=args.save,
        show_stats=not args.no_stats,
        show_full=not args.truncate
    )
    
    # Save to file if requested
    if args.save:
        output_file = args.output
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            print(f"\n💾 Output saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Error saving file: {e}")

if __name__ == "__main__":
    main()

