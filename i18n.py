"""Language Flipper. Pretty lightweight

The calculator and fetchers emit user-facing strings too (warnings, "no data"
errors), so they also look up translations here. The default language is
English, which keeps the offline smoke tests unchanged.
"""

LANGUAGES = {"en": "English", "hu": "Magyar"}

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "Wise HU RSU Tax Calculator",
        "app_subtitle": (
            "SZJA + SZOCHO due on capital gains when selling vested Wise "
            "shares. Prices: Yahoo Finance. FX: official MNB daily rates."
        ),
        "settings": "Settings",
        "language": "Language / Nyelv",
        "szja_rate": "SZJA rate",
        "szocho_rate": "SZOCHO rate",
        "apply_szocho_label": "Apply SZOCHO (13%)",
        "apply_szocho_help": (
            "Wise shares sold on a regulated exchange (Nasdaq/LSE) via a "
            "broker are a controlled capital market transaction: 15% SZJA "
            "only, no SZOCHO. Tick this only if your sale does not qualify. "
            "When it applies, SZOCHO is capped at 24x the monthly minimum "
            "wage (about {cap} HUF in 2026)."
        ),
        "disclaimer": (
            "This tool is only for informational purposes only and shall not "
            "be considered professional tax advice. The creator of this "
            "application does not bear responsibility for your tax returns "
            "accuracy. If unsure, consult with NAV or a certified professional."
        ),
        "donate_title": "Support this app",
        "donate_body": (
            "If this app has been useful and you would like to express your "
            "gratitude, you can donate to my Wise account: @kristofk178"
        ),
        "sec1_title": "1. Vesting lots",
        "lot_help": (
            "One row per vesting event. Ticker WISE = GBP (LSE), WSE = USD "
            "(Nasdaq). Leave price/FX blank or at 0, then press 'Fetch prices "
            "& FX rates'. You can also type values manually (e.g. when Yahoo "
            "has no history)."
        ),
        "col_vest_date": "Vest date",
        "col_ticker": "Ticker",
        "col_qty": "Qty",
        "col_price": "Price (native)",
        "col_fx_rate": "MNB rate (HUF/unit)",
        "ticker_help": "WISE = ordinary shares (GBP), WSE = US ADR (USD).",
        "price_help": "Auto-filled from Yahoo; override if needed. WISE price is in GBP.",
        "fx_help": "Official MNB rate, HUF per 1 unit of the ticker currency.",
        "fetch_lots_button": "Fetch prices & FX rates for vesting lots",
        "fetch_success": "Fetched prices and FX rates for all lots.",
        "col_cost_huf": "Cost basis (HUF)",
        "sec2_title": "2. Sale",
        "sale_date": "Sale date",
        "ticker_sold": "Ticker sold",
        "qty_sold": "Quantity sold",
        "sale_price": "Sale price (native)",
        "sale_price_help": (
            "Auto-filled from Yahoo; override with your actual execution price "
            "if known."
        ),
        "sale_rate": "MNB rate at sale (HUF/unit)",
        "sale_rate_help": "Official MNB rate on the sale date.",
        "fees": "Broker fees (HUF)",
        "fetch_sale_button": "Fetch sale price & FX rate",
        "price_used": "Price used: {price} {currency} on {date}.",
        "fx_used": "FX rate used: {rate} HUF/{currency} on {date}.",
        "sec3_title": "3. Tax due",
        "calculate_button": "Calculate tax",
        "err_no_lots": "Add at least one vesting lot with a positive quantity.",
        "err_no_qty": "Enter a positive quantity sold.",
        "err_missing_data": (
            "Some vesting lots are missing a price or FX rate. Fetch them or "
            "type them in manually."
        ),
        "err_no_lots_ticker": "No vesting lots found for ticker {ticker}",
        "err_sell_exceeds": "Cannot sell {qty:g} shares of {ticker}: only {held:g} shares vested.",
        "err_negative_qty": "Sale quantity must be non-negative.",
        "metric_proceeds": "Sale proceeds",
        "metric_avg_cost": "Avg cost / share",
        "metric_cogs": "Cost of goods sold",
        "metric_fees": "Broker fees",
        "metric_gross_gain": "Gross gain",
        "metric_szja": "SZJA",
        "metric_szocho": "SZOCHO",
        "metric_total_tax": "Total tax due",
        "pct_of_gain": "{pct:.1f}% of gain",
        "download_button": "Download breakdown (CSV)",
        "csv_title": "Wise HU RSU tax calculation",
        "csv_sale_qty": "Quantity sold",
        "warn_loss": (
            "Capital loss of {amount:,.0f} HUF. No tax is due on a loss; it "
            "may be used to offset other capital gains in your annual SZJA "
            "filing."
        ),
        "warn_szocho_not_applied": (
            "SZOCHO was not applied: shares sold on a regulated exchange via "
            "a broker are a controlled capital market transaction, taxed at "
            "15% SZJA only. Tick 'Apply SZOCHO' only if your sale does not "
            "qualify."
        ),
        "yahoo_no_data_around": "No Yahoo Finance data found for {ticker} around {date}",
        "yahoo_no_data_before": "No Yahoo Finance data found for {ticker} at or before {date}",
        "mnb_no_data_around": "No MNB rate found for {currency} around {date}",
        "mnb_no_data_before": "No MNB rate found for {currency} at or before {date}",
        "lot_error": "Lot {num} ({ticker}): {msg}",
    },
    "hu": {
        "app_title": "Wise RSU Adókalkulátor",
        "app_subtitle": (
            "A megszerzett Wise részvények eladásakor keletkező tőkenyereség "
            "után fizetendő SZJA + SZOCHO. Részvényárfolyam: Yahoo Finance. "
            "Devizaárfolyam: hivatalos MNB napi árfolyam."
        ),
        "settings": "Beállítások",
        "language": "Nyelv / Language",
        "szja_rate": "SZJA kulcs",
        "szocho_rate": "SZOCHO kulcs",
        "apply_szocho_label": "SZOCHO alkalmazása (13%)",
        "apply_szocho_help": (
            "A Wise részvények szabályozott tőzsdén (Nasdaq/LSE), közvetítőn "
            "keresztül történő eladása ellenőrzött tőkepiaci ügylet: csak "
            "15% SZJA, SZOCHO nélkül. Ezt csak akkor pipáld be, ha az "
            "ügyleted nem minősül ilyennek. Alkalmazás esetén a SZOCHO a "
            "havi minimálbér 24-szereséig (2026-ban kb. {cap} HUF) fizetendő."
        ),
        "disclaimer": (
            "Ez az eszköz csak tájékoztatási célokat szolgál, és nem "
            "tekinthető hivatalos adótanácsadásnak. Az alkalmazás készítője "
            "nem vállal felelősséget az adóbevallásod pontosságáért. Ha "
            "bizonytalan vagy, fordulj a NAV-hoz vagy okleveles "
            "szakemberhez."
        ),
        "donate_title": "Támogasd az alkalmazást",
        "donate_body": (
            "Ha hasznosnak találtad ezt az alkalmazást, és köszönetedet "
            "szeretnéd kifejezni, adományozhatsz a Wise fiókomra: @kristofk178"
        ),
        "sec1_title": "1. Megszerzett részvények (vesting)",
        "lot_help": (
            "Soronként egy vesting esemény. Ticker WISE = GBP (LSE), WSE = "
            "USD (Nasdaq). Az ár/árfolyam mezőket hagyd üresen vagy 0-n, majd "
            "kattints az 'Árak és árfolyamok lekérése' gombra. Az értékeket "
            "kézzel is megadhatod (pl. ha a Yahoo-nak nincs története)."
        ),
        "col_vest_date": "Vest dátuma",
        "col_ticker": "Ticker",
        "col_qty": "Mennyiség",
        "col_price": "Ár (devizában)",
        "col_fx_rate": "MNB árfolyam (HUF/egység)",
        "ticker_help": "WISE = törzsrészvények (GBP), WSE = US ADR (USD).",
        "price_help": "Automatikusan kitölti a Yahoo; szükség esetén felülírható. A WISE ára GBP-ben van.",
        "fx_help": "Hivatalos MNB árfolyam, HUF / 1 egység a ticker devizájában.",
        "fetch_lots_button": "Árak és árfolyamok lekérése a vestingekhez",
        "fetch_success": "Az árak és árfolyamok lekérése sikeres volt.",
        "col_cost_huf": "Költség (HUF)",
        "sec2_title": "2. Eladás",
        "sale_date": "Eladás dátuma",
        "ticker_sold": "Eladott ticker",
        "qty_sold": "Eladott mennyiség",
        "sale_price": "Eladási ár (devizában)",
        "sale_price_help": (
            "Automatikusan kitölti a Yahoo; felülírhatod a tényleges "
            "kötési árral, ha ismert."
        ),
        "sale_rate": "MNB árfolyam eladáskor (HUF/egység)",
        "sale_rate_help": "Hivatalos MNB árfolyam az eladás napján.",
        "fees": "Közvetítői díjak (HUF)",
        "fetch_sale_button": "Eladási ár és árfolyam lekérése",
        "price_used": "Felhasznált ár: {price} {currency} ({date}).",
        "fx_used": "Felhasznált árfolyam: {rate} HUF/{currency} ({date}).",
        "sec3_title": "3. Fizetendő adó",
        "calculate_button": "Adó kiszámítása",
        "err_no_lots": "Adj meg legalább egy vesting sort pozitív mennyiséggel.",
        "err_no_qty": "Adj meg pozitív eladott mennyiséget.",
        "err_missing_data": (
            "Néhány vesting sornál hiányzik az ár vagy az árfolyam. Töltsd le "
            "őket, vagy add meg kézzel."
        ),
        "err_no_lots_ticker": "Nem található vesting sor ehhez a tickerhez: {ticker}",
        "err_sell_exceeds": "Nem adható el {qty:g} részvény ({ticker}): csak {held:g} részvény vestingelt.",
        "err_negative_qty": "Az eladott mennyiség nem lehet negatív.",
        "metric_proceeds": "Eladási bevétel",
        "metric_avg_cost": "Átlagköltség / részvény",
        "metric_cogs": "Eladott részvények költsége",
        "metric_fees": "Közvetítői díjak",
        "metric_gross_gain": "Nyereség",
        "metric_szja": "SZJA",
        "metric_szocho": "SZOCHO",
        "metric_total_tax": "Fizetendő adó",
        "pct_of_gain": "{pct:.1f}% a nyereségből",
        "download_button": "Összesítés letöltése (CSV)",
        "csv_title": "Wise RSU adókalkuláció",
        "csv_sale_qty": "Eladott mennyiség",
        "warn_loss": (
            "{amount:,.0f} HUF tőkeveszteség. Veszteség után nem kell adót "
            "fizetni; más tőkenyereség ellentételezésére használható az éves "
            "SZJA-bevallásban."
        ),
        "warn_szocho_not_applied": (
            "A SZOCHO nem került alkalmazásra: a szabályozott tőzsdén, "
            "közvetítőn keresztül eladott részvények ellenőrzött tőkepiaci "
            "ügyletnek minősülnek, amelyre csak 15% SZJA vonatkozik. A "
            "'SZOCHO alkalmazása' opciót csak akkor pipáld be, ha az "
            "ügyleted nem minősül ilyennek."
        ),
        "yahoo_no_data_around": "Nem található Yahoo Finance adat ehhez: {ticker} ({date} körül)",
        "yahoo_no_data_before": "Nem található Yahoo Finance adat ehhez: {ticker} ({date} vagy korábban)",
        "mnb_no_data_around": "Nem található MNB árfolyam ehhez: {currency} ({date} körül)",
        "mnb_no_data_before": "Nem található MNB árfolyam ehhez: {currency} ({date} vagy korábban)",
        "lot_error": "{num}. sor ({ticker}): {msg}",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Return the translation for ``key`` in ``lang`` (falls back to EN)."""
    table = STRINGS.get(lang, STRINGS["en"])
    return table.get(key, STRINGS["en"].get(key, key))


def loss_warning(amount: float, lang: str = "en") -> str:
    return t("warn_loss", lang).format(amount=abs(amount))


def szocho_warning(lang: str = "en") -> str:
    return t("warn_szocho_not_applied", lang)


def no_data_message(kind: str, name: str, date_str: str, lang: str = "en") -> str:
    """Build a 'no data' error message for stock prices or FX rates.

    ``kind`` is one of {"yahoo_around", "yahoo_before", "mnb_around",
    "mnb_before"}.
    """
    keys = {
        "yahoo_around": "yahoo_no_data_around",
        "yahoo_before": "yahoo_no_data_before",
        "mnb_around": "mnb_no_data_around",
        "mnb_before": "mnb_no_data_before",
    }
    return t(keys[kind], lang).format(ticker=name, currency=name, date=date_str)
