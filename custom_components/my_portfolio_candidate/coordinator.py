"""DataUpdateCoordinator für My Portfolio Candidate."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOURCE,
    SOURCE_ING,
    SOURCE_YAHOO,
    CONF_DATA_SOURCE,
    BOERSE_START_HOUR,
    BOERSE_END_HOUR,
    ATTR_BEZEICHNUNG,
    ATTR_KUERZEL,
    ATTR_WKN,
    ATTR_ISIN,
    ATTR_ZIELKURS,
    ATTR_DATENQUELLE,
    ATTR_AKTUELLER_KURS,
    ATTR_DIFFERENZ_ABS,
    ATTR_DIFFERENZ_PCT,
    ATTR_KURS_VORTAG,
    ATTR_TAGES_ABS,
    ATTR_TAGES_PCT,
    ATTR_KURS_UNTERSCHRITTEN,
)
from .yahoo_finance import fetch_price_yahoo
from .ing import fetch_price_ing

_LOGGER = logging.getLogger(__name__)

# MESZ = UTC+2 (Sommerzeit), MEZ = UTC+1 (Winterzeit)
# HA liefert datetime.now(timezone.utc) – wir vergleichen mit lokaler Stunde
_MESZ = timezone(timedelta(hours=2))


def _is_boersenzeit() -> bool:
    """Prüft ob aktuell Börsenzeit (09:00–20:00 MESZ)."""
    now_mesz = datetime.now(_MESZ)
    return BOERSE_START_HOUR <= now_mesz.hour < BOERSE_END_HOUR


class MyPortfolioCandidateCoordinator(DataUpdateCoordinator):
    """Coordinator: Kurse abrufen und Kandidaten-Daten verwalten."""

    def __init__(
        self,
        hass: HomeAssistant,
        liste_name: str,
        entry_id: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        data_source: str = DEFAULT_SOURCE,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=timedelta(minutes=scan_interval),
        )
        self.liste_name = liste_name
        self.entry_id = entry_id
        self.data_source = data_source
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}")
        self._kandidaten: dict[str, dict] = {}
        self._session: aiohttp.ClientSession | None = None

    async def async_setup(self) -> None:
        """Gespeicherte Kandidaten-Daten laden."""
        stored = await self._store.async_load()
        if stored and "kandidaten" in stored:
            self._kandidaten = stored["kandidaten"]
        _LOGGER.debug(
            "Kandidatenliste '%s' geladen – %d Einträge, Quelle: %s",
            self.liste_name, len(self._kandidaten), self.data_source,
        )

    async def _fetch_price(self, kandidat: dict) -> dict:
        """Kurs abrufen – ING primär (via ISIN), Yahoo als Fallback."""
        quelle = kandidat.get(ATTR_DATENQUELLE) or self.data_source

        if quelle == SOURCE_ING:
            isin = (kandidat.get(ATTR_ISIN) or "").strip()
            if isin:
                return await fetch_price_ing(self._session, isin)
            _LOGGER.warning(
                "ING gewählt aber kein ISIN für '%s' – Fallback auf Yahoo",
                kandidat.get(ATTR_KUERZEL, "?"),
            )

        # Yahoo Finance (Fallback oder explizit gewählt)
        return await fetch_price_yahoo(self._session, kandidat.get(ATTR_KUERZEL, ""))

    async def _async_update_data(self) -> dict[str, dict]:
        """Aktuelle Kurse für alle Kandidaten abrufen – nur zu Börsenzeiten."""
        if not self._kandidaten:
            return {}

        # Außerhalb Börsenzeiten: letzte bekannte Daten zurückgeben ohne API-Aufruf
        if not _is_boersenzeit():
            _LOGGER.debug("Außerhalb Börsenzeiten – kein Kursabruf")
            return self.data or {}

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        updated_data: dict[str, dict] = {}

        for kid_id, kandidat in self._kandidaten.items():
            price_data = await self._fetch_price(kandidat)
            aktueller_kurs = price_data.get("aktueller_kurs")

            # Letzten bekannten Kurs behalten wenn Abruf fehlschlägt
            if aktueller_kurs is None and self.data:
                aktueller_kurs = self.data.get(kid_id, {}).get(ATTR_AKTUELLER_KURS)

            kid_data = dict(kandidat)
            kid_data[ATTR_AKTUELLER_KURS] = aktueller_kurs
            kid_data[ATTR_KURS_VORTAG]    = price_data.get("kurs_vortag")          or (self.data or {}).get(kid_id, {}).get(ATTR_KURS_VORTAG)
            kid_data[ATTR_TAGES_ABS]      = price_data.get("tages_aenderung_abs")  or (self.data or {}).get(kid_id, {}).get(ATTR_TAGES_ABS)
            kid_data[ATTR_TAGES_PCT]      = price_data.get("tages_aenderung_pct")  or (self.data or {}).get(kid_id, {}).get(ATTR_TAGES_PCT)

            zielkurs = kandidat.get(ATTR_ZIELKURS)

            # ── Differenz zum Zielkurs ────────────────────────────────────
            if aktueller_kurs is not None and zielkurs and float(zielkurs) > 0:
                diff_abs = round(aktueller_kurs - float(zielkurs), 4)
                diff_pct = round(diff_abs / float(zielkurs) * 100.0, 2)
                kid_data[ATTR_DIFFERENZ_ABS] = diff_abs
                kid_data[ATTR_DIFFERENZ_PCT] = diff_pct
            else:
                kid_data[ATTR_DIFFERENZ_ABS] = None
                kid_data[ATTR_DIFFERENZ_PCT] = None

            # ── Kurs unterschritten? ──────────────────────────────────────
            if aktueller_kurs is not None and zielkurs and float(zielkurs) > 0:
                kid_data[ATTR_KURS_UNTERSCHRITTEN] = bool(aktueller_kurs <= float(zielkurs))
            else:
                kid_data[ATTR_KURS_UNTERSCHRITTEN] = False

            updated_data[kid_id] = kid_data

        return updated_data

    # ── Kandidaten-Verwaltung ──────────────────────────────────────────────

    def get_kandidaten(self) -> dict[str, dict]:
        return self._kandidaten

    async def async_add_kandidat(self, kid_data: dict) -> str:
        kid_id = str(uuid.uuid4())
        self._kandidaten[kid_id] = kid_data
        await self._async_save()
        await self.async_request_refresh()
        return kid_id

    async def async_update_kandidat(self, kid_id: str, kid_data: dict) -> None:
        if kid_id not in self._kandidaten:
            raise ValueError(f"Kandidat {kid_id} nicht gefunden")
        self._kandidaten[kid_id].update(kid_data)
        await self._async_save()
        await self.async_request_refresh()

    async def async_remove_kandidat(self, kid_id: str) -> None:
        self._kandidaten.pop(kid_id, None)
        await self._async_save()

    async def _async_save(self) -> None:
        await self._store.async_save({"kandidaten": self._kandidaten})

    async def async_shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
