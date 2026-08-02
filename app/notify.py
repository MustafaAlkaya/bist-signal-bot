import logging

import requests

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram token/chat_id not configured; skipping send.")
        return False
    try:
        resp = requests.post(
            API_URL.format(token=TELEGRAM_BOT_TOKEN),
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


def format_digest(transitions: list[dict]) -> str:
    """transitions: list of {"ticker", "from", "to", "held", "pnl_pct"(optional)}"""
    lines = ["*BIST Sinyal Güncellemesi*"]
    for t in transitions:
        arrow = f"{t['from']} → {t['to']}"
        line = f"• `{t['ticker']}`  {arrow}"
        if t.get("held"):
            pnl = t.get("pnl_pct")
            pnl_str = f" (K/Z: {pnl:+.2f}%)" if pnl is not None else ""
            line += f"  ⚠️ ELİNİZDE{pnl_str}"
        lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Test mesajı - BIST sinyal botu çalışıyor."
    ok = send_message(text)
    print("Gönderildi." if ok else "Gönderilemedi, TELEGRAM_BOT_TOKEN/CHAT_ID kontrol edin.")
    sys.exit(0 if ok else 1)

