"""Smoke tests for the WiseHU RSU tax calculator.

Network-touching functions are stubbed so the suite runs offline. The tax
math itself is exercised with hand-computed expectations.
"""

from datetime import date

import pytest

import data_fetchers as df
import i18n
import tax_calculator as tc


@pytest.fixture(autouse=True)
def _clear_fetch_caches():
    df.get_stock_price.cache_clear()
    df.get_exchange_rate.cache_clear()
    yield


# ---------------------------------------------------------------------------
# tax_calculator: average cost
# ---------------------------------------------------------------------------

def _wise_lot(qty, price, rate, day=1):
    return tc.VestingLot(
        date=date(2024, 1, day), ticker="WISE", qty=qty,
        price_native=price, rate_huf=rate,
    )


def test_average_cost_weighted_by_quantity():
    lots = [
        _wise_lot(qty=10, price=10.0, rate=400.0, day=1),
        _wise_lot(qty=20, price=15.0, rate=400.0, day=2),
    ]
    avg = tc.average_cost_per_share(lots)
    assert avg["WISE"] == pytest.approx(160_000 / 30)


def test_average_cost_pools_per_ticker():
    lots = [
        tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0),
        tc.VestingLot(date(2024, 1, 1), "WSE", 10, 25.0, 300.0),
    ]
    avg = tc.average_cost_per_share(lots)
    assert avg["WISE"] == pytest.approx(4_000.0)
    assert avg["WSE"] == pytest.approx(7_500.0)


# ---------------------------------------------------------------------------
# tax_calculator: sale tax math
# ---------------------------------------------------------------------------

def test_sale_tax_gain_hand_computed():
    lots = [
        _wise_lot(qty=10, price=10.0, rate=400.0, day=1),
        _wise_lot(qty=20, price=15.0, rate=400.0, day=2),
    ]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=5, price_native=20.0, rate_huf=410.0, fees_huf=1_000.0)

    res = tc.calculate_sale_tax(lots, sale, apply_szocho=True)

    avg = 160_000 / 30
    proceeds = 5 * 20.0 * 410.0
    gross = proceeds - 5 * avg - 1_000.0

    assert res.proceeds_huf == pytest.approx(proceeds)
    assert res.cogs_huf == pytest.approx(5 * avg)
    assert res.gross_gain_huf == pytest.approx(gross)
    assert res.szja == pytest.approx(gross * 0.15, abs=0.01)
    assert res.szocho == pytest.approx(gross * 0.13, abs=0.01)
    assert res.total_tax == pytest.approx(gross * 0.28, abs=0.01)
    assert not res.is_loss


def test_fx_movement_is_captured_as_gain():
    lots = [tc.VestingLot(date(2024, 1, 1), "WSE", 10, price_native=10.0, rate_huf=300.0)]
    sale = tc.Sale(date(2024, 6, 1), "WSE", qty=10, price_native=10.0, rate_huf=330.0)
    res = tc.calculate_sale_tax(lots, sale, apply_szocho=True)
    # Same USD price, but HUF weakened: 10*10*330 - 10*10*300 = 3,000 FX gain.
    assert res.gross_gain_huf == pytest.approx(3_000.0)
    assert res.szja == pytest.approx(450.0)
    assert res.szocho == pytest.approx(390.0)


def test_loss_yields_zero_tax_and_warning():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=8.0, rate_huf=400.0)
    res = tc.calculate_sale_tax(lots, sale)
    assert res.is_loss
    assert res.total_tax == 0.0
    assert res.szja == 0.0 and res.szocho == 0.0
    assert any("loss" in w.lower() for w in res.warnings)


def test_szocho_off_by_default():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=12.0, rate_huf=400.0)
    res = tc.calculate_sale_tax(lots, sale)
    gross = 10 * 12.0 * 400.0 - 10 * 4_000
    assert res.szocho == 0.0
    assert res.szja == pytest.approx(0.15 * gross)
    assert res.total_tax == pytest.approx(0.15 * gross)
    assert any("SZOCHO was not applied" in w for w in res.warnings)


def test_zero_gain_has_no_percentage_delta():
    assert tc.tax_as_percent_of_gain(0.0, 0.0) is None
    assert tc.tax_as_percent_of_gain(0.0, -500.0) is None
    assert tc.tax_as_percent_of_gain(280.0, 1_000.0) == pytest.approx(28.0)


def test_error_messages_localized():
    lots = [_wise_lot(qty=10, price=10.0, rate=400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WSE", qty=1, price_native=12.0, rate_huf=400.0)
    with pytest.raises(ValueError) as exc:
        tc.calculate_sale_tax(lots, sale, lang="hu")
    assert "Nem található" in str(exc.value)


def test_apply_szocho_false_zeroes_szocho():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=12.0, rate_huf=400.0)
    res = tc.calculate_sale_tax(lots, sale, apply_szocho=False)
    assert res.szocho == 0.0
    assert res.szja == pytest.approx(0.15 * (10 * 12.0 * 400.0 - 10 * 4_000))
    assert any("SZOCHO was not applied" in w for w in res.warnings)


def test_fees_are_deductible():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=12.0, rate_huf=400.0, fees_huf=2_000.0)
    res = tc.calculate_sale_tax(lots, sale)
    assert res.gross_gain_huf == pytest.approx(10 * 12.0 * 400.0 - 10 * 4_000 - 2_000)


def test_selling_more_than_vested_raises():
    lots = [_wise_lot(qty=10, price=10.0, rate=400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=11, price_native=12.0, rate_huf=400.0)
    with pytest.raises(ValueError, match="only 10 shares vested"):
        tc.calculate_sale_tax(lots, sale)


def test_unknown_ticker_raises():
    lots = [_wise_lot(qty=10, price=10.0, rate=400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WSE", qty=1, price_native=12.0, rate_huf=400.0)
    with pytest.raises(ValueError, match="No vesting lots"):
        tc.calculate_sale_tax(lots, sale)


# ---------------------------------------------------------------------------
# data_fetchers: stock prices
# ---------------------------------------------------------------------------

def test_get_stock_price_falls_back_to_nearest_available(monkeypatch):
    monkeypatch.setattr(df, "_fetch_yahoo_close", lambda *a, **k: {"2024-01-02": 200.0})
    quote = df.get_stock_price("WISE.L", date(2024, 1, 5), divisor=100.0)
    assert quote.date == date(2024, 1, 2)
    assert quote.value == pytest.approx(2.0)  # 200 GBp -> GBP 2.00


def test_get_stock_price_applies_adr_ratio(monkeypatch):
    monkeypatch.setattr(df, "_fetch_yahoo_close", lambda *a, **k: {"2024-01-02": 50.0})
    quote = df.get_stock_price("WSE", date(2024, 1, 2), divisor=1.0, adr_ratio=2.0)
    assert quote.value == pytest.approx(100.0)


def test_get_stock_price_no_data_raises(monkeypatch):
    monkeypatch.setattr(df, "_fetch_yahoo_close", lambda *a, **k: None)
    with pytest.raises(ValueError, match="No Yahoo Finance data"):
        df.get_stock_price("WSE", date(2024, 1, 2))


# ---------------------------------------------------------------------------
# data_fetchers: MNB exchange rates
# ---------------------------------------------------------------------------

def test_get_exchange_rate_falls_back_to_nearest_available(monkeypatch):
    monkeypatch.setattr(
        df, "_fetch_mnb_rates",
        lambda *a, **k: {"2024-01-02": {"USD": 380.0, "GBP": 480.0}},
    )
    rate = df.get_exchange_rate("USD", date(2024, 1, 5))
    assert rate.date == date(2024, 1, 2)
    assert rate.value == pytest.approx(380.0)


def test_get_exchange_rate_no_data_raises(monkeypatch):
    monkeypatch.setattr(df, "_fetch_mnb_rates", lambda *a, **k: {})
    with pytest.raises(ValueError, match="No MNB rate"):
        df.get_exchange_rate("USD", date(2024, 1, 5))


def test_parse_mnb_response_with_escaped_inner_xml():
    xml_text = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:web="http://www.mnb.hu/webservices/">'
        "<soap:Body><web:GetExchangeRatesResponse>"
        "<web:GetExchangeRatesResult>"
        "&lt;MNBCurrentExchangeRates&gt;"
        "&lt;Day date=\"2024-01-02\"&gt;"
        "&lt;Rate unit=\"1\" curr=\"USD\" decim=\"0\"&gt;380.0&lt;/Rate&gt;"
        "&lt;Rate unit=\"100\" curr=\"JPY\" decim=\"0\"&gt;280.0&lt;/Rate&gt;"
        "&lt;/Day&gt;"
        "&lt;/MNBCurrentExchangeRates&gt;"
        "</web:GetExchangeRatesResult></web:GetExchangeRatesResponse>"
        "</soap:Body></soap:Envelope>"
    )
    parsed = df._parse_mnb_response(xml_text, ["USD", "JPY"])
    assert parsed["2024-01-02"]["USD"] == pytest.approx(380.0)
    # unit=100 means the rate is HUF per 100 JPY -> divide.
    assert parsed["2024-01-02"]["JPY"] == pytest.approx(2.8)


# ---------------------------------------------------------------------------
# i18n: Hungarian output
# ---------------------------------------------------------------------------

def test_loss_warning_hungarian():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=8.0, rate_huf=400.0)
    res = tc.calculate_sale_tax(lots, sale, lang="hu")
    assert res.total_tax == 0.0
    assert "tőkeveszteség" in res.warnings[0]


def test_szocho_warning_hungarian():
    lots = [tc.VestingLot(date(2024, 1, 1), "WISE", 10, 10.0, 400.0)]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=10, price_native=12.0, rate_huf=400.0)
    res = tc.calculate_sale_tax(lots, sale, apply_szocho=False, lang="hu")
    assert "nem került alkalmazásra" in res.warnings[0]
    assert res.szja == pytest.approx(0.15 * (10 * 12.0 * 400.0 - 10 * 4_000))


def test_language_does_not_change_numbers():
    lots = [
        _wise_lot(qty=10, price=10.0, rate=400.0, day=1),
        _wise_lot(qty=20, price=15.0, rate=400.0, day=2),
    ]
    sale = tc.Sale(date(2024, 6, 1), "WISE", qty=5, price_native=20.0, rate_huf=410.0, fees_huf=1_000.0)
    en = tc.calculate_sale_tax(lots, sale, lang="en")
    hu = tc.calculate_sale_tax(lots, sale, lang="hu")
    assert en.total_tax == hu.total_tax
    assert en.proceeds_huf == hu.proceeds_huf


def test_no_data_message_hungarian():
    msg = i18n.no_data_message("yahoo_around", "WSE", "2024-01-01", "hu")
    assert "Nem található" in msg
    msg_en = i18n.no_data_message("mnb_before", "GBP", "2024-01-01", "en")
    assert "No MNB rate found" in msg_en


# ---------------------------------------------------------------------------
# end-to-end smoke (pure math, no network)
# ---------------------------------------------------------------------------

def test_end_to_end_two_tickers_no_network():
    lots = [
        tc.VestingLot(date(2023, 6, 1), "WISE", 25, 8.5, 350.0),
        tc.VestingLot(date(2023, 12, 1), "WISE", 25, 11.0, 370.0),
        tc.VestingLot(date(2024, 3, 1), "WSE", 20, 15.0, 360.0),
    ]
    sale = tc.Sale(date(2024, 9, 1), "WISE", qty=30, price_native=13.0, rate_huf=390.0, fees_huf=500.0)

    res = tc.calculate_sale_tax(lots, sale, apply_szocho=True)

    total_cost = 25 * 8.5 * 350.0 + 25 * 11.0 * 370.0
    avg = total_cost / 50
    proceeds = 30 * 13.0 * 390.0
    gross = proceeds - 30 * avg - 500.0

    assert res.avg_cost_per_share_huf == pytest.approx(avg)
    assert res.proceeds_huf == pytest.approx(proceeds)
    assert res.total_tax == pytest.approx(gross * 0.28)
    assert res.total_tax > 0