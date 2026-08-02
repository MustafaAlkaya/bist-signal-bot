import json

from .config import HOLDINGS_PATH


def load_holdings() -> dict:
    """Load {ticker: {shares, avg_cost}}, ignoring example/comment keys starting with '_'."""
    if not HOLDINGS_PATH.exists():
        return {}
    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def annotate(ticker: str, result: dict, holdings: dict) -> dict:
    """Attach 'held' and profit/loss info to a signal result dict if the ticker is owned."""
    position = holdings.get(ticker)
    result["held"] = position is not None
    if position:
        avg_cost = position["avg_cost"]
        result["shares"] = position["shares"]
        result["avg_cost"] = avg_cost
        result["pnl_pct"] = round((result["last_close"] - avg_cost) / avg_cost * 100, 2)
    return result
