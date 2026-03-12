#!/usr/bin/env python3
"""
send_notify.py
──────────────
Reads momentum_data.json and sends a formatted HTML email summary
via Gmail SMTP using credentials stored as GitHub Actions secrets.

Required secrets (set in repo Settings → Secrets → Actions):
  GMAIL_USER    — your Gmail address, e.g. you@gmail.com
  GMAIL_PASS    — a Gmail App Password (NOT your normal password)
                  Create one at: https://myaccount.google.com/apppasswords
  NOTIFY_EMAIL  — destination address (can be same as GMAIL_USER)
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Config from environment (GitHub Actions secrets) ────────────────────────
GMAIL_USER   = os.environ.get("GMAIL_USER", "")
GMAIL_PASS   = os.environ.get("GMAIL_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")

DATA_FILE    = "momentum_data.json"
SCREENER_URL = "https://alex30free.github.io/asset-momentum-screener/"

# ── Colour palette matching the screener page ────────────────────────────────
BG          = "#0d0e0f"
SURFACE     = "#141518"
BORDER      = "#232428"
GOLD_HI     = "#f0b84a"
GOLD        = "#c8922a"
GOLD_DIM    = "#7a5c1e"
GREEN       = "#4caf82"
RED         = "#e05c5c"
TEXT        = "#d4d6de"
TEXT_DIM    = "#7a7d88"
TEXT_HI     = "#f0f1f5"
RANK1_BG    = "rgba(240,184,74,0.18)"
RANK2_BG    = "rgba(196,212,224,0.12)"
RANK3_BG    = "rgba(200,123,74,0.15)"


def fmt_pct(v, bold=False):
    if v is None:
        return f'<span style="color:{TEXT_DIM}">—</span>'
    color = GREEN if v > 0 else RED if v < 0 else TEXT_DIM
    sign  = "+" if v > 0 else ""
    val   = f"{sign}{v:.2f}%"
    if bold:
        return f'<strong style="color:{color};font-size:16px">{val}</strong>'
    return f'<span style="color:{color}">{val}</span>'


def rank_badge(r):
    if r == 1:
        bg, color, border = RANK1_BG, GOLD_HI, GOLD
    elif r == 2:
        bg, color, border = RANK2_BG, "#c8d4e0", "#5a7080"
    elif r == 3:
        bg, color, border = RANK3_BG, "#c87b4a", "#804a20"
    else:
        bg, color, border = "transparent", TEXT_DIM, BORDER
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:28px;height:28px;border-radius:50%;background:{bg};'
        f'color:{color};border:1px solid {border};font-size:13px;font-weight:600">'
        f'{r}</span>'
    )


def top_badge():
    return (
        f'<span style="display:inline-block;background:rgba(240,184,74,0.15);'
        f'color:{GOLD_HI};font-size:9px;letter-spacing:0.08em;text-transform:uppercase;'
        f'padding:2px 7px;border-radius:3px;border:1px solid rgba(240,184,74,0.3);'
        f'margin-left:8px;vertical-align:middle">▲ TOP PICK</span>'
    )


def build_row(asset, rank):
    is_top  = rank <= 3 and asset.get("score") is not None
    row_bg  = "rgba(200,146,42,0.08)" if is_top else "transparent"
    border_b = f"1px solid {BORDER}"

    score_html = fmt_pct(asset.get("score"), bold=True)
    if is_top:
        score_html += top_badge()

    return f"""
    <tr style="background:{row_bg};border-bottom:{border_b}">
      <td style="padding:14px 16px;text-align:center;width:48px">{rank_badge(rank)}</td>
      <td style="padding:14px 16px">
        <div style="font-size:15px;font-weight:500;color:{TEXT_HI}">{asset['label']}</div>
        <div style="font-size:11px;color:{TEXT_DIM};margin-top:2px;font-family:monospace">{asset['sub']}</div>
      </td>
      <td style="padding:14px 16px;text-align:right;font-family:monospace;font-size:13px">{fmt_pct(asset.get('r3'))}</td>
      <td style="padding:14px 16px;text-align:right;font-family:monospace;font-size:13px">{fmt_pct(asset.get('r6'))}</td>
      <td style="padding:14px 16px;text-align:right;font-family:monospace;font-size:13px">{fmt_pct(asset.get('r12'))}</td>
      <td style="padding:14px 16px;text-align:right;font-family:monospace">{score_html}</td>
    </tr>"""


def build_html(data):
    assets   = data.get("assets", [])
    updated  = data.get("updated", "")
    date_str = ""
    if updated:
        try:
            dt = datetime.fromisoformat(updated)
            date_str = dt.strftime("%-d %B %Y")   # e.g. "20 March 2026"
        except Exception:
            date_str = updated[:10]

    top3 = [a for a in assets[:3] if a.get("score") is not None]
    top3_summary = " · ".join(
        f'<span style="color:{GOLD_HI};font-weight:600">{a["label"]}</span> '
        f'({fmt_pct(a.get("score"))})'
        for a in top3
    )

    rows_html = "".join(build_row(a, i + 1) for i, a in enumerate(assets))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Asset Allocation Momentum — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#0a0b0c;font-family:'Segoe UI',Arial,sans-serif">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0b0c;padding:32px 16px">
  <tr><td align="center">
  <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%">

    <!-- ── HEADER ── -->
    <tr>
      <td style="background:{SURFACE};border:1px solid {BORDER};border-bottom:3px solid {GOLD};
                 padding:32px 36px 28px;border-radius:8px 8px 0 0">
        <div style="font-family:monospace;font-size:10px;letter-spacing:0.14em;
                    color:{GOLD};text-transform:uppercase;margin-bottom:12px">
          StockLab · Screener VI · Monthly Update
        </div>
        <div style="font-size:30px;font-weight:700;color:{TEXT_HI};line-height:1.1;margin-bottom:6px">
          Asset Class <span style="color:{GOLD_HI}">Momentum</span>
        </div>
        <div style="font-size:13px;color:{TEXT_DIM};margin-top:8px">
          Updated {date_str} · Rankings for {date_str[3:] if len(date_str) > 8 else 'this month'}
        </div>
      </td>
    </tr>

    <!-- ── TOP 3 SUMMARY ── -->
    <tr>
      <td style="background:rgba(200,146,42,0.08);border-left:1px solid {BORDER};
                 border-right:1px solid {BORDER};padding:20px 36px">
        <div style="font-family:monospace;font-size:10px;letter-spacing:0.12em;
                    color:{GOLD};text-transform:uppercase;margin-bottom:10px">
          ▲ This Month's Top 3 Allocation Targets
        </div>
        <div style="font-size:14px;color:{TEXT};line-height:1.8">
          {top3_summary}
        </div>
      </td>
    </tr>

    <!-- ── TABLE ── -->
    <tr>
      <td style="background:{SURFACE};border:1px solid {BORDER};
                 border-top:none;padding:0;border-radius:0 0 8px 8px;overflow:hidden">
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:monospace">

          <!-- thead -->
          <tr style="background:{BG};border-bottom:1px solid {BORDER}">
            <th style="padding:12px 16px;text-align:center;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500;width:48px">Rank</th>
            <th style="padding:12px 16px;text-align:left;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500">Asset Class</th>
            <th style="padding:12px 16px;text-align:right;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500">3M</th>
            <th style="padding:12px 16px;text-align:right;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500">6M</th>
            <th style="padding:12px 16px;text-align:right;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500">12M</th>
            <th style="padding:12px 16px;text-align:right;font-size:10px;letter-spacing:0.1em;
                       color:{TEXT_DIM};text-transform:uppercase;font-weight:500">Avg Score</th>
          </tr>

          {rows_html}

        </table>
      </td>
    </tr>

    <!-- ── CTA ── -->
    <tr>
      <td style="padding:28px 0 8px;text-align:center">
        <a href="{SCREENER_URL}"
           style="display:inline-block;background:{GOLD_HI};color:#0d0e0f;
                  font-family:monospace;font-size:12px;font-weight:600;
                  letter-spacing:0.12em;text-transform:uppercase;text-decoration:none;
                  padding:12px 28px;border-radius:4px">
          View Full Screener →
        </a>
      </td>
    </tr>

    <!-- ── FOOTER ── -->
    <tr>
      <td style="padding:20px 0 4px;text-align:center;
                 font-family:monospace;font-size:10px;color:{TEXT_DIM};line-height:1.8">
        <div>StockLab · <a href="https://alex30free.github.io/stocklab/"
             style="color:{TEXT_DIM};text-decoration:none">alex30free.github.io/stocklab</a></div>
        <div style="margin-top:6px;color:#3a3c42">
          ⚠ For informational purposes only — not financial advice.
        </div>
      </td>
    </tr>

  </table>
  </td></tr>
  </table>

</body>
</html>"""


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())


def main():
    # Validate secrets are present
    if not GMAIL_USER or not GMAIL_PASS or not NOTIFY_EMAIL:
        print("⚠  Email secrets not configured — skipping notification.")
        print("   Set GMAIL_USER, GMAIL_PASS and NOTIFY_EMAIL in repo secrets.")
        sys.exit(0)   # exit 0 so the workflow doesn't fail

    # Load data
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"⚠  {DATA_FILE} not found — skipping notification.")
        sys.exit(0)

    # Build date string for subject
    updated  = data.get("updated", "")
    date_str = ""
    if updated:
        try:
            dt = datetime.fromisoformat(updated)
            date_str = dt.strftime("%-d %B %Y")
        except Exception:
            date_str = updated[:10]

    top3 = [a["label"] for a in data.get("assets", [])[:3] if a.get("score") is not None]
    top3_str = " · ".join(top3) if top3 else "—"

    subject  = f"📊 StockLab Asset Momentum — {date_str} | Top picks: {top3_str}"
    html     = build_html(data)

    print(f"Sending notification to {NOTIFY_EMAIL} …")
    send_email(subject, html)
    print("✅  Email sent successfully.")


if __name__ == "__main__":
    main()
