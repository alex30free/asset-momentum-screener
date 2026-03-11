# Asset Allocation Momentum — StockLab Screener VI

Monthly momentum screener for 9 global asset classes.  
Ranks assets by the average of their **3-month, 6-month and 12-month price return**.  
Top 3 assets are highlighted as the current allocation targets.

**Live page →** `https://<your-github-username>.github.io/asset-momentum-screener/`  
**Part of →** [StockLab](https://alex30free.github.io/stocklab/)

---

## How it works

| Step | What happens |
|------|-------------|
| GitHub Actions | Runs `fetch_momentum.py` every **20th of the month** at 07:00 UTC |
| Python script | Pulls 3M / 6M / 12M price history via **yfinance** for each ETF ticker |
| JSON output | Writes `momentum_data.json` and commits it back to the repo |
| GitHub Pages | Serves `index.html`, which reads `momentum_data.json` and renders the table |

## Asset universe

| Asset class | ETF / Index | Ticker |
|---|---|---|
| USA | S&P 500 (iShares Core) | CSPX.AS |
| Europa | MSCI Europe | IMAE.AS |
| Japan | MSCI Japan | IJPA.AS |
| Tillväxtmarknader | MSCI Emerging Markets | EMIM.AS |
| Sverige | XACT OMXS30 | XACT-OMXS30.ST |
| Svenska småbolag | XACT Svenska Småbolag | XACT-SMABOLAG.ST |
| Obligationer | XACT Obligation | XACT-OBLIGATION.ST |
| Korta räntor | Riksbankens Referensränta | — (approximated) |
| Guld | Physical Gold ETC | SGLD.MI |

## Formula

```
Composite Score = ( Return_3M + Return_6M + Return_12M ) / 3
```

Top 3 scores → current month's allocation targets.

## Local setup

```bash
pip install yfinance
python fetch_momentum.py          # writes momentum_data.json
# then open index.html in a browser
```

## GitHub Pages setup

1. Go to **Settings → Pages** in this repo  
2. Set source to `main` branch, `/ (root)` folder  
3. Enable Pages → your site will be live at `https://<user>.github.io/<repo>/`

The workflow commits `momentum_data.json` automatically — Pages re-deploys within ~1 minute.

---

*For informational purposes only — not financial advice.*
