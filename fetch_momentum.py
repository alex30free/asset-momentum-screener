#!/usr/bin/env python3
"""
fetch_momentum.py
─────────────────
Fetches 3M / 6M / 12M price returns for each asset class ETF via
yfinance and writes momentum_data.json to the repo root.

Run manually:   python fetch_momentum.py
Run via CI/CD:  GitHub Actions (.github/workflows/update_momentum.yml)
"""

import json
import math
from datetime import datetime, timedelta, timezone

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("yfinance is not installed. Run: pip install yfinance")

# ── ASSET CONFIGURATION ────────────────────────────────────────────────────────
# ticker: Yahoo Finance symbol. None = no market price (e.g. Riksbankens ränta)
ASSETS = [
    {"key": "usa",    "label": "USA",                "sub": "S&P 500",                   "ticker": "CSPX.AS"},
    {"key": "europe", "label": "Europa",              "sub": "MSCI Europe",               "ticker": "IMAE.AS"},
    {"key": "japan",  "label": "Japan",               "sub": "MSCI Japan",                "ticker": "IJPA.AS"},
    {"key": "em",     "label": "Tillväxtmarknader",   "sub": "MSCI Emerging Markets",     "ticker": "EMIM.AS"},
    {"key": "sweden", "label": "Sverige",             "sub": "XACT OMXS30",               "ticker": "XACT-OMXS30.ST"},
    {"key": "smswe",  "label": "Svenska småbolag",    "sub": "XACT Svenska Småbolag",     "ticker": "XACT-SMABOLAG.ST"},
    {"key": "bonds",  "label": "Obligationer",        "sub": "XACT Obligation",           "ticker": "XACT-OBLIGATION.ST"},
    {"key": "cash",   "label": "Korta räntor",        "sub": "Riksbankens Referensränta", "ticker": None},
    {"key": "gold",   "label": "Guld",                "sub": "Physical Gold",             "ticker": "SGLD.MI"},
]

# ── HELPERS ────────────────────────────────────────────────────────────────────

def trading_days_ago(n: int) -> datetime:
    """Return a date roughly n calendar days ago (yfinance handles weekends)."""
    return datetime.now(timezone.utc) - timedelta(days=n)


def fetch_return(ticker_sym: str, months: int) -> float | None:
    """
    Return the price return (%) for <ticker_sym> over the last <months> months.
    Returns None on failure.
    """
    cal_days = int(months * 31)          # a little extra to guarantee enough history
    start = datetime.now(timezone.utc) - timedelta(days=cal_days + 10)

    try:
        tkr = yf.Ticker(ticker_sym)
        hist = tkr.history(start=start.strftime("%Y-%m-%d"), interval="1d", auto_adjust=True)
        if hist.empty or len(hist) < 2:
            return None

        # price exactly ~months ago: pick the row closest to cal_days back
        target = datetime.now(timezone.utc) - timedelta(days=cal_days)
        # find closest date
        hist.index = hist.index.tz_localize(None) if hist.index.tz is None else hist.index.tz_convert(None)
        diffs = abs(hist.index - target.replace(tzinfo=None))
        past_close = float(hist.loc[diffs.idxmin(), "Close"])
        now_close  = float(hist["Close"].iloc[-1])

        if past_close <= 0:
            return None
        return round((now_close / past_close - 1) * 100, 4)

    except Exception as exc:
        print(f"  ⚠  {ticker_sym} ({months}M): {exc}")
        return None


# ── RIKSBANK REFERENCE RATE (manual / approximate) ─────────────────────────────
def get_riksbank_rate_approx() -> dict:
    """
    The Riksbank reference rate is not traded as a price series.
    We approximate the 'return' as the cumulative rate itself (annualised).
    Users can override RIKSBANK_RATE_PCT below with the current value.
    """
    RIKSBANK_RATE_PCT = 2.25   # ← update manually each month if desired
    return {
        "r3":  round(RIKSBANK_RATE_PCT / 4, 4),
        "r6":  round(RIKSBANK_RATE_PCT / 2, 4),
        "r12": round(RIKSBANK_RATE_PCT, 4),
    }


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    now_iso = datetime.now(timezone.utc).isoformat()
    print(f"\n🏦 Asset Allocation Momentum Fetcher")
    print(f"   Run at: {now_iso}\n")

    results = []
    for asset in ASSETS:
        key    = asset["key"]
        label  = asset["label"]
        ticker = asset["ticker"]

        print(f"→ {label} ({ticker or 'N/A'})")

        if ticker is None:
            # Special handling for Riksbank rate
            rates = get_riksbank_rate_approx()
            r3, r6, r12 = rates["r3"], rates["r6"], rates["r12"]
        else:
            r3  = fetch_return(ticker,  3)
            r6  = fetch_return(ticker,  6)
            r12 = fetch_return(ticker, 12)

        # Composite score = average of three windows
        vals = [v for v in [r3, r6, r12] if v is not None]
        score = round(sum(vals) / len(vals), 4) if vals else None

        print(f"   3M={r3}  6M={r6}  12M={r12}  → score={score}\n")

        results.append({
            "key":   key,
            "label": label,
            "sub":   asset["sub"],
            "ticker": ticker,
            "r3":    r3,
            "r6":    r6,
            "r12":   r12,
            "score": score,
        })

    # Sort by score descending (None last)
    results.sort(key=lambda x: x["score"] if x["score"] is not None else -math.inf, reverse=True)

    output = {
        "updated": now_iso,
        "assets":  results,
    }

    with open("momentum_data.json", "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print("✅  Written to momentum_data.json")


if __name__ == "__main__":
    main()
