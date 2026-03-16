from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


def make_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://finance.yahoo.com/",
    })
    return session


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
    return f"{symbol}.NS"


def fetch_ticker_data(ticker_symbol: str):
    """Try to fetch info using .info first, fall back to fast_info if empty."""
    session = make_session()
    ticker = yf.Ticker(ticker_symbol, session=session)

    # Try fast_info first — more reliable on cloud servers
    try:
        fi = ticker.fast_info
        price = getattr(fi, "last_price", None) or getattr(fi, "previous_close", None)
        if price and price > 0:
            # Build a info-like dict from fast_info
            info = {
                "regularMarketPrice": round(float(price), 2),
                "currentPrice": round(float(price), 2),
                "regularMarketPreviousClose": round(float(getattr(fi, "previous_close", price) or price), 2),
                "previousClose": round(float(getattr(fi, "previous_close", price) or price), 2),
                "regularMarketOpen": round(float(getattr(fi, "open", 0) or 0), 2),
                "dayHigh": round(float(getattr(fi, "day_high", 0) or 0), 2),
                "dayLow": round(float(getattr(fi, "day_low", 0) or 0), 2),
                "regularMarketVolume": int(getattr(fi, "last_volume", 0) or 0),
                "fiftyTwoWeekHigh": round(float(getattr(fi, "year_high", 0) or 0), 2),
                "fiftyTwoWeekLow": round(float(getattr(fi, "year_low", 0) or 0), 2),
                "marketCap": int(getattr(fi, "market_cap", 0) or 0),
                "currency": getattr(fi, "currency", "INR") or "INR",
                "longName": None,
                "shortName": None,
                "sector": "N/A",
                "industry": "N/A",
                "trailingPE": 0,
                "trailingEps": 0,
                "dividendYield": 0,
                "beta": 0,
                "averageVolume": 0,
            }

            # Try to enrich with .info (best effort, don't fail if it errors)
            try:
                full_info = ticker.info
                if full_info and isinstance(full_info, dict) and full_info.get("regularMarketPrice"):
                    info.update(full_info)
            except Exception:
                pass

            return ticker, info

    except Exception as e:
        logger.warning(f"fast_info failed for {ticker_symbol}: {e}")

    # Fall back to .info directly
    try:
        info = ticker.info
        if info and isinstance(info, dict) and (
            info.get("regularMarketPrice") or info.get("currentPrice")
        ):
            return ticker, info
    except Exception as e:
        logger.warning(f".info failed for {ticker_symbol}: {e}")

    return ticker, None


@router.get("/{symbol}")
async def get_stock_data(symbol: str, exchange: Optional[str] = "NSE"):
    ticker_symbol = resolve_ticker(symbol)

    try:
        ticker, info = fetch_ticker_data(ticker_symbol)

        # If NSE fails, try BSE
        if not info:
            bse_symbol = symbol.upper().replace(".NS", "").replace(".BO", "") + ".BO"
            logger.info(f"NSE failed, trying BSE: {bse_symbol}")
            ticker, info = fetch_ticker_data(bse_symbol)
            if info:
                ticker_symbol = bse_symbol

        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Stock '{symbol}' not found on NSE or BSE. Try the exact ticker (e.g., RELIANCE, TCS, INFY)."
            )

        # Fetch chart data
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
        except Exception as e:
            logger.warning(f"Chart data fetch failed for {ticker_symbol}: {e}")

        current_price = (
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or (chart_data[-1]["close"] if chart_data else 0)
        )
        prev_close = (
            info.get("regularMarketPreviousClose")
            or info.get("previousClose")
            or current_price
        )
        price_change = round(float(current_price) - float(prev_close), 2)
        pct_change = round((price_change / float(prev_close) * 100) if prev_close else 0, 2)

        return {
            "symbol": symbol.upper(),
            "ticker": ticker_symbol,
            "company_name": (
                info.get("longName") or info.get("shortName") or symbol.upper()
            ),
            "exchange": "BSE" if ".BO" in ticker_symbol else "NSE",
            "sector": info.get("sector") or "N/A",
            "industry": info.get("industry") or "N/A",
            "current_price": round(float(current_price), 2),
            "previous_close": round(float(prev_close), 2),
            "price_change": price_change,
            "pct_change": pct_change,
            "open": round(float(info.get("regularMarketOpen") or info.get("open") or 0), 2),
            "day_high": round(float(info.get("dayHigh") or info.get("regularMarketDayHigh") or 0), 2),
            "day_low": round(float(info.get("dayLow") or info.get("regularMarketDayLow") or 0), 2),
            "volume": int(info.get("regularMarketVolume") or info.get("volume") or 0),
            "avg_volume": int(info.get("averageVolume") or 0),
            "week_52_high": round(float(info.get("fiftyTwoWeekHigh") or 0), 2),
            "week_52_low": round(float(info.get("fiftyTwoWeekLow") or 0), 2),
            "market_cap": int(info.get("marketCap") or 0),
            "pe_ratio": round(float(info.get("trailingPE") or 0), 2),
            "eps": round(float(info.get("trailingEps") or 0), 2),
            "dividend_yield": round(float(info.get("dividendYield") or 0) * 100, 2),
            "beta": round(float(info.get("beta") or 0), 2),
            "currency": info.get("currency") or "INR",
            "chart_data": chart_data[-30:] if chart_data else [],
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock data: {str(e)}"
        )


@router.get("/{symbol}/summary")
async def get_stock_summary(symbol: str):
    """Get a brief summary of key stock metrics for LLM consumption."""
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