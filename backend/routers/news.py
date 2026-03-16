

from fastapi import APIRouter, HTTPException
import httpx
import feedparser
import asyncio
from typing import List, Optional
import logging
from datetime import datetime
import os
import re

logger = logging.getLogger(__name__)
router = APIRouter()

RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/rss.cms",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "livemint": "https://www.livemint.com/rss/markets",
    "zeebiz": "https://www.zeebiz.com/rss/market-news.xml",
}


def clean_html(text: str) -> str:
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text or '').strip()


def parse_rss_date(date_str: str) -> str:
    if not date_str:
        return datetime.now().isoformat()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str).isoformat()
    except Exception:
        return datetime.now().isoformat()


async def fetch_rss_news(company_name: str, symbol: str) -> List[dict]:
    articles = []
    search_terms = [symbol.upper(), company_name.upper()]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for source, url in RSS_FEEDS.items():
            try:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:30]:
                        title = entry.get("title", "")
                        summary = clean_html(entry.get("summary", "") or entry.get("description", ""))
                        link = entry.get("link", "")
                        published = parse_rss_date(entry.get("published", ""))

                        # Filter for relevant articles
                        combined = (title + " " + summary).upper()
                        is_relevant = any(term in combined for term in search_terms)
                        # Also include general market news if fewer results
                        is_market_news = any(kw in combined for kw in ["NIFTY", "SENSEX", "MARKET", "STOCK", "SHARE", "EQUITY"])

                        if is_relevant or (is_market_news and len(articles) < 5):
                            articles.append({
                                "title": title,
                                "summary": summary[:500] if summary else title,
                                "url": link,
                                "source": source.replace("_", " ").title(),
                                "published_at": published,
                                "relevant": is_relevant,
                            })
            except Exception as e:
                logger.warning(f"RSS feed {source} failed: {e}")
                continue

    # Sort: relevant first, then by date
    articles.sort(key=lambda x: (not x["relevant"], x["published_at"]), reverse=False)
    return articles[:15]


async def fetch_newsapi(query: str, symbol: str) -> List[dict]:
    """Fetch news from NewsAPI (free tier)."""
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": f"{query} OR {symbol} stock India",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                    "apiKey": api_key,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                articles = []
                for a in data.get("articles", []):
                    articles.append({
                        "title": a.get("title", ""),
                        "summary": a.get("description", "") or a.get("title", ""),
                        "url": a.get("url", ""),
                        "source": a.get("source", {}).get("name", "NewsAPI"),
                        "published_at": a.get("publishedAt", datetime.now().isoformat()),
                        "relevant": True,
                    })
                return articles
    except Exception as e:
        logger.warning(f"NewsAPI failed: {e}")
    return []


async def fetch_gnews(query: str, symbol: str) -> List[dict]:
    """Fetch news from GNews API (free tier - 100 requests/day)."""
    api_key = os.getenv("GNEWS_KEY", "")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://gnews.io/api/v4/search",
                params={
                    "q": f"{query} stock NSE India",
                    "lang": "en",
                    "country": "in",
                    "max": 10,
                    "apikey": api_key,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                articles = []
                for a in data.get("articles", []):
                    articles.append({
                        "title": a.get("title", ""),
                        "summary": a.get("description", "") or a.get("title", ""),
                        "url": a.get("url", ""),
                        "source": a.get("source", {}).get("name", "GNews"),
                        "published_at": a.get("publishedAt", datetime.now().isoformat()),
                        "relevant": True,
                    })
                return articles
    except Exception as e:
        logger.warning(f"GNews failed: {e}")
    return []


@router.get("/{symbol}")
async def get_stock_news(symbol: str, company_name: Optional[str] = None):
    """
    Fetch recent news for a stock from multiple sources.
    Falls back gracefully if any source fails.
    """
    company = company_name or symbol.upper()

    # Run all sources in parallel
    rss_task = fetch_rss_news(company, symbol)
    newsapi_task = fetch_newsapi(company, symbol)
    gnews_task = fetch_gnews(company, symbol)

    results = await asyncio.gather(rss_task, newsapi_task, gnews_task, return_exceptions=True)

    all_articles = []
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        title_key = a["title"][:60].lower().strip()
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(a)

    # Sort relevant first
    unique_articles.sort(key=lambda x: (not x.get("relevant", False), x.get("published_at", "")), reverse=True)

    if not unique_articles:
        # Return a placeholder if no news found
        unique_articles = [{
            "title": f"No recent news found for {symbol.upper()}",
            "summary": "No recent news articles could be fetched at this time. The AI brief will be generated based on available stock data.",
            "url": "",
            "source": "System",
            "published_at": datetime.now().isoformat(),
            "relevant": True,
        }]

    return {
        "symbol": symbol.upper(),
        "articles": unique_articles[:10],
        "total": len(unique_articles),
        "timestamp": datetime.now().isoformat(),
    }
