#!/usr/bin/env python3
"""
Automated Swedish News to Facebook Bot
Fetches news from scrape_news.py (Ekonomi and Sverige categories), translates to Bangla, and posts to Facebook Page.
"""

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

import json
import os
import requests
from googletrans import Translator
from datetime import datetime
import logging
from scrape_news import scrape_news

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize translator
translator = Translator()

# File paths
POSTED_DB_FILE = os.path.join(os.path.dirname(__file__), 'posted.json')

# Facebook API
FB_API_VERSION = 'v19.0'
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN')

# Maximum number of articles to post per run
# Set to 1 to post one article per run (bot runs every 4 hours)
# Set to None for unlimited posting (posts all filtered articles)
MAX_POSTS = 1


def normalize_url(url):
    """
    Normalize URL to ensure consistent format for duplicate checking.
    Removes trailing slashes and ensures consistent format.
    """
    if not url:
        return ""
    url = url.strip()
    # Remove trailing slash for consistency
    if url.endswith('/'):
        url = url[:-1]
    return url


def load_posted_articles():
    """Load list of already posted article URLs (normalized)."""
    if os.path.exists(POSTED_DB_FILE):
        try:
            with open(POSTED_DB_FILE, 'r', encoding='utf-8') as f:
                urls = json.load(f)
                # Normalize all URLs in the database
                return {normalize_url(url) for url in urls if url}
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    return set()


def save_posted_article(url):
    """Save article URL to posted database (normalized)."""
    posted = load_posted_articles()
    normalized_url = normalize_url(url)
    if normalized_url:
        posted.add(normalized_url)
        with open(POSTED_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(posted)), f, ensure_ascii=False, indent=2)




def translate_text(text, dest='bn', use_openai=True):
    """
    Translate text to Bangla.
    
    Uses OpenAI for better quality translation, with googletrans as fallback.
    
    Args:
        text: Text to translate
        dest: Destination language (default: 'bn' for Bangla)
        use_openai: If True, try OpenAI first (better quality), then fallback to googletrans
    
    Returns:
        Translated text, or original if translation fails
    """
    if not text or not text.strip():
        return ""
    
    # Try OpenAI translation first (if enabled and API key available)
    if use_openai:
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            try:
                import requests
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Truncate if too long (titles are usually short, but be safe)
                text_to_translate = text[:500] if len(text) > 500 else text
                
                prompt = f"Translate the following Swedish text to Bangla (Bengali). Only return the translation, nothing else.\n\n{text_to_translate}"
                
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a professional translator. Translate Swedish text to Bangla (Bengali) accurately and naturally."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.3,  # Lower temperature for more accurate translation
                }
                
                response = requests.post(url, headers=headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    translated = result['choices'][0]['message']['content'].strip()
                    # Remove quotes if OpenAI wrapped the translation
                    if translated.startswith('"') and translated.endswith('"'):
                        translated = translated[1:-1]
                    if translated.startswith("'") and translated.endswith("'"):
                        translated = translated[1:-1]
                    logger.debug("Title translated using OpenAI")
                    return translated
                # If OpenAI fails, fall through to googletrans
            except Exception as e:
                logger.debug(f"OpenAI translation failed, using googletrans fallback: {e}")
                # Fall through to googletrans
    
    # Fallback to googletrans (free, but lower quality)
    try:
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Limit text length to avoid API issues
        if len(text) > 8000:
            text = text[:8000]
        
        result = translator.translate(text, dest=dest)
        logger.debug("Title translated using googletrans (fallback)")
        return result.text
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text  # Return original if translation fails




def format_facebook_post(title_bn, summary_bn, link):
    """
    Format the Facebook post message.
    New format: Bangla summary text + source link
    """
    post = ""
    
    if summary_bn:
        post = f"{summary_bn}\n\n"
    
    post += f"🔗 সূত্র: {link}"
    
    return post


def post_to_facebook(message):
    """Post message to Facebook Page using Graph API."""
    if not FB_PAGE_ID or not FB_PAGE_TOKEN:
        logger.error("Facebook credentials not set (FB_PAGE_ID, FB_PAGE_TOKEN)")
        return False
    
    url = f"https://graph.facebook.com/{FB_API_VERSION}/{FB_PAGE_ID}/feed"
    
    params = {
        'message': message,
        'access_token': FB_PAGE_TOKEN
    }
    
    try:
        response = requests.post(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'id' in result:
            logger.info(f"Successfully posted to Facebook. Post ID: {result['id']}")
            return True
        else:
            logger.error(f"Facebook API error: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to post to Facebook: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Facebook API response: {error_data}")
            except:
                logger.error(f"Facebook API response: {e.response.text}")
        return False




def main():
    """Main function to orchestrate the news bot."""
    logger.info("=" * 60)
    logger.info("Swedish News to Facebook Bot - Starting")
    logger.info("=" * 60)
    
    # Check environment variables
    if not FB_PAGE_ID or not FB_PAGE_TOKEN:
        logger.error("Required environment variables not set:")
        logger.error("  - FB_PAGE_ID")
        logger.error("  - FB_PAGE_TOKEN")
        return
    
    # Load posted articles database
    posted_articles = load_posted_articles()
    logger.info(f"Loaded {len(posted_articles)} previously posted articles")
    
    # Scrape news from configured URLs
    logger.info("Scraping news from marcusoscarsson.se...")
    try:
        scraped_data = scrape_news()
        all_articles = scraped_data.get('articles', [])
        logger.info(f"Scraped {len(all_articles)} articles")
    except Exception as e:
        logger.error(f"Error scraping news: {e}")
        return
    
    if not all_articles:
        logger.warning("No articles found. Exiting.")
        return
    
    # Process and post new articles
    posted_count = 0
    skipped_count = 0
    for article in all_articles:
        # Use URL as unique identifier
        url = article.get('url', '')
        if not url:
            logger.warning("Article missing URL, skipping...")
            continue
        
        # Normalize URL for consistent duplicate checking
        normalized_url = normalize_url(url)
        
        # Skip if already posted
        if normalized_url in posted_articles:
            title = article.get('title_sv', 'Unknown')
            logger.info(f"⏭️  Skipping already posted article: {title[:50]}... (URL: {normalized_url[:60]}...)")
            skipped_count += 1
            continue
        
        # Get title and summary
        title_sv = article.get('title_sv', '')
        summary_sv = article.get('summary_sv', '')
        
        if not title_sv:
            logger.warning("Article missing title, skipping...")
            continue
        
        try:
            # Translate title to Bangla using OpenAI (better quality) with googletrans fallback
            title_bn = translate_text(title_sv, dest='bn', use_openai=True)
            if not title_bn:
                title_bn = title_sv  # Fallback to original
            
            # Check if summary is already in Bangla (if OpenAI generated it directly)
            # Check config to see if output_language is set to 'bn'
            import json
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            summary_already_bangla = False
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    summarizer_config = config.get("summarizer", {})
                    if summarizer_config.get("output_language") == "bn" and summarizer_config.get("type") == "openai":
                        summary_already_bangla = True
            except:
                pass  # If config read fails, assume we need to translate
            
            # Translate summary to Bangla (only if not already in Bangla)
            summary_bn = ""
            if summary_sv:
                if summary_already_bangla:
                    # Summary is already in Bangla from OpenAI
                    summary_bn = summary_sv
                    logger.info("Using Bangla summary generated directly by OpenAI")
                else:
                    # Need to translate from Swedish to Bangla (fallback case - should rarely happen)
                    # Use OpenAI for better quality, with googletrans as fallback
                    summary_bn = translate_text(summary_sv, dest='bn', use_openai=True)
                    if not summary_bn:
                        summary_bn = summary_sv  # Fallback to original
            
            # Format Facebook post
            fb_message = format_facebook_post(
                title_bn,
                summary_bn,
                url  # Original URL is used as link
            )
            
            # Post to Facebook
            logger.info(f"Posting article: {title_sv[:50]}...")
            if post_to_facebook(fb_message):
                # Mark as posted (save normalized URL)
                save_posted_article(normalized_url)
                posted_count += 1
                logger.info(f"✓ Successfully posted: {title_sv[:50]}...")
                
                # Stop after posting MAX_POSTS articles (if MAX_POSTS is set)
                if MAX_POSTS is not None and posted_count >= MAX_POSTS:
                    logger.info(f"Reached MAX_POSTS limit ({MAX_POSTS}). Stopping.")
                    break
            else:
                logger.warning(f"✗ Failed to post: {title_sv[:50]}...")
            
            # Add small delay to avoid rate limiting
            import time
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error processing article {title_sv[:50]}...: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info(f"Bot finished. Posted {posted_count} new articles.")
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} already posted articles.")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

