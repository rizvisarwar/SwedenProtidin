#!/usr/bin/env python3
"""
Automated Swedish News to Facebook Bot
Fetches news from scrape_news.py (Ekonomi and Sverige categories), translates to Bangla, and posts to Facebook Page.
"""

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




def translate_text(text, dest='bn'):
    """Translate text to Bangla using googletrans."""
    if not text or not text.strip():
        return ""
    
    try:
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Limit text length to avoid API issues
        if len(text) > 8000:
            text = text[:8000]
        
        result = translator.translate(text, dest=dest)
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
    
    # Scrape news from multiple categories
    logger.info("Scraping news from marcusoscarsson.se (Ekonomi and Sverige categories)...")
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
            # Translate title to Bangla
            title_bn = translate_text(title_sv, dest='bn')
            if not title_bn:
                title_bn = title_sv  # Fallback to original
            
            # Translate summary to Bangla
            summary_bn = ""
            if summary_sv:
                summary_bn = translate_text(summary_sv, dest='bn')
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

