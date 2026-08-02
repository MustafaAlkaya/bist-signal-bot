import logging
import random
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

BATCH_SIZE = 20
MIN_ROWS = 60


def fetch_history(tickers, period="1y", interval="1d"):
    """Fetch OHLCV history for all tickers, batched to avoid Yahoo throttling.

    Returns a dict {ticker: DataFrame}. Tickers with insufficient/missing data
    are skipped (logged), never raising for the whole batch.
    """
    result = {}
    batches = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]

    for batch in batches:
        try:
            raw = yf.download(
                tickers=batch,
                period=period,
                interval=interval,
                group_by="ticker",
                threads=True,
                auto_adjust=True,
                progress=False,
            )
        except Exception as exc:
            logger.warning("Batch fetch failed for %s: %s", batch, exc)
            raw = None

        for ticker in batch:
            df = _extract_ticker_frame(raw, ticker)
            if df is None or len(df) < MIN_ROWS:
                logger.warning("Skipping %s: insufficient data (%s rows)",
                               ticker, 0 if df is None else len(df))
                continue
            result[ticker] = df

        time.sleep(random.uniform(0.5, 1.5))

    return result


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully-empty rows and any row with a missing Close (e.g. today's
    still-in-progress bar, which yfinance sometimes includes with only Volume set)."""
    df = df.dropna(how="all")
    if "Close" in df.columns:
        df = df[df["Close"].notna()]
    return df


def _extract_ticker_frame(raw, ticker):
    if raw is None or raw.empty:
        return None
    try:
        df = raw[ticker] if isinstance(raw.columns, pd.MultiIndex) else raw
        df = _clean(df)
        return df if not df.empty else None
    except Exception:
        return None


def fetch_single(ticker, period="1y", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                          auto_adjust=True, progress=False)
        df = _clean(df)
        return df if not df.empty else None
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", ticker, exc)
        return None
