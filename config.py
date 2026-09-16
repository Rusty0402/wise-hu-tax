"""Central configuration for the WiseHU RSU tax calculator.

Tax constants and default security metadata live here so they are easy to
review and update as Hungarian rules and Wise listings change.
"""

from dataclasses import dataclass

# --- Hungarian personal income tax (SZJA) ---------------------------------
SZJA_RATE = 0.15

# --- Social contribution tax (SZOCHO) on investment income -----------------
SZOCHO_RATE = 0.13

# 2026 statutory minimum wage (HUF / month), per 426/2025. (XII. 23.) Korm.
# rendelet.
MINIMUM_WAGE_MONTHLY_2026 = 322_800

# The 13% SZOCHO on investment income (when it applies) is payable only up to
# 24x the *monthly* minimum wage per calendar year (Szocho tv.).
# 2026: 24 * 322,800 = 7,747,200 HUF/year.
SZOCHO_CAP_MULTIPLIER = 24
SZOCHO_ANNUAL_CAP_2026 = MINIMUM_WAGE_MONTHLY_2026 * SZOCHO_CAP_MULTIPLIER


@dataclass(frozen=True)
class Security:
    """A tradable listing of an RSU-eligible security.

    ``yahoo_ticker`` is what Yahoo Finance expects. ``currency`` is the
    currency the *Yahoo price* is quoted in, which is not always the currency
    a human would assume (LSE listings report GBp/pence, not GBP).
    ``price_divisor`` converts the raw Yahoo quote into whole ``currency``
    units (100 for pence -> pounds, 1 otherwise).
    """

    key: str
    yahoo_ticker: str
    currency: str
    price_divisor: float = 1.0
    adr_ratio: float = 1.0


# Wise plc listings. WISE.L prices are reported by Yahoo in pence (GBp), so
# price_divisor=100 turns them into GBP. adr_ratio converts an ADR price into
# ordinary-share terms (1.0 until the ratio is confirmed for WSE).
SECURITIES: dict[str, Security] = {
    "WSE": Security(
        key="WSE",
        yahoo_ticker="WSE",
        currency="USD",
    ),
    "WISE": Security(
        key="WISE",
        yahoo_ticker="WISE.L",
        currency="GBP",
        price_divisor=100.0,
    ),
}

# How far back to look for a price/rate when the requested date is a weekend
# or public holiday. Both Yahoo and MNB simply have no quote on those days.
LOOKBACK_DAYS = 14