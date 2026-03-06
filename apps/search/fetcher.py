"""
Shamela fetcher: fetches book metadata and text from shamela.ws.
Uses ethical rate-limiting and Django cache to avoid hammering the server.
"""
import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "SHAMELA_BASE_URL", "https://shamela.ws")
CACHE_TTL = getattr(settings, "SHAMELA_FETCH_CACHE_SECONDS", 3600)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8,en;q=0.7",
}

def _fetch_url(url: str) -> Optional[str]:
    """Fetch a URL with caching and polite delay."""
    cache_key = f"shamela_html_{url}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        time.sleep(1)  # polite 1-second delay
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
        cache.set(cache_key, html, CACHE_TTL)
        return html
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def search_shamela_books(query: str, limit: int = 10) -> list[dict]:
    """
    Search shamela.ws for books matching `query`.
    Returns list of dicts with keys: shamela_id, title, author, subject, url.
    """
    search_url = f"{BASE_URL}/search?q={requests.utils.quote(query)}"
    html = _fetch_url(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []

    # shamela.ws search results container (may change with site updates)
    for card in soup.select(".book-card, .search-result, .book-item")[:limit]:
        try:
            title_el = card.select_one(".book-title, h3, h2, .title")
            author_el = card.select_one(".author, .book-author")
            link_el = card.select_one("a[href]")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            # Extract shamela_id from URL (e.g. /book/1234 → 1234)
            shamela_id = href.rstrip("/").split("/")[-1]

            results.append({
                "shamela_id": shamela_id,
                "title": title_el.get_text(strip=True),
                "author": author_el.get_text(strip=True) if author_el else "",
                "subject": "",
                "url": href,
            })
        except Exception as e:
            logger.warning(f"Error parsing search result: {e}")
            continue

    return results


def fetch_book_text(shamela_id: str, page: int = 1) -> Optional[str]:
    """
    Fetch the text content of a specific book page from shamela.ws.
    Returns plain text or None on failure.
    """
    url = f"{BASE_URL}/book/{shamela_id}/{page}"
    html = _fetch_url(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    # Try to find main text content
    content_el = soup.select_one(".book-content, .text-content, article, .nass, #bookContent")
    if content_el:
        # Remove navigation, footnotes
        for tag in content_el.select("nav, .footnote, script, style"):
            tag.decompose()
        return content_el.get_text(separator="\n", strip=True)

    # Fallback: grab largest <div> or <p> blocks
    paragraphs = soup.find_all("p")
    if paragraphs:
        return "\n".join(p.get_text(strip=True) for p in paragraphs[:50])

    return None


def fetch_book_metadata(shamela_id: str) -> Optional[dict]:
    """Fetch metadata for a book by its shamela ID."""
    url = f"{BASE_URL}/book/{shamela_id}"
    html = _fetch_url(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("h1.book-title, h1, title")
    author_el = soup.select_one(".author, .book-author, [itemprop='author']")
    subject_el = soup.select_one(".category, .subject, .book-category")
    desc_el = soup.select_one(".description, .book-description, [itemprop='description']")

    return {
        "shamela_id": shamela_id,
        "title": title_el.get_text(strip=True) if title_el else f"Livre #{shamela_id}",
        "author": author_el.get_text(strip=True) if author_el else "",
        "subject": subject_el.get_text(strip=True) if subject_el else "",
        "description": desc_el.get_text(strip=True) if desc_el else "",
        "shamela_url": url,
    }
