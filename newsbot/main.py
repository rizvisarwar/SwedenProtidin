#!/usr/bin/env python3
"""
Automated Swedish News to Facebook Bot
Fetches news from scrape_news.py, generates full news articles in Bangla using OpenAI, and posts to Facebook Page.
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
    New format: Bangla news article text + source link
    """
    post = ""
    
    if summary_bn:
        post = f"{summary_bn}\n\n"
    
    post += f"🔗 সূত্র: {link}"
    
    return post


def validate_facebook_token():
    """
    Validate Facebook Page Access Token and check required permissions.
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not FB_PAGE_ID or not FB_PAGE_TOKEN:
        return False, "Facebook credentials not set (FB_PAGE_ID, FB_PAGE_TOKEN)"
    
    # Check token validity and get permissions
    debug_url = f"https://graph.facebook.com/{FB_API_VERSION}/debug_token"
    params = {
        'input_token': FB_PAGE_TOKEN,
        'access_token': FB_PAGE_TOKEN
    }
    
    try:
        response = requests.get(debug_url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'data' not in result:
            return False, f"Invalid token response: {result}"
        
        data = result['data']
        
        # Check if token is valid
        if not data.get('is_valid', False):
            error_msg = data.get('error', {}).get('message', 'Token is invalid')
            return False, f"Token is invalid: {error_msg}"
        
        # Check if token is for a page
        if data.get('type') != 'PAGE':
            return False, f"Token type is '{data.get('type', 'unknown')}', expected 'PAGE'. Please use a Page Access Token, not a User Access Token."
        
        # Check if token is for the correct page
        token_page_id = str(data.get('profile_id', ''))
        if token_page_id != str(FB_PAGE_ID):
            return False, f"Token is for page ID '{token_page_id}', but FB_PAGE_ID is set to '{FB_PAGE_ID}'. They must match."
        
        # Get permissions
        scopes = data.get('scopes', [])
        required_permissions = ['pages_read_engagement', 'pages_manage_posts']
        missing_permissions = [perm for perm in required_permissions if perm not in scopes]
        
        if missing_permissions:
            return False, f"Token is missing required permissions: {', '.join(missing_permissions)}. Current permissions: {', '.join(scopes) if scopes else 'none'}"
        
        # Check token expiration
        expires_at = data.get('expires_at', 0)
        if expires_at > 0:
            from datetime import datetime
            exp_time = datetime.fromtimestamp(expires_at)
            logger.info(f"Token expires at: {exp_time}")
        
        logger.info(f"✓ Facebook token validated successfully. Permissions: {', '.join(scopes)}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to validate token: {e}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = f"Failed to validate token: {error_data}"
            except:
                error_msg = f"Failed to validate token: {e.response.text}"
        return False, error_msg


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
    
    # Validate Facebook token and permissions BEFORE proceeding
    logger.info("Validating Facebook Page Access Token...")
    is_valid, error_msg = validate_facebook_token()
    if not is_valid:
        logger.error("=" * 60)
        logger.error("❌ Facebook Page Access Token validation FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {error_msg}")
        logger.error("")
        logger.error("The bot cannot run until the Facebook token issue is fixed.")
        logger.error("")
        logger.error("To fix this issue:")
        logger.error("1. Ensure you have a Page Access Token (not a User Access Token)")
        logger.error("2. The token must have the following permissions:")
        logger.error("   - pages_read_engagement")
        logger.error("   - pages_manage_posts")
        logger.error("3. Your account must be an admin of the page")
        logger.error("4. The token's page ID must match FB_PAGE_ID")
        logger.error("")
        logger.error("You can debug your token at:")
        logger.error("  https://developers.facebook.com/tools/debug/accesstoken/")
        logger.error("=" * 60)
        return
    
    # Check OpenAI API key (required for article generation)
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        logger.error("WARNING: OPENAI_API_KEY not set. Articles will not be generated, only links will be posted.")
    else:
        logger.info(f"OPENAI_API_KEY is set (length: {len(openai_key)} characters)")
    
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
        
        # Debug: Log what we got from scraping
        logger.info(f"Article summary_sv length: {len(summary_sv)} characters")
        if summary_sv:
            logger.info(f"Article summary_sv preview: {summary_sv[:200]}...")
        else:
            logger.warning(f"Article summary_sv is EMPTY - article generation may have failed")
        
        if not title_sv:
            logger.warning("Article missing title, skipping...")
            continue
        
        try:
            # Translate title to Bangla using OpenAI (better quality) with googletrans fallback
            title_bn = translate_text(title_sv, dest='bn', use_openai=True)
            if not title_bn:
                title_bn = title_sv  # Fallback to original
            
            # Check if content is already in Bangla (if OpenAI generated it directly)
            # Check config to see if output_language is set to 'bn'
            import json
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
            content_already_bangla = False
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    summarizer_config = config.get("summarizer", {})
                    if summarizer_config.get("output_language") == "bn" and summarizer_config.get("type") == "openai":
                        content_already_bangla = True
            except:
                pass  # If config read fails, assume we need to translate
            
            # Get Bangla news article (or summary if fallback)
            summary_bn = ""
            if summary_sv:
                if content_already_bangla:
                    # Content is already a full news article in Bangla from OpenAI
                    summary_bn = summary_sv
                    logger.info(f"Using Bangla news article generated directly by OpenAI (length: {len(summary_bn)} chars)")
                else:
                    # Need to translate from Swedish to Bangla (fallback case - should rarely happen)
                    # Use OpenAI for better quality, with googletrans as fallback
                    summary_bn = translate_text(summary_sv, dest='bn', use_openai=True)
                    if not summary_bn:
                        summary_bn = summary_sv  # Fallback to original
            else:
                logger.error(f"ERROR: No summary/article generated for: {title_sv[:50]}... (summary_sv is empty). Check if OPENAI_API_KEY is set and summarizer is working.")
            
            # Check if we have article text to post - skip if empty
            if not summary_bn or not summary_bn.strip():
                logger.error(f"ERROR: summary_bn is empty! Cannot post article without text. Skipping: {title_sv[:50]}...")
                logger.error(f"  This usually means:")
                logger.error(f"  1. OPENAI_API_KEY is not set or invalid")
                logger.error(f"  2. Article generation failed (check logs above for errors)")
                logger.error(f"  3. Summarizer returned empty result")
                skipped_count += 1
                continue  # Skip this article and move to next one
            
            # Debug: Log what we're about to post
            logger.info(f"Bangla article length: {len(summary_bn)} characters")
            logger.info(f"Bangla article preview: {summary_bn[:200]}...")
            
            # Format Facebook post
            fb_message = format_facebook_post(
                title_bn,
                summary_bn,
                url  # Original URL is used as link
            )
            
            # Debug: Log the formatted message
            logger.info(f"Formatted Facebook message length: {len(fb_message)} characters")
            logger.info(f"Formatted Facebook message preview: {fb_message[:300]}...")
            
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

