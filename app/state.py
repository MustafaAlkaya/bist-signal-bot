import json
from datetime import datetime, timezone

from .config import STATE_PATH


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def diff_and_update(previous: dict, ticker: str, result: dict) -> dict | None:
    """Update `previous` in place with `result` for `ticker`.

    Returns a transition dict {"from": ..., "to": ...} if the signal changed
    since the last run, else None (signal unchanged, no notification needed).
    """
    prior_signal = previous.get(ticker, {}).get("signal")
    new_signal = result["signal"]

    result = dict(result)
    result["last_changed"] = (
        datetime.now(timezone.utc).isoformat()
        if prior_signal != new_signal
        else previous.get(ticker, {}).get("last_changed", datetime.now(timezone.utc).isoformat())
    )
    previous[ticker] = result

    if prior_signal is not None and prior_signal != new_signal:
        return {"from": prior_signal, "to": new_signal}
    return None
