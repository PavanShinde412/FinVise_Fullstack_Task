

from fastapi import APIRouter, HTTPException
import yfinance as yf
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.get("/{symbol}")
async def get_stock_data(symbol: str, exchange: Optional[str] = "NSE"):
    ticker_symbol = resolve_ticker(symbol)
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        if not info or info.get("regularMarketPrice") is None:
            bse_symbol = symbol.upper().replace(".NS", "") + ".BO"
            ticker = yf.Ticker(bse_symbol)
            info = ticker.info
            if not info or info.get("regularMarketPrice") is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stock '{symbol}' not found on NSE or BSE. Try using the exact ticker (e.g., RELIANCE, TCS, INFY)."
                )
            ticker_symbol = bse_symbol

        hist = ticker.history(period="1mo", interval="1d")
        chart_data = []
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

        current_price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose") or current_price
        price_change = round(current_price - prev_close, 2)
        pct_change = round((price_change / prev_close * 100) if prev_close else 0, 2)

        return {
            "symbol": symbol.upper(),
            "ticker": ticker_symbol,
            "company_name": info.get("longName") or info.get("shortName") or symbol.upper(),
            "exchange": "BSE" if ".BO" in ticker_symbol else "NSE",
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "current_price": round(current_price, 2),
            "previous_close": round(prev_close, 2),
            "price_change": price_change,
            "pct_change": pct_change,
            "open": round(info.get("regularMarketOpen") or info.get("open") or 0, 2),
            "day_high": round(info.get("dayHigh") or info.get("regularMarketDayHigh") or 0, 2),
            "day_low": round(info.get("dayLow") or info.get("regularMarketDayLow") or 0, 2),
            "volume": info.get("regularMarketVolume") or info.get("volume") or 0,
            "avg_volume": info.get("averageVolume") or 0,
            "week_52_high": round(info.get("fiftyTwoWeekHigh") or 0, 2),
            "week_52_low": round(info.get("fiftyTwoWeekLow") or 0, 2),
            "market_cap": info.get("marketCap") or 0,
            "pe_ratio": round(info.get("trailingPE") or 0, 2),
            "eps": round(info.get("trailingEps") or 0, 2),
            "dividend_yield": round((info.get("dividendYield") or 0) * 100, 2),
            "beta": round(info.get("beta") or 0, 2),
            "currency": info.get("currency", "INR"),
            "chart_data": chart_data[-30:] if chart_data else [],
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
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
