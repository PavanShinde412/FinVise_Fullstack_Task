

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import json
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()


class StockData(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    pct_change: float
    price_change: float
    day_high: float
    day_low: float
    week_52_high: float
    week_52_low: float
    volume: int
    market_cap: Optional[float] = 0
    pe_ratio: Optional[float] = 0
    sector: Optional[str] = "N/A"


class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str


class BriefRequest(BaseModel):
    stock_data: StockData
    news_articles: List[NewsArticle]


SYSTEM_PROMPT = """You are FinVise AI — a friendly financial educator who makes the stock market accessible to complete beginners. 
You write video scripts that are warm, clear, engaging, and free of jargon. 
Your audience has never invested before. Speak like a knowledgeable friend, not a textbook.
Always respond with valid JSON only — no markdown, no preamble."""


def build_user_prompt(stock: StockData, news: List[NewsArticle]) -> str:
    news_text = "\n".join([
        f"- [{a.source}] {a.title}: {a.summary[:200]}"
        for a in news[:5]
    ])

    market_cap_cr = f"₹{stock.market_cap / 1e7:.0f} Cr" if stock.market_cap else "N/A"
    direction = "up" if stock.pct_change >= 0 else "down"
    arrow = "📈" if stock.pct_change >= 0 else "📉"

    # 52-week position (how close to high/low)
    if stock.week_52_high > stock.week_52_low:
        pct_from_low = ((stock.current_price - stock.week_52_low) / (stock.week_52_high - stock.week_52_low)) * 100
        position_desc = f"{pct_from_low:.0f}% above its 52-week low"
    else:
        position_desc = "near its 52-week range"

    prompt = f"""
Generate a 90-second video brief script for {stock.company_name} ({stock.symbol}) in valid JSON format.

STOCK DATA:
- Current Price: ₹{stock.current_price}
- Today's Change: {direction} {abs(stock.pct_change)}% (₹{abs(stock.price_change)}) {arrow}
- Day Range: ₹{stock.day_low} – ₹{stock.day_high}
- 52-Week Range: ₹{stock.week_52_low} – ₹{stock.week_52_high}
- The stock is currently {position_desc}
- Volume: {stock.volume:,} shares traded
- Market Cap: {market_cap_cr}
- P/E Ratio: {stock.pe_ratio}
- Sector: {stock.sector}

RECENT NEWS:
{news_text}

OUTPUT FORMAT (return ONLY this JSON, nothing else):
{{
  "company_name": "{stock.company_name}",
  "symbol": "{stock.symbol}",
  "sections": {{
    "hook": {{
      "duration": "0-10 sec",
      "text": "A single punchy, attention-grabbing line. Make it specific to today's news or price move. Max 2 sentences."
    }},
    "stock_snapshot": {{
      "duration": "10-30 sec",
      "text": "Explain the current price, today's movement, and 52-week context in plain English. No jargon. Tell a story about where the stock is and where it's been. 3-4 sentences."
    }},
    "whats_happening": {{
      "duration": "30-60 sec",
      "text": "Describe 2-3 key news events or factors driving the stock right now. Explain what they mean in simple terms, like you're texting a friend. 4-5 sentences."
    }},
    "beginner_takeaway": {{
      "duration": "60-80 sec",
      "text": "What should a first-time investor understand about this stock right now? Be balanced — mention both opportunity and risk without recommending action. 3-4 sentences."
    }},
    "call_to_action": {{
      "duration": "80-90 sec",
      "text": "A neutral, educational closing line. Encourage learning and doing one's own research. 1-2 sentences."
    }}
  }},
  "full_script": "The complete script as one flowing paragraph (all sections combined), suitable for a single voiceover track.",
  "sentiment": "bullish|bearish|neutral",
  "key_points": ["point 1", "point 2", "point 3"],
  "disclaimer": "This is for educational purposes only and not financial advice."
}}
"""
    return prompt


async def call_groq(prompt: str) -> Optional[str]:
    """Call Groq API (llama-3.3-70b — fast & free)."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                    "response_format": {"type": "json_object"},
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"Groq error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Groq call failed: {e}")
    return None


async def call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API (free tier)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1500,
                        "responseMimeType": "application/json",
                    }
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.warning(f"Gemini error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
    return None


async def call_anthropic(prompt: str) -> Optional[str]:
    """Call Anthropic API as tertiary fallback."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1500,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["content"][0]["text"]
    except Exception as e:
        logger.warning(f"Anthropic call failed: {e}")
    return None


def generate_fallback_brief(stock: StockData, news: List[NewsArticle]) -> dict:
    """Generate a rule-based brief if all LLMs fail."""
    direction = "gained" if stock.pct_change >= 0 else "fallen"
    sentiment = "bullish" if stock.pct_change >= 0 else "bearish"
    top_news = news[0].title if news else "No recent news available"

    hook = f"{stock.company_name} shares are in focus today — {'up' if stock.pct_change >= 0 else 'down'} {abs(stock.pct_change):.1f}%!"
    snapshot = f"{stock.company_name} ({stock.symbol}) is currently trading at ₹{stock.current_price}, having {direction} ₹{abs(stock.price_change):.2f} or {abs(stock.pct_change):.1f}% today. The stock touched a high of ₹{stock.day_high} and a low of ₹{stock.day_low} during the day. Over the past year, it has ranged between ₹{stock.week_52_low} and ₹{stock.week_52_high}."
    whats_happening = f"In terms of recent developments, {top_news}. The stock is seeing {'above' if stock.volume > 1000000 else 'moderate'} trading volumes, which shows {'strong investor interest' if stock.volume > 1000000 else 'steady market activity'}."
    takeaway = f"For a first-time investor, {stock.company_name} is a {'large-cap' if (stock.market_cap or 0) > 1e12 else 'mid-cap'} company in the {stock.sector or 'Indian market'}. As with any stock, it's important to understand the business before investing. Today's {'gain' if stock.pct_change >= 0 else 'drop'} may be due to market-wide trends or company-specific news."
    cta = "Do your research, understand the company's fundamentals, and consider consulting a SEBI-registered advisor before making investment decisions."

    full_script = f"{hook} {snapshot} {whats_happening} {takeaway} {cta}"

    return {
        "company_name": stock.company_name,
        "symbol": stock.symbol,
        "sections": {
            "hook": {"duration": "0-10 sec", "text": hook},
            "stock_snapshot": {"duration": "10-30 sec", "text": snapshot},
            "whats_happening": {"duration": "30-60 sec", "text": whats_happening},
            "beginner_takeaway": {"duration": "60-80 sec", "text": takeaway},
            "call_to_action": {"duration": "80-90 sec", "text": cta},
        },
        "full_script": full_script,
        "sentiment": sentiment,
        "key_points": [
            f"Price {direction} {abs(stock.pct_change):.1f}% today",
            f"Trading at ₹{stock.current_price}",
            top_news[:100],
        ],
        "disclaimer": "This is for educational purposes only and not financial advice.",
        "source": "fallback",
    }


@router.post("/generate")
async def generate_brief(request: BriefRequest):
    """
    Generate an AI-powered 90-second video brief for a stock.
    Tries Groq → Gemini → Anthropic → Rule-based fallback.
    """
    prompt = build_user_prompt(request.stock_data, request.news_articles)

    # Try LLMs in order
    raw_response = None
    llm_used = None

    for llm_name, llm_fn in [("groq", call_groq), ("gemini", call_gemini), ("anthropic", call_anthropic)]:
        raw_response = await llm_fn(prompt)
        if raw_response:
            llm_used = llm_name
            break

    if raw_response:
        try:
            # Clean JSON if needed
            raw_response = raw_response.strip()
            if raw_response.startswith("```"):
                raw_response = re.sub(r"```[a-z]*\n?", "", raw_response).strip().rstrip("```").strip()
            brief = json.loads(raw_response)
            brief["llm_used"] = llm_used
            return brief
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error from {llm_used}: {e}")

    # Fallback to rule-based
    logger.info("All LLMs failed, using fallback brief generator")
    return generate_fallback_brief(request.stock_data, request.news_articles)
