"""This is the main data fetcher.

Two sources:

* Yahoo Finance via yfinance for historical close prices.
* The official Magyar Nemzeti Bank service for historical daily
  HUF rates.

Both sources only quote on business days, so every lookup falls back
to the most recent available quote at/before the requested date.

The two _fetch_* helpers are the network seams: smoke tests monkeypatch
them so no real API calls are made.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from typing import Optional

import requests
import yfinance as yf

import i18n
from config import LOOKBACK_DAYS

MNB_WSDL = "http://www.mnb.hu/arfolyamok.asmx"
MNB_NS = "http://www.mnb.hu/webservices/"
MNB_SOAP_ACTION = "http://www.mnb.hu/webservices/MNBArfolyamServiceSoap/GetExchangeRates"

# The SOAP binding lives on plain HTTP (the HTTPS host only serves the help
# page), so we deliberately POST to http://.
# Optional dependency guard: ``mnb`` (zeep-based) is not used; we talk to the
# SOAP endpoint directly with ``requests`` to keep the dependency surface small.
HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": MNB_SOAP_ACTION,
}


@dataclass(frozen=True)
class Quote:
    """Historical stock price and the calendar date it was quoted on."""

    date: date
    value: float


@dataclass(frozen=True)
class Rate:
    """MNB rate (HUF per 1 currency unit) and its calendar date."""

    date: date
    value: float


# --- network seams (monkeypatched by smoke tests) --------------------------

def _fetch_yahoo_close(ticker: str, start: str, end: str) -> Optional[dict]:
    """Return {iso_date: close} for ``ticker`` in [start, end].

    Kept separate so test can pass them without touching network.
    """
    frame = yf.Ticker(ticker).history(
        start=start, end=end, auto_adjust=False
    )
    if frame is None or frame.empty:
        return None
    closes = frame["Close"]
    return {str(ts.date()): float(val) for ts, val in closes.items()}


def _fetch_mnb_rates(currencies: list[str], start: str, end: str) -> Optional[dict]:
    """Return {iso_date: {currency: huf_per_unit}} for the given range.

    Hits MNB SOAP service and parses the XML.
    """
    currency_csv = ",".join(currencies)
    body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:web="{MNB_NS}">
  <soap:Body>
    <web:GetExchangeRates>
      <web:startDate>{start}</web:startDate>
      <web:endDate>{end}</web:endDate>
      <web:currencyNames>{currency_csv}</web:currencyNames>
    </web:GetExchangeRates>
  </soap:Body>
</soap:Envelope>"""
    resp = requests.post(MNB_WSDL, data=body, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return _parse_mnb_response(resp.text, currencies)


def _parse_mnb_response(xml_text: str, currencies: list[str]) -> dict:
    """Extract {iso_date: {currency: huf_per_unit}} from a SOAP response."""
    import xml.etree.ElementTree as ET

    def strip(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    outer = ET.fromstring(xml_text)
    result_text: Optional[str] = None
    for elem in outer.iter():
        if strip(elem.tag) == "GetExchangeRatesResult" and elem.text:
            result_text = elem.text.strip()
            break
    if not result_text:
        raise ValueError("MNB SOAP response contained no exchange-rate result")

    inner = ET.fromstring(result_text)
    days: dict[str, dict[str, float]] = {}
    for day in inner.iter():
        if strip(day.tag) != "Day":
            continue
        day_date = day.attrib.get("date")
        if not day_date:
            continue
        rates: dict[str, float] = {}
        for rate in day:
            if strip(rate.tag) != "Rate":
                continue
            currency = rate.attrib.get("curr")
            unit = float(rate.attrib.get("unit", "1"))
            if currency in currencies:
                # MNB sends decimals with a comma (Hungarian locale).
                raw = (rate.text or "0").replace(",", ".")
                rates[currency] = float(raw) / unit
        days[day_date] = rates
    return days


# --- public lookups ---------------------------------------------------------

def _lookback_dates(on_date: date, lookback: int = LOOKBACK_DAYS) -> list[date]:
    """All calendar dates in [on_date - lookback, on_date], oldest first."""
    start = on_date - timedelta(days=lookback)
    return [start + timedelta(days=i) for i in range((on_date - start).days + 1)]


@lru_cache(maxsize=512)
def get_stock_price(
    ticker: str, on_date: date, divisor: float = 1.0, adr_ratio: float = 1.0, lang: str = "en"
) -> Quote:
    """Close price of ``ticker`` at or before ``on_date``.

    ``divisor`` converts pence-quoted listings into whole units (see
    ``config.Security``). ``adr_ratio`` converts an ADR quote into ordinary
    shares. Raises ``ValueError`` if nothing is available within the lookback.
    """
    days = _lookback_dates(on_date)
    data = _fetch_yahoo_close(ticker, days[0].isoformat(), (on_date + timedelta(days=1)).isoformat())
    if not data:
        raise ValueError(
            i18n.no_data_message(
                "yahoo_around", ticker, on_date.isoformat(), lang
            )
        )
    for day in reversed(days):
        iso = day.isoformat()
        if iso in data:
            price = data[iso] / divisor * adr_ratio
            return Quote(date=day, value=round(price, 6))
    raise ValueError(
        i18n.no_data_message(
            "yahoo_before", ticker, on_date.isoformat(), lang
        )
    )


@lru_cache(maxsize=512)
def get_exchange_rate(currency: str, on_date: date, lang: str = "en") -> Rate:
    """Official MNB HUF rate for ``currency`` at or before ``on_date``."""
    days = _lookback_dates(on_date)
    data = _fetch_mnb_rates([currency], days[0].isoformat(), on_date.isoformat())
    if not data:
        raise ValueError(
            i18n.no_data_message(
                "mnb_around", currency, on_date.isoformat(), lang
            )
        )
    for day in reversed(days):
        iso = day.isoformat()
        if iso in data and currency in data[iso]:
            return Rate(date=day, value=float(data[iso][currency]))
    raise ValueError(
        i18n.no_data_message(
            "mnb_before", currency, on_date.isoformat(), lang
        )
    )
