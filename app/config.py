import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"

WATCHLIST_PATH = CONFIG_DIR / "watchlist.yaml"
HOLDINGS_PATH = CONFIG_DIR / "holdings.json"
STATE_PATH = DATA_DIR / "state.json"

MARKET_TIMEZONE = "Europe/Istanbul"
MARKET_OPEN_HOUR = 10
MARKET_CLOSE_HOUR = 18

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def load_watchlist():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["tickers"], cfg["thresholds"]
