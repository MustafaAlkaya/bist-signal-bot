import pandas as pd

# Bağımsız (pandas-ta'sız) indikatör hesaplamaları.
# pandas-ta paketi PyPI'dan kaldırıldığı için standart formüller doğrudan uygulanır.


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, fast: int, slow: int, signal: int):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def _bbands(close: pd.Series, length: int, std: float):
    mid = close.rolling(window=length).mean()
    dev = close.rolling(window=length).std(ddof=0)
    upper = mid + std * dev
    lower = mid - std * dev
    return lower, upper


def compute_indicators(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Append RSI, MACD, SMA fast/slow, and Bollinger Bands columns to df."""
    out = df.copy()
    close = out["Close"]

    out["rsi"] = _rsi(close, length=14)

    macd_line, signal_line = _macd(
        close,
        fast=thresholds["macd_fast"],
        slow=thresholds["macd_slow"],
        signal=thresholds["macd_signal"],
    )
    out["macd"] = macd_line
    out["macd_signal"] = signal_line

    out["sma_fast"] = close.rolling(window=thresholds["sma_fast"]).mean()
    out["sma_slow"] = close.rolling(window=thresholds["sma_slow"]).mean()

    bb_lower, bb_upper = _bbands(close, thresholds["bbands_length"], thresholds["bbands_std"])
    out["bb_lower"] = bb_lower
    out["bb_upper"] = bb_upper

    return out
