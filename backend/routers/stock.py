from fastapi import APIRouter, HTTPException
import yfinance as yf
import httpx
import requests
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Origin": "https://www.nseindia.com",
}


def resolve_ticker(symbol: str) -> str:
    symbol = symbol.upper().strip()
    symbol = symbol.replace(".NS", "").replace(".BO", "").replace(".BSE", "")
    index_map = {
        "NIFTY50": "^NSEI",
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
    }
    if symbol in index_map:
        return index_map[symbol]
    return symbol


async def fetch_from_nse(symbol: str) -> Optional[dict]:
    """Fetch stock data from NSE India public API."""
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        async with httpx.AsyncClient(headers=HEADERS, timeout=10, follow_redirects=True) as client:
            await client.get("https://www.nseindia.com", timeout=10)
            resp = await client.get(url, timeout=10)
            if resp.status_code != 200:
                return None
            data = resp.json()
            pd_info = data.get("priceInfo", {})
            md = data.get("metadata", {})
            info = data.get("info", {})

            current_price = pd_info.get("lastPrice") or pd_info.get("close") or 0
            prev_close = pd_info.get("previousClose") or current_price
            if not current_price:
                return None

            price_change = round(float(current_price) - float(prev_close), 2)
            pct_change = round((price_change / float(prev_close) * 100) if prev_close else 0, 2)

            return {
                "symbol": symbol,
                "ticker": f"{symbol}.NS",
                "company_name": info.get("companyName") or md.get("companyName") or symbol,
                "exchange": "NSE",
                "sector": info.get("industry") or "N/A",
                "industry": info.get("industry") or "N/A",
                "current_price": round(float(current_price), 2),
                "previous_close": round(float(prev_close), 2),
                "price_change": price_change,
                "pct_change": pct_change,
                "open": round(float(pd_info.get("open") or 0), 2),
                "day_high": round(float((pd_info.get("intraDayHighLow") or {}).get("max") or pd_info.get("high") or 0), 2),
                "day_low": round(float((pd_info.get("intraDayHighLow") or {}).get("min") or pd_info.get("low") or 0), 2),
                "volume": int(md.get("totalTradedVolume") or 0),
                "avg_volume": 0,
                "week_52_high": round(float((pd_info.get("weekHighLow") or {}).get("max") or 0), 2),
                "week_52_low": round(float((pd_info.get("weekHighLow") or {}).get("min") or 0), 2),
                "market_cap": 0,
                "pe_ratio": 0,
                "eps": 0,
                "dividend_yield": 0,
                "beta": 0,
                "currency": "INR",
                "chart_data": [],
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.warning(f"NSE API failed for {symbol}: {e}")
        return None


async def fetch_from_stooq(symbol: str) -> Optional[dict]:
    """Fetch from Stooq — no API key, no IP restrictions."""
    try:
        stooq_symbol = f"{symbol}.IN"
        url = f"https://stooq.com/q/l/?s={stooq_symbol}&f=sd2t2ohlcvn&h&e=json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            symbols = data.get("symbols", [])
            if not symbols:
                return None
            s = symbols[0]
            current_price = float(s.get("Close") or s.get("Last") or 0)
            if current_price == 0:
                return None

            open_price = float(s.get("Open") or current_price)
            high = float(s.get("High") or current_price)
            low = float(s.get("Low") or current_price)
            volume = int(float(s.get("Volume") or 0))
            prev_close = open_price
            price_change = round(current_price - prev_close, 2)
            pct_change = round((price_change / prev_close * 100) if prev_close else 0, 2)

            return {
                "symbol": symbol,
                "ticker": f"{symbol}.NS",
                "company_name": s.get("Name") or symbol,
                "exchange": "NSE",
                "sector": "N/A",
                "industry": "N/A",
                "current_price": round(current_price, 2),
                "previous_close": round(prev_close, 2),
                "price_change": price_change,
                "pct_change": pct_change,
                "open": round(open_price, 2),
                "day_high": round(high, 2),
                "day_low": round(low, 2),
                "volume": volume,
                "avg_volume": 0,
                "week_52_high": 0,
                "week_52_low": 0,
                "market_cap": 0,
                "pe_ratio": 0,
                "eps": 0,
                "dividend_yield": 0,
                "beta": 0,
                "currency": "INR",
                "chart_data": [],
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.warning(f"Stooq failed for {symbol}: {e}")
        return None


async def fetch_from_yfinance(symbol: str) -> Optional[dict]:
    """yfinance with session headers."""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.yahoo.com/",
        })

        for suffix in [".NS", ".BO"]:
            ticker_symbol = symbol + suffix
            try:
                ticker = yf.Ticker(ticker_symbol, session=session)
                fi = ticker.fast_info
                price = getattr(fi, "last_price", None) or getattr(fi, "previous_close", None)
                if not price or float(price) <= 0:
                    continue

                prev_close = float(getattr(fi, "previous_close", price) or price)
                current_price = float(price)
                price_change = round(current_price - prev_close, 2)
                pct_change = round((price_change / prev_close * 100) if prev_close else 0, 2)

                chart_data = []
                try:
                    hist = ticker.history(period="1mo", interval="1d")
                    if not hist.empty:
                        for date, row in hist.iterrows():
                            chart_data.append({
                                "date": date.strftime("%Y-%m-%d"),
                                "open": round(float(row["Open"]), 2),
                                "high": round(float(row["High"]), 2),
                                "low": round(float(row["Low"]), 2),
                                "close": round(float(row["Close"]), 2),
                                "volume": int(row["Volume"]),
                            })
                except Exception:
                    pass

                company_name = symbol
                sector = "N/A"
                market_cap = 0
                pe_ratio = 0
                week_52_high = round(float(getattr(fi, "year_high", 0) or 0), 2)
                week_52_low = round(float(getattr(fi, "year_low", 0) or 0), 2)
                try:
                    info = ticker.info
                    if info and isinstance(info, dict):
                        company_name = info.get("longName") or info.get("shortName") or symbol
                        sector = info.get("sector") or "N/A"
                        market_cap = int(info.get("marketCap") or 0)
                        pe_ratio = round(float(info.get("trailingPE") or 0), 2)
                except Exception:
                    pass

                return {
                    "symbol": symbol,
                    "ticker": ticker_symbol,
                    "company_name": company_name,
                    "exchange": "BSE" if suffix == ".BO" else "NSE",
                    "sector": sector,
                    "industry": "N/A",
                    "current_price": round(current_price, 2),
                    "previous_close": round(prev_close, 2),
                    "price_change": price_change,
                    "pct_change": pct_change,
                    "open": round(float(getattr(fi, "open", 0) or 0), 2),
                    "day_high": round(float(getattr(fi, "day_high", 0) or 0), 2),
                    "day_low": round(float(getattr(fi, "day_low", 0) or 0), 2),
                    "volume": int(getattr(fi, "last_volume", 0) or 0),
                    "avg_volume": 0,
                    "week_52_high": week_52_high,
                    "week_52_low": week_52_low,
                    "market_cap": market_cap,
                    "pe_ratio": pe_ratio,
                    "eps": 0,
                    "dividend_yield": 0,
                    "beta": 0,
                    "currency": "INR",
                    "chart_data": chart_data[-30:],
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception:
                continue
        return None
    except Exception as e:
        logger.warning(f"yfinance failed for {symbol}: {e}")
        return None


@router.get("/{symbol}")
async def get_stock_data(symbol: str, exchange: Optional[str] = "NSE"):
    clean_symbol = resolve_ticker(symbol)

    # Try 3 sources in order: NSE → Stooq → yfinance
    result = await fetch_from_nse(clean_symbol)

    if not result:
        logger.info(f"NSE failed for {clean_symbol}, trying Stooq...")
        result = await fetch_from_stooq(clean_symbol)

    if not result:
        logger.info(f"Stooq failed for {clean_symbol}, trying yfinance...")
        result = await fetch_from_yfinance(clean_symbol)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found. Please use the exact NSE ticker (e.g., RELIANCE, TCS, HDFCBANK, INFY)."
        )

    return result


@router.get("/{symbol}/summary")
async def get_stock_summary(symbol: str):
    """Get key stock metrics for LLM consumption."""
    data = await get_stock_data(symbol)
    return {
        "symbol": data["symbol"],
        "company_name": data["company_name"],
        "current_price": data["current_price"],
        "pct_change": data["pct_change"],
        "price_change": data["price_change"],
        "day_high": data["day_high"],
        "day_low": data["day_low"],
        "week_52_high": data["week_52_high"],
        "week_52_low": data["week_52_low"],
        "volume": data["volume"],
        "market_cap": data["market_cap"],
        "pe_ratio": data["pe_ratio"],
        "sector": data["sector"],
    }