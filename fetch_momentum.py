#!/usr/bin/env python3
"""
fetch_momentum.py
─────────────────
Fetches 3-month, 6-month and 12-month price returns for 9 asset class ETFs
via yfinance, then writes momentum_data.json for the screener page.

Usage:
    pip install yfinance
    python fetch_momentum.py
"""

import json
import math
import time
from datetime import datetime, timedelta, timezone

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("ERROR: Run: pip install yfinance")

# ── VERIFIED Yahoo Finance tickers ─────────────────────────────────────────────
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

# Update this to the current Riksbank policy rate
RIKSBANK_RATE_PCT = 2.25

WINDOW_DAYS = {3: 95, 6: 190, 12: 380}


def fetch_return(ticker_sym, months, retries=3):
    cal_days = WINDOW_DAYS[months]
    start_dt = datetime.now(timezone.utc) - timedelta(days=cal_days + 20)

    for attempt in range(retries):
        try:
            tkr  = yf.Ticker(ticker_sym)
            hist = tkr.history(
                start=start_dt.strftime("%Y-%m-%d"),
                interval="1d",
                auto_adjust=True,
            )

            if hist is None or hist.empty or len(hist) < 10:
                print(f"      no data (attempt {attempt+1})")
                time.sleep(2 ** attempt)
                continue

            if hist.index.tz is not None:
                hist.index = hist.index.tz_convert(None)

            close = hist["Close"].dropna()
            if len(close) < 5:
                return None

            current_price = float(close.iloc[-1])
            target_date   = datetime.now() - timedelta(days=cal_days)
            diffs         = abs(close.index.to_series() - target_date)
            base_price    = float(close.loc[diffs.idxmin()])

            if base_price <= 0:
                return None

            return round((current_price / base_price - 1) * 100, 4)

        except Exception as exc:
            print(f"      Error attempt {attempt+1}: {exc}")
            time.sleep(2 ** attempt)

    return None


def cash_returns():
    return {
        "r3":  round(RIKSBANK_RATE_PCT / 4, 4),
        "r6":  round(RIKSBANK_RATE_PCT / 2, 4),
        "r12": round(RIKSBANK_RATE_PCT,      4),
    }


def main():
    now_utc = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  Asset Allocation Momentum Fetcher")
    print(f"  {now_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    results = []

    for asset in ASSETS:
        label  = asset["label"]
        ticker = asset["ticker"]
        print(f"-> {label} ({ticker or 'rate approx'})")

        if ticker is None:
            cash = cash_returns()
            r3, r6, r12 = cash["r3"], cash["r6"], cash["r12"]
        else:
            r3  = fetch_return(ticker, 3);  time.sleep(1)
            r6  = fetch_return(ticker, 6);  time.sleep(1)
            r12 = fetch_return(ticker, 12); time.sleep(1)

        vals  = [v for v in [r3, r6, r12] if v is not None]
        score = round(sum(vals) / len(vals), 4) if vals else None

        print(f"   3M={r3}  6M={r6}  12M={r12}  score={score}\n")

        results.append({
            "key":    asset["key"],
            "label":  label,
            "sub":    asset["sub"],
            "ticker": ticker,
            "r3":     r3,
            "r6":     r6,
            "r12":    r12,
            "score":  score,
        })

    results.sort(
        key=lambda x: x["score"] if x["score"] is not None else -math.inf,
        reverse=True,
    )

    output = {
        "updated": now_utc.isoformat(),
        "assets":  results,
    }

    with open("momentum_data.json", "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print(f"{'='*60}")
    print(f"  Saved momentum_data.json")
    for i, r in enumerate(results[:3]):
        print(f"  Top {i+1}: {r['label']}  score={r['score']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
