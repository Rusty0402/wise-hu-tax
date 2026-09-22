"""Main tax calculation logic.

NO I/O HERE: input is already in HUF with
the corresponding MNB rate supplied via SOAP. This keeps the math trivial and separate from I/O Python.

Model for tax rules as of 2026:

* Shares sold on a regulated exchange (Nasdaq/LSE) through a broker count as
  an "ellenőrzött tőkepiaci ügylet" (controlled capital market transaction).
  The resulting gain is taxed at SZJA only (15%), and NO SZOCHO applies.
  Gains and losses from such transactions are netted within the tax year.
* SZOCHO (13%) applies only when the transaction does NOT qualify as a
  controlled capital market transaction, and even then only up to 24x the
  monthly minimum wage per year. The app therefore defaults to
  ``apply_szocho=False`` and treats SZOCHO as an explicit opt-in.
* At sale, the capital gain (árfolyamnyereség) is:
      proceeds_HUF - (qty_sold * average_cost_per_share_HUF) - fees
  where the average cost is computed across all vesting lots of the same
  security, each lot converted to HUF at the MNB rate on its vesting date.
* FX movements are automatically captured because acquisition cost and sale
  proceeds are converted at their respective dates' MNB rates.
* A negative gain yields zero tax (losses may offset other capital gains; the
  app surfaces the loss amount rather than netting across securities).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import i18n
from config import SZOCHO_RATE, SZJA_RATE


@dataclass
class VestingLot:
    """One RSU vesting event, already decorated with market data."""

    date: date
    ticker: str
    qty: float
    price_native: float
    rate_huf: float  # official MNB rate, HUF per 1 currency unit

    @property
    def cost_basis_huf(self) -> float:
        return self.qty * self.price_native * self.rate_huf


@dataclass
class Sale:
    """One sale event, already decorated with market data."""

    date: date
    ticker: str
    qty: float
    price_native: float
    rate_huf: float  # official MNB rate, HUF per 1 currency unit
    fees_huf: float = 0.0


@dataclass
class TaxResult:
    """Everything a user needs to understand and verify the tax due."""

    ticker: str
    qty_sold: float
    avg_cost_per_share_huf: float
    proceeds_huf: float
    cogs_huf: float
    fees_huf: float
    gross_gain_huf: float
    szja: float
    szocho: float
    total_tax: float
    is_loss: bool
    warnings: list[str] = field(default_factory=list)


def average_cost_per_share(lots: list[VestingLot]) -> dict[str, float]:
    """Weighted-average HUF cost per share, keyed by ticker.

    The Hungarian default cost-basis method for securities. Only lots of the
    same ticker are pooled.
    """
    totals: dict[str, list[float]] = {}
    for lot in lots:
        totals.setdefault(lot.ticker, []).append(
            (lot.qty, lot.cost_basis_huf)
        )
    return {
        ticker: sum(cost for _, cost in rows) / sum(qty for qty, _ in rows)
        for ticker, rows in totals.items()
        if sum(qty for qty, _ in rows) > 0
    }


def tax_as_percent_of_gain(total_tax: float, gross_gain_huf: float) -> Optional[float]:
    """Effective tax as a percentage of the gross gain.

    Returns ``None`` when there is no positive gain (zero or a loss), which
    avoids division-by-zero in the UI.
    """
    if gross_gain_huf <= 0:
        return None
    return total_tax / gross_gain_huf * 100


def calculate_sale_tax(
    lots: list[VestingLot],
    sale: Sale,
    szja_rate: float = SZJA_RATE,
    szocho_rate: float = SZOCHO_RATE,
    apply_szocho: bool = False,
    lang: str = "en",
) -> TaxResult:
    """Calculate SZJA + SZOCHO due on ``sale`` against ``lots``.

    ``apply_szocho`` defaults to ``False`` because a sale on a regulated
    exchange through a broker is a controlled capital market transaction
    (15% SZJA only). Pass ``True`` only for transactions that do not qualify.

    ``lang`` selects the language of the human-readable warnings
    ("en" or "hu"); it does not affect the numbers.

    Raises ``ValueError`` when the sale references an unknown ticker or more
    shares than were ever vested.
    """
    ticker_lots = [lot for lot in lots if lot.ticker == sale.ticker]
    if not ticker_lots:
        raise ValueError(
            i18n.t("err_no_lots_ticker", lang).format(ticker=sale.ticker)
        )

    held = sum(lot.qty for lot in ticker_lots)
    if sale.qty > held:
        raise ValueError(
            i18n.t("err_sell_exceeds", lang).format(
                qty=sale.qty, ticker=sale.ticker, held=held
            )
        )
    if sale.qty < 0:
        raise ValueError(i18n.t("err_negative_qty", lang))

    avg_cost = average_cost_per_share(lots)[sale.ticker]
    proceeds_huf = sale.qty * sale.price_native * sale.rate_huf
    cogs_huf = sale.qty * avg_cost
    gross_gain = proceeds_huf - cogs_huf - sale.fees_huf

    warnings: list[str] = []
    is_loss = gross_gain < 0

    if is_loss:
        szja = 0.0
        szocho = 0.0
        warnings.append(i18n.loss_warning(abs(gross_gain), lang))
    else:
        szja = gross_gain * szja_rate
        szocho = gross_gain * szocho_rate if apply_szocho else 0.0
        if not apply_szocho:
            warnings.append(i18n.szocho_warning(lang))

    return TaxResult(
        ticker=sale.ticker,
        qty_sold=sale.qty,
        avg_cost_per_share_huf=round(avg_cost, 2),
        proceeds_huf=round(proceeds_huf, 2),
        cogs_huf=round(cogs_huf, 2),
        fees_huf=round(sale.fees_huf, 2),
        gross_gain_huf=round(gross_gain, 2),
        szja=round(szja, 2),
        szocho=round(szocho, 2),
        total_tax=round(szja + szocho, 2),
        is_loss=is_loss,
        warnings=warnings,
    )
