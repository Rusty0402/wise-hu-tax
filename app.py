"""Streamlit UI for the Wise HU RSU tax calculator.

Flow:
1. Enter vesting lots (date, ticker, qty). Auto-fetch the Yahoo
   closing price and MNB FX rate for each lot.
2. Describe a sale (ticker, qty, date, price, rate, fees).
3. The app computes SZJA + SZOCHO due on the capital gain using the
   Hungarian average-cost method and shows a full breakdown.

The UI is available in English and Hungarian.
"""

from datetime import date

import pandas as pd
import streamlit as st

import data_fetchers as df
import tax_calculator as tc
from config import SECURITIES, SZOCHO_ANNUAL_CAP_2026, SZOCHO_RATE, SZJA_RATE
from i18n import LANGUAGES, t

st.set_page_config(page_title="Wise HU RSU Tax Calculator", layout="centered")

st.markdown(
    """
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #163300;
        border-color: #163300;
        color: #ffffff;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1f4400;
        border-color: #1f4400;
        color: #ffffff;
    }
    div.stButton > button[kind="primary"]:focus {
        border-color: #163300;
        box-shadow: 0 0 0 0.2rem rgba(22, 51, 0, 0.35);
    }
    [data-testid="stDataEditor"],
    div.stDataFrameGlideDataEditor {
        --gdg-accent-color: #163300 !important;
        --gdg-accent-fg: #ffffff !important;
        --gdg-accent-light: rgba(22, 51, 0, 0.15) !important;
        --primary-color: #163300 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: language, rates and SZOCHO cap
# ---------------------------------------------------------------------------
with st.sidebar:
    lang = st.selectbox(
        t("language", "en"),
        options=list(LANGUAGES),
        format_func=lambda code: LANGUAGES[code],
        key="lang",
    )
    st.header(t("settings", lang))
    szja_rate = st.number_input(
        t("szja_rate", lang), min_value=0.0, max_value=1.0, value=SZJA_RATE,
        step=0.005, format="%.3f",
    )
    szocho_rate = st.number_input(
        t("szocho_rate", lang), min_value=0.0, max_value=1.0, value=SZOCHO_RATE,
        step=0.005, format="%.3f",
    )
    apply_szocho = st.checkbox(
        t("apply_szocho_label", lang),
        value=False,
        help=t("apply_szocho_help", lang).format(cap=f"{SZOCHO_ANNUAL_CAP_2026:,.0f}"),
    )
st.caption(t("disclaimer", lang))

with st.expander(t("donate_title", lang)):
    st.write(t("donate_body", lang))

st.title(t("app_title", lang))
st.caption(t("app_subtitle", lang))

# ---------------------------------------------------------------------------
# Helper: default empty lots table
# ---------------------------------------------------------------------------
LOT_COLUMNS = ["date", "ticker", "qty", "price", "fx_rate"]


def empty_lots() -> pd.DataFrame:
    return pd.DataFrame(
        [{"date": date.today(), "ticker": "WISE", "qty": 0.0, "price": 0.0, "fx_rate": 0.0}],
        columns=LOT_COLUMNS,
    )


if "lots" not in st.session_state:
    st.session_state.lots = empty_lots()


def _build_csv(lots: pd.DataFrame, result: tc.TaxResult, lang: str = "en") -> str:
    """Render the lots + result as a CSV string for download."""
    lines: list[str] = []
    lines.append(t("csv_title", lang))
    lines.append(f"{t('ticker_sold', lang)},{result.ticker}")
    lines.append(f"{t('csv_sale_qty', lang)},{result.qty_sold:g}")
    lines.append(f"{t('metric_proceeds', lang)} (HUF),{result.proceeds_huf:,.0f}")
    lines.append(f"{t('metric_avg_cost', lang)} (HUF),{result.avg_cost_per_share_huf:,.2f}")
    lines.append(f"{t('metric_cogs', lang)} (HUF),{result.cogs_huf:,.0f}")
    lines.append(f"{t('metric_fees', lang)} (HUF),{result.fees_huf:,.0f}")
    lines.append(f"{t('metric_gross_gain', lang)} (HUF),{result.gross_gain_huf:,.0f}")
    lines.append(f"SZJA (HUF),{result.szja:,.0f}")
    lines.append(f"SZOCHO (HUF),{result.szocho:,.0f}")
    lines.append(f"{t('metric_total_tax', lang)} (HUF),{result.total_tax:,.0f}")
    lines.append("")
    lines.append("date,ticker,qty,price_native,fx_rate_huf,cost_huf")
    for _, row in lots.iterrows():
        cost = row["qty"] * row["price"] * row["fx_rate"]
        lines.append(
            f"{row['date']},{row['ticker']},{row['qty']:g},"
            f"{row['price']:.4f},{row['fx_rate']:.4f},{cost:,.0f}"
        )
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Section 1: vesting lots
# ---------------------------------------------------------------------------
st.subheader(t("sec1_title", lang))

edited = st.data_editor(
    st.session_state.lots,
    column_config={
        "date": st.column_config.DateColumn(
            t("col_vest_date", lang), format="YYYY-MM-DD", required=True
        ),
        "ticker": st.column_config.SelectboxColumn(
            t("col_ticker", lang), options=list(SECURITIES), required=True,
            help=t("ticker_help", lang),
        ),
        "qty": st.column_config.NumberColumn(t("col_qty", lang), min_value=0.0, required=True),
        "price": st.column_config.NumberColumn(
            t("col_price", lang), min_value=0.0,
            help=t("price_help", lang),
        ),
        "fx_rate": st.column_config.NumberColumn(
            t("col_fx_rate", lang), min_value=0.0,
            help=t("fx_help", lang),
        ),
    },
    num_rows="dynamic",
)
st.caption(t("lot_help", lang))
st.session_state.lots = edited

if st.button(t("fetch_lots_button", lang)):
    lots = st.session_state.lots.copy()
    fetch_issues: list[str] = []
    for idx, row in lots.iterrows():
        sec = SECURITIES[row["ticker"]]
        try:
            quote = df.get_stock_price(
                sec.yahoo_ticker, row["date"],
                divisor=sec.price_divisor, adr_ratio=sec.adr_ratio,
                lang=lang,
            )
            lots.at[idx, "price"] = round(quote.value, 4)
        except ValueError as exc:
            fetch_issues.append(
                t("lot_error", lang).format(num=idx + 1, ticker=row["ticker"], msg=exc)
            )
        try:
            rate = df.get_exchange_rate(sec.currency, row["date"], lang=lang)
            lots.at[idx, "fx_rate"] = round(rate.value, 4)
        except ValueError as exc:
            fetch_issues.append(
                t("lot_error", lang).format(num=idx + 1, ticker=row["ticker"], msg=exc)
            )
    st.session_state.lots = lots
    if fetch_issues:
        for issue in fetch_issues:
            st.warning(issue)
    else:
        st.success(t("fetch_success", lang))

lots = st.session_state.lots

if (lots["price"] > 0).any() and (lots["fx_rate"] > 0).any():
    preview = lots.copy()
    preview["cost_huf"] = (
        preview["price"] * preview["fx_rate"] * preview["qty"]
    ).where(preview["price"] > 0, None)
    preview["cost_huf"] = preview["cost_huf"].round(0)
    st.dataframe(
        preview.rename(
            columns={
                "date": t("col_vest_date", lang),
                "ticker": t("col_ticker", lang),
                "qty": t("col_qty", lang),
                "price": t("col_price", lang),
                "fx_rate": t("col_fx_rate", lang),
                "cost_huf": t("col_cost_huf", lang),
            }
        ),
        hide_index=True,
        width="stretch",
    )

# ---------------------------------------------------------------------------
# Section 2: the sale
# ---------------------------------------------------------------------------
st.subheader(t("sec2_title", lang))

sale_date = st.date_input(t("sale_date", lang), value=date.today())
sale_ticker = st.selectbox(t("ticker_sold", lang), list(SECURITIES))
sale_qty = st.number_input(t("qty_sold", lang), min_value=0.0, value=0.0)

c_price, c_rate = st.columns(2)
if "sale_price" not in st.session_state:
    st.session_state.sale_price = 0.0
if "sale_rate" not in st.session_state:
    st.session_state.sale_rate = 0.0
sale_price = c_price.number_input(
    t("sale_price", lang), min_value=0.0, key="sale_price",
    help=t("sale_price_help", lang),
)
sale_rate = c_rate.number_input(
    t("sale_rate", lang), min_value=0.0, key="sale_rate",
    help=t("sale_rate_help", lang),
)
fees_huf = st.number_input(t("fees", lang), min_value=0.0, value=0.0)

def _fetch_sale_callback(ticker, on_date, lang):
    sec = SECURITIES[ticker]
    infos: list[str] = []
    issues: list[str] = []
    try:
        quote = df.get_stock_price(
            sec.yahoo_ticker, on_date,
            divisor=sec.price_divisor, adr_ratio=sec.adr_ratio,
            lang=lang,
        )
        st.session_state.sale_price = round(quote.value, 4)
        infos.append(
            t("price_used", lang).format(
                price=f"{quote.value:.4f}", currency=sec.currency, date=quote.date
            )
        )
    except ValueError as exc:
        issues.append(str(exc))
    try:
        rate = df.get_exchange_rate(sec.currency, on_date, lang=lang)
        st.session_state.sale_rate = round(rate.value, 4)
        infos.append(
            t("fx_used", lang).format(
                rate=f"{rate.value:.2f}", currency=sec.currency, date=rate.date
            )
        )
    except ValueError as exc:
        issues.append(str(exc))
    st.session_state._sale_fetch_infos = infos
    st.session_state._sale_fetch_issues = issues


st.button(
    t("fetch_sale_button", lang),
    on_click=_fetch_sale_callback,
    args=(sale_ticker, sale_date, lang),
)

for msg in st.session_state.pop("_sale_fetch_infos", []):
    st.info(msg)
for msg in st.session_state.pop("_sale_fetch_issues", []):
    st.warning(msg)

# ---------------------------------------------------------------------------
# Section 3: calculation
# ---------------------------------------------------------------------------
st.subheader(t("sec3_title", lang))

if st.button(t("calculate_button", lang), type="primary"):
    valid = lots[lots["qty"] > 0].copy()
    if valid.empty:
        st.error(t("err_no_lots", lang))
    elif sale_qty <= 0:
        st.error(t("err_no_qty", lang))
    else:
        missing = valid[(valid["price"] <= 0) | (valid["fx_rate"] <= 0)]
        if not missing.empty:
            st.error(t("err_missing_data", lang))
        else:
            vest_lots = [
                tc.VestingLot(
                    date=row["date"], ticker=row["ticker"], qty=row["qty"],
                    price_native=row["price"], rate_huf=row["fx_rate"],
                )
                for _, row in valid.iterrows()
            ]
            sale = tc.Sale(
                date=sale_date, ticker=sale_ticker, qty=sale_qty,
                price_native=sale_price, rate_huf=sale_rate, fees_huf=fees_huf,
            )
            try:
                result = tc.calculate_sale_tax(
                    vest_lots, sale,
                    szja_rate=szja_rate, szocho_rate=szocho_rate,
                    apply_szocho=apply_szocho, lang=lang,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("metric_proceeds", lang), f"{result.proceeds_huf:,.0f} HUF")
                m2.metric(t("metric_avg_cost", lang), f"{result.avg_cost_per_share_huf:,.0f} HUF")
                m3.metric(t("metric_cogs", lang), f"{result.cogs_huf:,.0f} HUF")
                m4.metric(t("metric_fees", lang), f"{result.fees_huf:,.0f} HUF")

                m5, m6, m7 = st.columns(3)
                m5.metric(
                    t("metric_gross_gain", lang),
                    f"{result.gross_gain_huf:,.0f} HUF",
                    delta_color="off",
                )
                m6.metric(t("metric_szja", lang), f"{result.szja:,.0f} HUF")
                m7.metric(t("metric_szocho", lang), f"{result.szocho:,.0f} HUF")

                pct = tc.tax_as_percent_of_gain(result.total_tax, result.gross_gain_huf)
                st.metric(
                    t("metric_total_tax", lang),
                    f"{result.total_tax:,.0f} HUF",
                    delta=t("pct_of_gain", lang).format(pct=pct) if pct is not None else None,
                )

                for warning in result.warnings:
                    st.warning(warning)

                st.download_button(
                    t("download_button", lang),
                    data=_build_csv(valid, result, lang),
                    file_name="wise_rsu_tax.csv",
                    mime="text/csv",
                )

st.caption(t("disclaimer", lang))
