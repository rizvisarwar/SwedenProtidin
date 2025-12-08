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
            "category": "ekonomi"
        }
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}")
        raise

config = load_config()
BASE_URL = config.get("base_url", "https://marcusoscarsson.se")
CATEGORY = config.get("category", "ekonomi")
CATEGORY_URL = f"{BASE_URL}/category/{CATEGORY}/"

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

def parse_category_page(html):
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

        articles.append({
            "title_sv": title,
            "url": url
        })

    return articles[:1]  # limit to latest 5 articles

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

        # Generate summary using AI summarizer
        summary = ""
        if content_text:
            summary = summarizer.summarize(content_text, max_sentences=3)

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

def scrape_ekonomi():
    category_html = fetch_html(CATEGORY_URL)
    articles = parse_category_page(category_html)

    scraped_output = {
        "source": "marcusoscarsson.se",
        "category": "Ekonomi",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "articles": []
    }

    for art in articles:
        print(f"Scraping article: {art['url']}")
        detail = parse_article_page(art["url"])

        merged = {
            **art,
            **detail,
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        scraped_output["articles"].append(merged)

    return scraped_output

if __name__ == "__main__":
    data = scrape_ekonomi()
    print(json.dumps(data, indent=2, ensure_ascii=False))
