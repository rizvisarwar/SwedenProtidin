import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import json

BASE_URL = "https://marcusoscarsson.se"
CATEGORY_URL = f"{BASE_URL}/category/ekonomi/"

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

def parse_article_page(url):
    """Parse individual article page to extract content."""
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else None

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

        return {
            "title_sv": title,
            "content_sv": content_text
        }
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return {
            "title_sv": None,
            "content_sv": "",
            "image": None
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
