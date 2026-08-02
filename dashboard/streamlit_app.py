import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import STATE_PATH, load_watchlist  # noqa: E402
from app.data_fetch import fetch_single  # noqa: E402
from app.indicators import compute_indicators  # noqa: E402

st.set_page_config(page_title="BIST Sinyal Paneli", layout="wide")


def _password_gate():
    try:
        required = st.secrets.get("DASHBOARD_PASSWORD")
    except Exception:
        required = None
    if not required:
        return True
    if st.session_state.get("authed"):
        return True
    pw = st.text_input("Şifre", type="password")
    if pw == required:
        st.session_state["authed"] = True
        return True
    if pw:
        st.error("Yanlış şifre")
    return False


if not _password_gate():
    st.stop()

st.title("BIST Sinyal Paneli")

if not STATE_PATH.exists():
    st.warning("Henüz veri yok. GitHub Actions zamanlanmış görevi ilk kez çalıştığında burada veriler görünecek.")
    st.stop()

with open(STATE_PATH, "r", encoding="utf-8") as f:
    state = json.load(f)

if not state:
    st.info("State dosyası boş, henüz sinyal hesaplanmamış.")
    st.stop()

rows = []
for ticker, data in state.items():
    rows.append({
        "Hisse": ticker,
        "Sinyal": data.get("signal"),
        "Skor": data.get("score"),
        "RSI": data.get("rsi"),
        "MACD": data.get("macd"),
        "MACD Sinyal": data.get("macd_signal"),
        "SMA20": data.get("sma_fast"),
        "SMA50": data.get("sma_slow"),
        "Son Kapanış": data.get("last_close"),
        "Elimde": "✅" if data.get("held") else "",
        "K/Z %": data.get("pnl_pct"),
        "Son Değişim": data.get("last_changed"),
    })

df = pd.DataFrame(rows)

col1, col2, col3 = st.columns(3)
col1.metric("Toplam Hisse", len(df))
col2.metric("AL Sinyali", int((df["Sinyal"] == "BUY").sum()))
col3.metric("SAT Sinyali", int((df["Sinyal"] == "SELL").sum()))

signal_filter = st.multiselect("Sinyale göre filtrele", ["BUY", "SELL", "HOLD"],
                                default=["BUY", "SELL", "HOLD"])
held_only = st.checkbox("Sadece elimdekiler")

filtered = df[df["Sinyal"].isin(signal_filter)]
if held_only:
    filtered = filtered[filtered["Elimde"] == "✅"]

def _color_signal(val):
    color = {"BUY": "#1a7f37", "SELL": "#cf222e", "HOLD": "#57606a"}.get(val, "")
    return f"color: {color}; font-weight: bold"

st.dataframe(
    filtered.sort_values("Skor", ascending=False).style.map(_color_signal, subset=["Sinyal"]),
    width="stretch",
    hide_index=True,
)

st.divider()
st.subheader("Hisse Grafiği")

all_tickers, thresholds = load_watchlist()
selected = st.selectbox("Hisse seçin", sorted(state.keys()))

if selected:
    with st.spinner(f"{selected} verisi çekiliyor..."):
        hist = fetch_single(selected, period="6mo")
    if hist is None:
        st.error("Veri çekilemedi.")
    else:
        enriched = compute_indicators(hist, thresholds)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=enriched.index, open=enriched["Open"], high=enriched["High"],
            low=enriched["Low"], close=enriched["Close"], name=selected,
        ))
        fig.add_trace(go.Scatter(x=enriched.index, y=enriched["sma_fast"],
                                  name="SMA20", line=dict(color="orange", width=1)))
        fig.add_trace(go.Scatter(x=enriched.index, y=enriched["sma_slow"],
                                  name="SMA50", line=dict(color="blue", width=1)))
        fig.add_trace(go.Scatter(x=enriched.index, y=enriched["bb_upper"],
                                  name="BB Üst", line=dict(color="gray", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=enriched.index, y=enriched["bb_lower"],
                                  name="BB Alt", line=dict(color="gray", width=1, dash="dot")))
        fig.update_layout(xaxis_rangeslider_visible=False, height=500)
        st.plotly_chart(fig, width="stretch")
