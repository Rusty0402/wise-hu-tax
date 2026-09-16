# Wise HU RSU Tax Calculator

A minimal webapp that computes the **SZJA + SZOCHO tax due on capital gains**
when selling vested Wise (WISE/WSE) shares in Hungary, using historical prices
from Yahoo Finance and official daily FX rates from the Magyar Nemzeti Bank.

The UI is available in **English and Hungarian** — switch with the selector in
the sidebar.

## What it does

1. You enter past **vesting lots** (vest date, ticker, quantity).
2. The app fetches the Yahoo closing price and the MNB FX rate for each vest
   date (falling back to the most recent available business day) and converts
   every lot into a HUF cost basis.
3. You describe a **sale** (ticker, quantity, date, price, fees).
4. The app computes the capital gain using the Hungarian **average-cost**
   method (weighted average HUF cost per share per ticker), then:

   - **SZJA** = 15% of the gain
   - **SZOCHO** = 13% of the gain, **off by default**: shares sold on a
     regulated exchange (Nasdaq/LSE) through a broker are a *controlled
     capital market transaction* taxed at 15% SZJA only. Tick "Apply SZOCHO"
     only if your sale does not qualify. When it applies, SZOCHO is capped at
     24x the monthly minimum wage per year.
   - FX movements are captured automatically because acquisition cost and
     sale proceeds are converted at their respective dates' MNB rates.

Manual overrides are available for every price and FX rate, e.g. for vesting
dates before a listing's Yahoo history begins (WSE only has Yahoo data from
2026-05; WISE.L goes back to 2021-07).

## Tickers

| Key  | Listing     | Currency | Yahoo ticker | Notes                                        |
|------|-------------|----------|--------------|----------------------------------------------|
| WISE | LSE         | GBP      | `WISE.L`     | Yahoo quotes pence; divided by 100 to GBP.  |
| WSE  | Nasdaq (ADR)| USD      | `WSE`        | ADR ratio assumed 1:1 (verify before relying on it). |

## Run locally

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

## Test

```bash
python -m pytest tests -q
```

The smoke tests stub the network seam (`data_fetchers._fetch_*`), so the suite
runs offline.

## Deploy

Push the repo to GitHub and create a **Streamlit Community Cloud** app
pointing at `app.py` with `requirements.txt` as the dependency file.

> This tool provides an estimate only and is not professional tax advice.
> Verify all figures with a qualified Hungarian tax advisor or NAV before
> filing.