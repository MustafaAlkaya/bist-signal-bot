import pandas as pd


def _macd_cross_vote(df: pd.DataFrame, lookback: int = 2) -> int:
    """+1 if MACD crossed above signal within the last `lookback` bars, -1 if crossed below, else 0."""
    tail = df.iloc[-(lookback + 1):]
    diff = tail["macd"] - tail["macd_signal"]
    if len(diff) < 2:
        return 0
    for i in range(1, len(diff)):
        if diff.iloc[i - 1] <= 0 and diff.iloc[i] > 0:
            return 1
        if diff.iloc[i - 1] >= 0 and diff.iloc[i] < 0:
            return -1
    return 0


REQUIRED_FIELDS = ["rsi", "macd", "macd_signal", "sma_fast", "sma_slow",
                    "bb_upper", "bb_lower", "Close"]


def evaluate_ticker(df: pd.DataFrame, thresholds: dict) -> dict | None:
    """Compute the vote-based signal for the latest row of an indicator-enriched df.

    Returns None if the latest row is missing required indicator values
    (e.g. a data gap), so the caller can skip the ticker for this run.
    """
    last = df.iloc[-1]
    if last[REQUIRED_FIELDS].isna().any():
        return None

    votes = 0
    if last["rsi"] < thresholds["rsi_oversold"]:
        votes += 1
    elif last["rsi"] > thresholds["rsi_overbought"]:
        votes -= 1

    votes += _macd_cross_vote(df)

    if last["sma_fast"] > last["sma_slow"]:
        votes += 1
    elif last["sma_fast"] < last["sma_slow"]:
        votes -= 1

    if last["Close"] <= last["bb_lower"]:
        votes += 1
    elif last["Close"] >= last["bb_upper"]:
        votes -= 1

    if votes >= thresholds["buy_score"]:
        signal = "BUY"
    elif votes <= thresholds["sell_score"]:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "score": int(votes),
        "rsi": round(float(last["rsi"]), 2),
        "macd": round(float(last["macd"]), 4),
        "macd_signal": round(float(last["macd_signal"]), 4),
        "sma_fast": round(float(last["sma_fast"]), 2),
        "sma_slow": round(float(last["sma_slow"]), 2),
        "bb_upper": round(float(last["bb_upper"]), 2),
        "bb_lower": round(float(last["bb_lower"]), 2),
        "last_close": round(float(last["Close"]), 2),
    }
