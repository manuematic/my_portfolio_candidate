"""Constants for Börsenkandidaten integration."""

DOMAIN = "boersen_kandidat"
NAME = "Börsenkandidaten"

# Storage
STORAGE_KEY = f"{DOMAIN}.kandidaten"
STORAGE_VERSION = 1

# Config keys
CONF_LISTE_NAME = "liste_name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DATA_SOURCE = "data_source"
DEFAULT_SCAN_INTERVAL = 15  # minutes

# Data sources
SOURCE_ING   = "ing"
SOURCE_YAHOO = "yahoo_finance"
DEFAULT_SOURCE = SOURCE_ING

# Börsenzeiten (MESZ = UTC+2)
BOERSE_START_HOUR = 9    # 09:00 MESZ
BOERSE_END_HOUR   = 20   # 20:00 MESZ

# Kandidat attribute keys
ATTR_BEZEICHNUNG     = "bezeichnung"
ATTR_KUERZEL         = "kuerzel"
ATTR_WKN             = "wkn"
ATTR_ISIN            = "isin"
ATTR_ZIELKURS        = "zielkurs"          # Kauf-Zielkurs (Alarm bei Unterschreitung)
ATTR_DATENQUELLE     = "datenquelle"
ATTR_AKTUELLER_KURS  = "aktueller_kurs"
ATTR_DIFFERENZ_ABS   = "differenz_abs"     # aktueller_kurs - zielkurs
ATTR_DIFFERENZ_PCT   = "differenz_pct"     # differenz in %
ATTR_KURS_VORTAG     = "kurs_vortag"
ATTR_TAGES_ABS       = "tages_aenderung_abs"
ATTR_TAGES_PCT       = "tages_aenderung_pct"
ATTR_KURS_UNTERSCHRITTEN = "kurs_unterschritten"  # bool – Alarmierungsentität

# Platforms
PLATFORMS = ["sensor", "binary_sensor"]

# Yahoo Finance JSON-API
YAHOO_API_HOSTS = [
    "query1.finance.yahoo.com",
    "query2.finance.yahoo.com",
]

# Gemeinsame HTTP-Headers
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
    "Referer": "https://finance.yahoo.com/",
}
