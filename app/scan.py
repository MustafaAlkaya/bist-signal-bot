import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from . import data_fetch, notify, portfolio, state as state_mod
from .config import MARKET_CLOSE_HOUR, MARKET_OPEN_HOUR, MARKET_TIMEZONE, load_watchlist
from .indicators import compute_indicators
from .signals import evaluate_ticker

# Windows konsollarında dar kod sayfaları (örn. cp1254) emoji/ok gibi
# karakterlerde UnicodeEncodeError verebilir; bunu önlemek için UTF-8'e zorla.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def is_market_hours(now=None) -> bool:
    now = now or datetime.now(ZoneInfo(MARKET_TIMEZONE))
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    return MARKET_OPEN_HOUR <= now.hour < MARKET_CLOSE_HOUR


def run(tickers=None, dry_run=False, ignore_market_hours=False):
    if not ignore_market_hours and not is_market_hours():
        logger.info("Outside BIST trading hours, exiting without action.")
        return

    all_tickers, thresholds = load_watchlist()
    tickers = tickers or all_tickers
    holdings = portfolio.load_holdings()

    logger.info("Fetching data for %d tickers...", len(tickers))
    history = data_fetch.fetch_history(tickers)

    prev_state = state_mod.load_state()
    transitions = []

    for ticker, df in history.items():
        try:
            enriched = compute_indicators(df, thresholds)
            result = evaluate_ticker(enriched, thresholds)
        except Exception as exc:
            logger.warning("Failed to evaluate %s: %s", ticker, exc)
            continue
        if result is None:
            continue

        result = portfolio.annotate(ticker, result, holdings)
        transition = state_mod.diff_and_update(prev_state, ticker, result)

        if transition and not (transition["to"] == "BUY" and result["held"]):
            transitions.append({
                "ticker": ticker,
                "from": transition["from"],
                "to": transition["to"],
                "held": result["held"],
                "pnl_pct": result.get("pnl_pct"),
            })

    logger.info("Evaluated %d tickers, %d signal transitions.", len(history), len(transitions))

    if dry_run:
        for ticker, result in prev_state.items():
            print(ticker, result.get("signal"), result.get("score"))
        print("--- transitions ---")
        for t in transitions:
            print(t)
        return

    if transitions:
        notify.send_message(notify.format_digest(transitions))

    state_mod.save_state(prev_state)


def main():
    parser = argparse.ArgumentParser(description="BIST sinyal tarayıcısı")
    parser.add_argument("--tickers", help="Virgülle ayrılmış hisse listesi (örn. THYAO.IS,ASELS.IS)")
    parser.add_argument("--dry-run", action="store_true", help="Telegram/commit atla, sonucu yazdır")
    parser.add_argument("--ignore-market-hours", action="store_true",
                         help="Piyasa saati kontrolünü atla (test için)")
    args = parser.parse_args()

    tickers = args.tickers.split(",") if args.tickers else None

    try:
        run(tickers=tickers, dry_run=args.dry_run, ignore_market_hours=args.ignore_market_hours)
    except Exception:
        logger.exception("Scan failed")
        if not args.dry_run:
            notify.send_message("⚠️ BIST tarama görevi hata verdi, loglara bakın.")
        sys.exit(1)


if __name__ == "__main__":
    main()
