#!/usr/bin/env python3
"""
Test script to view the raw scraped text from articles.
Shows what content the bot is actually scraping and processing.
"""

import sys
import os
import argparse
from datetime import datetime
import json

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Compatibility fix for cgi module
try:
    import cgi
    if not hasattr(cgi, 'parse_header'):
        def _create_parse_header():
            def parse_header(line):
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
        cgi.parse_header = _create_parse_header()
except ImportError:
    import sys
    from urllib.parse import parse_qs, unquote
    def _create_parse_header():
        def parse_header(line):
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
    
    class cgi:
        @staticmethod
        def parse_qs(qs, keep_blank_values=False, strict_parsing=False):
            return parse_qs(qs, keep_blank_values=keep_blank_values, strict_parsing=strict_parsing)
        
        @staticmethod
        def unquote(s):
            return unquote(s)
        
        @staticmethod
        def parse_header(line):
            return _create_parse_header()(line)
    
    sys.modules['cgi'] = cgi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'newsbot'))

def main():
    parser = argparse.ArgumentParser(description='View scraped article text (output is always saved to file)')
    parser.add_argument('--output', '-o', type=str, default='scraped_text_output.txt', help='Output file name (default: scraped_text_output.txt)')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Limit number of articles (default: 5)')
    parser.add_argument('--full-content', action='store_true', help='Show full article content (if not set, shows first 2000 chars)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Scraped Article Text Viewer")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check for OpenAI API key if needed
    config_file = os.path.join(os.path.dirname(__file__), 'newsbot', 'config.json')
    summarizer_type = "sumy"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            summarizer_config = config.get("summarizer", {})
            summarizer_type = summarizer_config.get("type", "sumy")
    except:
        pass
    
    if summarizer_type == "openai":
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  WARNING: OpenAI API key not set")
            print("   The bot is configured to use OpenAI summarizer.")
            print("   Summaries may not be generated, but raw content will be shown.")
            print()
    
    # Import after cgi fix
    scrape_news = None
    try:
        from scrape_news import scrape_news
    except ValueError as e:
        if "OpenAI API key required" in str(e):
            print("=" * 80)
            print("WARNING: OpenAI API key not found")
            print("=" * 80)
            print()
            print("The bot is configured to use OpenAI summarizer.")
            print("Without the API key, summaries won't be generated.")
            print()
            print("To fix this:")
            print("  Windows PowerShell: $env:OPENAI_API_KEY='sk-your-key-here'")
            print("  Windows CMD: set OPENAI_API_KEY=sk-your-key-here")
            print()
            print("Cannot continue without API key (scraper requires it for initialization).")
            print("Please set OPENAI_API_KEY and try again.")
            return
        else:
            print(f"Error importing scrape_news: {e}")
            import traceback
            traceback.print_exc()
            return
    except Exception as e:
        print(f"Error importing scrape_news: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if scrape_news is None:
        print("Error: Could not import scrape_news")
        return
    
    # Scrape articles
    print("Scraping articles...")
    print("-" * 80)
    try:
        data = scrape_news()
        articles = data.get('articles', [])
        print(f"Scraped {len(articles)} articles")
        print()
    except Exception as e:
        print(f"Error scraping: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not articles:
        print("No articles found!")
        return
    
    # Limit articles
    articles = articles[:args.limit]
    
    output_lines = []
    
    def add_line(text=""):
        output_lines.append(text)
        print(text)
    
    add_line("=" * 80)
    add_line("📄 SCRAPED ARTICLE TEXT")
    add_line("=" * 80)
    add_line()
    
    for i, article in enumerate(articles, 1):
        add_line()
        add_line("=" * 80)
        add_line(f"ARTICLE {i} of {len(articles)}")
        add_line("=" * 80)
        add_line()
        
        # Basic info
        url = article.get('url', 'No URL')
        title_sv = article.get('title_sv', 'No title')
        category = article.get('category', 'Unknown')
        scraped_at = article.get('scraped_at', 'Unknown')
        
        add_line(f"Category: {category}")
        add_line(f"URL: {url}")
        add_line(f"Scraped at: {scraped_at}")
        add_line()
        
        # Title
        add_line("─" * 80)
        add_line("TITLE (Swedish):")
        add_line("─" * 80)
        add_line(title_sv)
        add_line(f"(Length: {len(title_sv)} characters)")
        add_line()
        
        # Full scraped content (this is what was actually scraped from the page)
        content_sv = article.get('content_sv', '')
        if content_sv:
            add_line("─" * 80)
            add_line("SCRAPED CONTENT (Swedish):")
            add_line("─" * 80)
            if args.full_content:
                # Show full content
                add_line(content_sv)
            else:
                # Show first 2000 characters by default
                content_preview = content_sv[:2000] if len(content_sv) > 2000 else content_sv
                add_line(content_preview)
                if len(content_sv) > 2000:
                    add_line(f"\n... (truncated, total length: {len(content_sv)} characters)")
                    add_line(f"Use --full-content to see the complete text")
            add_line(f"(Length: {len(content_sv)} characters)")
            add_line(f"(Words: {len(content_sv.split())} words)")
            add_line()
        else:
            add_line("─" * 80)
            add_line("SCRAPED CONTENT (Swedish):")
            add_line("─" * 80)
            add_line("No content found (content_sv not in article data)")
            add_line()
        
        # Raw JSON (for debugging) - exclude summary
        add_line("─" * 80)
        add_line("RAW DATA (JSON):")
        add_line("─" * 80)
        # Include content_sv in JSON if it exists (truncate if too long), exclude summary
        article_copy = {k: v for k, v in article.items() if k != 'summary_sv'}
        if 'content_sv' in article_copy and article_copy['content_sv']:
            if not args.full_content and len(article_copy['content_sv']) > 500:
                article_copy['content_sv'] = article_copy['content_sv'][:500] + "... (truncated)"
        add_line(json.dumps(article_copy, indent=2, ensure_ascii=False))
        add_line()
    
    # Statistics
    add_line()
    add_line("=" * 80)
    add_line("STATISTICS")
    add_line("=" * 80)
    
    articles_with_content = sum(1 for a in articles if a.get('content_sv'))
    avg_title_len = sum(len(a.get('title_sv', '')) for a in articles) / len(articles) if articles else 0
    avg_content_len = sum(len(a.get('content_sv', '')) for a in articles) / articles_with_content if articles_with_content else 0
    
    add_line(f"Total articles: {len(articles)}")
    add_line(f"Articles with content: {articles_with_content}")
    add_line(f"Average title length: {avg_title_len:.0f} characters")
    add_line(f"Average content length: {avg_content_len:.0f} characters")
    add_line()
    
    add_line("=" * 80)
    add_line("Display complete!")
    add_line("=" * 80)
    
    # Always save to file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"\nOutput saved to: {args.output}")
    except Exception as e:
        print(f"\nError saving file: {e}")

if __name__ == "__main__":
    main()

