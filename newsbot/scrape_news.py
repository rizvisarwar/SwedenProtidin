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
            "categories": ["ekonomi", "sverige"]
        }
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}")
        raise

config = load_config()
BASE_URL = config.get("base_url", "https://marcusoscarsson.se")
# Support both old "category" (single) and new "categories" (list) for backward compatibility
if "categories" in config:
    CATEGORIES = config["categories"]
elif "category" in config:
    CATEGORIES = [config["category"]]
else:
    CATEGORIES = ["ekonomi"]  # default fallback

# Initialize summarizer (Dependency Injection - follows SOLID principles)
# Use ISO 639-1 language code 'sv' for Swedish
_summarizer = create_summarizer("sumy", language="sv")

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

    # Try several possible selectors
    selectors = [
        "article h2 a",
        "h2.entry-title a",
        ".post h2 a",
        ".post-title a",
        "h2 a"
    ]

    links = []
    for sel in selectors:
        found = soup.select(sel)
        if found:
            links = found
            break

    for link in links:
        title = link.get_text(strip=True)
        url = link.get("href")

        if not url:
            continue

        if not url.startswith("http"):
            url = BASE_URL + url

        article = {
            "title_sv": title,
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
            summary = summarizer.summarize(content_text, max_sentences=4)

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
    Scrape articles from multiple categories (Ekonomi and Sverige).
    Combines articles from all configured categories.
    """
    all_articles = []
    
    # Fetch articles from each category
    for category in CATEGORIES:
        category_url = f"{BASE_URL}/category/{category}/"
        print(f"Fetching articles from category: {category}")
        
        try:
            category_html = fetch_html(category_url)
            articles = parse_category_page(category_html, category_name=category.capitalize())
            all_articles.extend(articles)
        except Exception as e:
            print(f"Error fetching category {category}: {e}")
            continue
    
    # Determine category display name(s)
    if len(CATEGORIES) == 1:
        category_display = CATEGORIES[0].capitalize()
    else:
        category_display = ", ".join(c.capitalize() for c in CATEGORIES)
    
    scraped_output = {
        "source": "marcusoscarsson.se",
        "categories": [c.capitalize() for c in CATEGORIES],
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

