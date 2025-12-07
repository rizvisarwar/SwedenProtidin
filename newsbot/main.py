#!/usr/bin/env python3
"""
Automated Swedish News to Facebook Bot
Fetches news from RSS feeds, translates to Bangla, and posts to Facebook Page.
"""

import json
import os
import feedparser
import requests
from googletrans import Translator
from datetime import datetime
import logging
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize translator
translator = Translator()

# File paths
RSS_LIST_FILE = os.path.join(os.path.dirname(__file__), 'rss_list.json')
POSTED_DB_FILE = os.path.join(os.path.dirname(__file__), 'posted.json')

# Facebook API
FB_API_VERSION = 'v19.0'
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN')

# Maximum number of articles to post per run
# Set to 1 to post one article per run (bot runs every 4 hours)
# Set to None for unlimited posting (posts all filtered articles)
MAX_POSTS = 1

# Sweden news filtering
SWEDEN_KEYWORDS = [
    "Sverige", "svensk", "Stockholm", "Göteborg", "Malmö", "Skåne",
    "Uppsala", "Norrbotten", "Västerbotten", "Södermanland",
    "Jönköping", "Örebro", "Västmanland", "Halland"
]

BLOCKLIST_KEYWORDS = [
    "USA", "Israel", "Kina", "Ryssland", "China", "Russia",
    "Nato", "EU", "UK", "Germany", "France", "Brazil",
    "Middle East"
]

BLOCKLIST_CATEGORIES = ["utrikes", "world", "international"]


def load_rss_feeds():
    """Load RSS feed URLs from JSON file."""
    try:
        with open(RSS_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"RSS list file not found: {RSS_LIST_FILE}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {RSS_LIST_FILE}")
        return []


def load_posted_articles():
    """Load list of already posted article GUIDs."""
    if os.path.exists(POSTED_DB_FILE):
        try:
            with open(POSTED_DB_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    return set()


def save_posted_article(guid):
    """Save article GUID to posted database."""
    posted = load_posted_articles()
    posted.add(guid)
    with open(POSTED_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(posted), f, ensure_ascii=False, indent=2)


def is_sweden_news(title, description, category, link=""):
    """
    Filter function - filters out articles with 'varlden' or 'expressen-direkt' in the link.
    Returns True to process article, False to skip.
    """
    if not title:
        return False
    
    if not link:
        return True
    
    link_lower = link.lower()
    
    # Filter out articles with 'varlden' (world) in the link
    if 'varlden' in link_lower:
        logger.debug(f"Skipping article (varlden in link): {title[:50]}...")
        return False
    
    # Filter out articles with 'expressen-direkt' in the link
    if 'expressen-direkt' in link_lower:
        logger.debug(f"Skipping article (expressen-direkt in link): {title[:50]}...")
        return False
    
    # Accept all other articles
    return True


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


def clean_description(description):
    """Clean description text by removing HTML tags and CDATA."""
    if not description:
        return ""
    
    import re
    # Remove CDATA wrapper if present
    desc = description.strip()
    desc = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', desc, flags=re.DOTALL)
    
    # Remove HTML tags
    desc = re.sub(r'<[^>]+>', '', desc)
    
    # Clean up whitespace
    desc = ' '.join(desc.split())
    
    return desc


def format_facebook_post(title_bn, description_bn, link):
    """Format the Facebook post message."""
    post = f"{title_bn}\n\n"
    
    if description_bn:
        post += f"📌 {description_bn}\n\n"
    
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


def process_rss_feed(feed_url):
    """Process a single RSS feed and return articles."""
    try:
        logger.info(f"Fetching RSS feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
        
        articles = []
        for entry in feed.entries:
            guid = entry.get('id') or entry.get('link') or entry.get('title', '')
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            description = entry.get('description', '') or entry.get('summary', '')
            
            # Extract category from tags or link
            category = ''
            if hasattr(entry, 'tags') and entry.tags:
                category = ', '.join([tag.get('term', '') for tag in entry.tags])
            # Also check link for category hints (e.g., /utrikes/, /inrikes/)
            if '/utrikes/' in link.lower():
                category = 'utrikes'
            elif '/inrikes/' in link.lower():
                category = 'inrikes'
            
            articles.append({
                'guid': guid,
                'title': title,
                'link': link,
                'description': description,
                'category': category
            })
        
        logger.info(f"Found {len(articles)} articles in feed")
        return articles
        
    except Exception as e:
        logger.error(f"Error processing RSS feed {feed_url}: {e}")
        return []


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
    
    # Load RSS feeds
    rss_feeds = load_rss_feeds()
    if not rss_feeds:
        logger.error("No RSS feeds found. Exiting.")
        return
    
    logger.info(f"Loaded {len(rss_feeds)} RSS feeds")
    
    # Randomly select one RSS feed
    selected_feed = random.choice(rss_feeds)
    logger.info(f"Randomly selected RSS feed: {selected_feed}")
    
    # Load posted articles database
    posted_articles = load_posted_articles()
    logger.info(f"Loaded {len(posted_articles)} previously posted articles")
    
    # Process the selected feed
    all_articles = process_rss_feed(selected_feed)
    
    logger.info(f"Total articles found: {len(all_articles)}")
    
    # Process and post new articles
    posted_count = 0
    filtered_count = 0
    for article in all_articles:
        guid = article['guid']
        
        # Skip if already posted
        if guid in posted_articles:
            logger.debug(f"Skipping already posted article: {article['title'][:50]}...")
            continue
        
        # Filter check - skip articles with 'varlden' in link
        if not is_sweden_news(
            article['title'],
            article.get('description', ''),
            article.get('category', ''),
            article.get('link', '')
        ):
            filtered_count += 1
            continue
        
        try:
            # Translate title
            title_bn = translate_text(article['title'], dest='bn')
            if not title_bn:
                title_bn = article['title']  # Fallback to original
            
            # Clean and translate description
            description_clean = clean_description(article.get('description', ''))
            description_bn = ""
            if description_clean:
                description_bn = translate_text(description_clean, dest='bn')
                if not description_bn:
                    description_bn = description_clean  # Fallback to original
            
            # Format Facebook post
            fb_message = format_facebook_post(
                title_bn,
                description_bn,
                article['link']
            )
            
            # Post to Facebook
            logger.info(f"Posting article: {article['title'][:50]}...")
            if post_to_facebook(fb_message):
                # Mark as posted
                save_posted_article(guid)
                posted_count += 1
                logger.info(f"✓ Successfully posted: {article['title'][:50]}...")
                
                # Stop after posting MAX_POSTS articles (if MAX_POSTS is set)
                if MAX_POSTS is not None and posted_count >= MAX_POSTS:
                    logger.info(f"Reached MAX_POSTS limit ({MAX_POSTS}). Stopping.")
                    break
            else:
                logger.warning(f"✗ Failed to post: {article['title'][:50]}...")
            
            # Add small delay to avoid rate limiting
            import time
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error processing article {article['title'][:50]}...: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info(f"Bot finished. Posted {posted_count} new articles.")
    logger.info(f"Filtered out {filtered_count} articles.")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

