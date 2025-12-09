import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import json
import os
from summarizer import create_summarizer

# Load configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Load configuration from config.json file."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default fallback configuration
        return {
            "base_url": "https://marcusoscarsson.se",
            "urls": ["https://marcusoscarsson.se/sverige/"]
        }
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}")
        raise

config = load_config()
BASE_URL = config.get("base_url", "https://marcusoscarsson.se")

# Support URL-based scraping (new) and category-based scraping (backward compatibility)
if "urls" in config:
    # New: Use list of URLs directly
    SCRAPE_URLS = config["urls"]
    USE_URLS = True
elif "categories" in config:
    # Old: Build URLs from categories
    CATEGORIES = config["categories"]
    SCRAPE_URLS = [f"{BASE_URL}/category/{cat}/" for cat in CATEGORIES]
    USE_URLS = False
elif "category" in config:
    # Old: Single category
    CATEGORIES = [config["category"]]
    SCRAPE_URLS = [f"{BASE_URL}/category/{CATEGORIES[0]}/"]
    USE_URLS = False
else:
    # Default fallback
    SCRAPE_URLS = [f"{BASE_URL}/category/ekonomi/"]
    USE_URLS = False

# Initialize summarizer (Dependency Injection - follows SOLID principles)
# Read summarizer config from config.json
_summarizer_config = config.get("summarizer", {})
_summarizer_type = _summarizer_config.get("type", "sumy")
_summarizer_language = _summarizer_config.get("language", "sv")
_summarizer_output_language = _summarizer_config.get("output_language")  # Optional: target language for summary
_summarizer_kwargs = {}

# Only add language parameter for summarizers that support it (not OpenAI)
if _summarizer_type in ["sumy", "textrank", "huggingface"]:
    _summarizer_kwargs["language"] = _summarizer_language

# Add OpenAI-specific parameters
if _summarizer_type == "openai":
    _summarizer_kwargs["api_key"] = os.environ.get("OPENAI_API_KEY")
    # If output_language is specified, OpenAI can generate summary directly in that language
    if _summarizer_output_language:
        _summarizer_kwargs["output_language"] = _summarizer_output_language

_summarizer = create_summarizer(_summarizer_type, **_summarizer_kwargs)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

def fetch_html(url):
    """Fetch HTML content from URL with error handling."""
    time.sleep(1.5)  # polite delay
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        raise

def parse_category_page(html, category_name=None):
    """
    Parse category page to extract article links.
    
    Args:
        html: HTML content of the category page
        category_name: Optional category name to include in article metadata
    
    Returns:
        List of article dictionaries with title_sv, url, and optionally category
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    seen_urls = set()  # Track seen URLs to avoid duplicates

    # Try several possible selectors (in order of preference)
    selectors = [
        "article h2 a",
        "h2.entry-title a",
        ".post h2 a",
        ".post-title a",
        "h2 a",
        ".post-preview-image a",  # For Sverige page structure
        "div.post-preview a",  # Alternative structure
    ]

    links = []
    for sel in selectors:
        found = soup.select(sel)
        if found and len(found) > 0:  # Make sure we actually found links
            links = found
            break
    
    # Special handling for .post-preview-image structure (Sverige page)
    # In this structure, the image link has no text, but there's a sibling link with the title
    if links and all(not link.get_text(strip=True) for link in links[:3]):
        # Links have no text, look for title in sibling elements
        processed_links = []
        for link in links:
            url = link.get("href", "")
            if not url:
                continue
            
            # Find the container (posts-header)
            container = link.find_parent(class_="posts-header")
            if container:
                # Find the title link (post-link) or h4 in the container
                title_link = container.find('a', class_="post-link")
                if title_link:
                    # Get title from h4 inside the link, or from link text
                    h4 = title_link.find('h4')
                    if h4:
                        title = h4.get_text(strip=True)
                    else:
                        title = title_link.get_text(strip=True)
                    # Use the URL from title_link if available, otherwise use image link URL
                    url = title_link.get("href", url)
                else:
                    # Try finding h4 directly
                    h4 = container.find('h4')
                    if h4:
                        title = h4.get_text(strip=True)
                    else:
                        continue
            else:
                continue
            
            if title and url:
                processed_links.append((title, url))
        
        links = processed_links
    else:
        # Standard structure - links have text
        processed_links = []
        for link in links:
            title = link.get_text(strip=True)
            url = link.get("href")
            if title and url:
                processed_links.append((title, url))
        links = processed_links
    
    # If still no links found, try finding all article links manually
    if not links:
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filter for article links (has meaningful text, is article URL, not category/nav)
            if (text and len(text) > 10 and
                'marcusoscarsson.se' in href and
                href != 'https://marcusoscarsson.se' and
                not href.endswith('/sverige/') and
                not href.endswith('/ekonomi/') and
                not href.endswith('/varlden/') and
                not href.endswith('/usa/') and
                not href.endswith('/om/') and
                '/category/' not in href):
                links.append((text, href))

    # Process links (now they're tuples of (title, url) or link objects)
    for item in links:
        if isinstance(item, tuple):
            title, url = item
        else:
            title = item.get_text(strip=True)
            url = item.get("href")

        if not url or not title:
            continue

        # Normalize URL
        if not url.startswith("http"):
            url = BASE_URL + url
        
        # Remove trailing slash for consistency
        url = url.rstrip('/')
        
        # Skip if already seen
        if url in seen_urls:
            continue
        seen_urls.add(url)

        article = {
            "title_sv": title.strip(),
            "url": url
        }
        if category_name:
            article["category"] = category_name
        
        articles.append(article)

    return articles[:5]  # limit to latest 5 articles per category

def parse_article_page(url, summarizer=None):
    """
    Parse individual article page to extract content and generate summary.
    
    Args:
        url: Article URL to parse
        summarizer: SummaryGenerator instance (optional, uses default if not provided)
                    Follows Dependency Inversion Principle - accepts abstraction
        
    Returns:
        Dictionary with title, content, and summary
    """
    if summarizer is None:
        summarizer = _summarizer
    
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        # --- Title extraction ---
        # Read from <title> tag in <head> section
        title_elem = soup.find("title")
        title = None
        if title_elem:
            title = title_elem.get_text(strip=True)
            # If title contains " | " separator, extract the first part (before the separator)
            if " | " in title:
                title = title.split(" | ")[0].strip()

        # Content
        content_selectors = [
            ".post-content",
            ".entry-content",
            ".single-content",
            "article"
        ]

        content_text = ""
        for sel in content_selectors:
            container = soup.select_one(sel)
            if container:
                paragraphs = [p.get_text(strip=True) for p in container.find_all("p")]
                content_text = "\n".join(paragraphs)
                break

        # Clean content: remove common noise
        if content_text:
            import re
            # Remove date patterns like "2025 12 08" (standalone lines)
            content_text = re.sub(r'^\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\s*$', '', content_text, flags=re.MULTILINE)
            content_text = re.sub(r'\n\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\n', '\n', content_text)
            # Remove author bylines and metadata (common patterns)
            content_text = re.sub(r'^.*?(?:Text:|Foto:|Foto:|Bild:).*?$', '', content_text, flags=re.MULTILINE | re.IGNORECASE)
            # Remove "LÄS MER:" links and similar
            content_text = re.sub(r'LÄS MER:.*$', '', content_text, flags=re.MULTILINE | re.IGNORECASE)
            # Remove excessive newlines
            content_text = re.sub(r'\n{3,}', '\n\n', content_text)
            content_text = content_text.strip()

        # Generate summary using AI summarizer
        # Use 4 sentences for better context (can be adjusted)
        summary = ""
        if content_text and len(content_text) > 100:  # Only summarize if substantial content
            try:
                summary = summarizer.summarize(content_text, max_sentences=4)
            except ValueError as e:
                # API key or rate limit errors - log and continue without summary
                print(f"Warning: Could not generate summary: {e}")
                summary = ""
            except Exception as e:
                # Other errors - log and continue without summary
                print(f"Warning: Summary generation failed: {e}")
                summary = ""

        return {
            "title_sv": title,
            "summary_sv": summary
        }
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return {
            "title_sv": None,
            "summary_sv": ""
        }

def scrape_news():
    """
    Scrape articles from a list of URLs or categories.
    Supports both URL-based scraping (new) and category-based scraping (backward compatible).
    """
    all_articles = []
    
    # Fetch articles from each URL
    for url in SCRAPE_URLS:
        # Extract category/source name from URL for metadata
        if USE_URLS:
            # Extract name from URL (e.g., "sverige" from "https://marcusoscarsson.se/sverige/")
            url_parts = url.rstrip('/').split('/')
            source_name = url_parts[-1].capitalize() if url_parts else "News"
            print(f"Fetching articles from URL: {url}")
        else:
            # Legacy category-based: extract category name from URL
            source_name = url.split('/category/')[-1].rstrip('/').capitalize() if '/category/' in url else "News"
            print(f"Fetching articles from category: {source_name}")
        
        try:
            page_html = fetch_html(url)
            articles = parse_category_page(page_html, category_name=source_name)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            continue
    
    # Build metadata
    if USE_URLS:
        sources = [url.rstrip('/').split('/')[-1].capitalize() for url in SCRAPE_URLS]
    else:
        sources = [url.split('/category/')[-1].rstrip('/').capitalize() for url in SCRAPE_URLS if '/category/' in url]
    
    scraped_output = {
        "source": "marcusoscarsson.se",
        "sources": sources if sources else ["News"],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "articles": []
    }

    # Process each article
    for art in all_articles:
        print(f"Scraping article: {art['url']}")
        detail = parse_article_page(art["url"])

        merged = {
            **art,
            **detail,
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        scraped_output["articles"].append(merged)

    return scraped_output

# Keep backward compatibility alias
scrape_ekonomi = scrape_news

if __name__ == "__main__":
    data = scrape_news()
    print(json.dumps(data, indent=2, ensure_ascii=False))

