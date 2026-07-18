"""Config flow + Options-Flow für My Portfolio Candidate."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_LISTE_NAME,
    CONF_SCAN_INTERVAL,
    CONF_DATA_SOURCE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOURCE,
    SOURCE_ING,
    SOURCE_YAHOO,
    ATTR_BEZEICHNUNG,
    ATTR_DATENQUELLE,
    ATTR_WKN,
    ATTR_ISIN,
    ATTR_KUERZEL,
    ATTR_ZIELKURS,
    ATTR_NOTIZ,
    ATTR_MEMO_ZIELKURS,
    ATTR_MEMO_STOPPKURS,
    NOTIZ_MAX_LEN,
)

_LOGGER = logging.getLogger(__name__)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _source_label(source: str) -> str:
    return {
        SOURCE_ING:   "ING (via ISIN – primär, DE & internationale Aktien)",
        SOURCE_YAHOO: "Yahoo Finance (via Kürzel – Fallback, US-Aktien, ETFs)",
    }.get(source, source)


def _kandidat_schema(defaults: dict | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema({
        vol.Required(ATTR_BEZEICHNUNG, default=d.get(ATTR_BEZEICHNUNG, "")): selector.selector(
            {"text": {"type": "text"}}
        ),
        vol.Required(ATTR_KUERZEL, default=d.get(ATTR_KUERZEL, "")): selector.selector(
            {"text": {"type": "text"}}
        ),
        vol.Required(ATTR_DATENQUELLE, default=d.get(ATTR_DATENQUELLE, SOURCE_ING)): selector.selector({
            "select": {
                "options": [
                    {"value": SOURCE_ING,   "label": _source_label(SOURCE_ING)},
                    {"value": SOURCE_YAHOO, "label": _source_label(SOURCE_YAHOO)},
                ],
                "mode": "list",
            }
        }),
        vol.Optional(ATTR_WKN, default=d.get(ATTR_WKN, "")): selector.selector(
            {"text": {"type": "text"}}
        ),
        vol.Optional(ATTR_ISIN, default=d.get(ATTR_ISIN, "")): selector.selector(
            {"text": {"type": "text"}}
        ),
        vol.Required(ATTR_ZIELKURS, default=d.get(ATTR_ZIELKURS, 0.0)): selector.selector(
            {"number": {"min": 0, "max": 999999, "step": 0.001, "mode": "box"}}
        ),
        vol.Optional(ATTR_MEMO_ZIELKURS, default=d.get(ATTR_MEMO_ZIELKURS, 0.0)): selector.selector(
            {"number": {"min": 0, "max": 999999, "step": 0.001, "mode": "box"}}
        ),
        vol.Optional(ATTR_MEMO_STOPPKURS, default=d.get(ATTR_MEMO_STOPPKURS, 0.0)): selector.selector(
            {"number": {"min": 0, "max": 999999, "step": 0.001, "mode": "box"}}
        ),
        vol.Optional(ATTR_NOTIZ, default=d.get(ATTR_NOTIZ, "")): selector.selector(
            {"text": {"type": "text"}}
        ),
    })


def _current_options(config_entry) -> dict:
    return {
        CONF_SCAN_INTERVAL: config_entry.options.get(
            CONF_SCAN_INTERVAL,
            config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        ),
        CONF_DATA_SOURCE: config_entry.options.get(
            CONF_DATA_SOURCE,
            config_entry.data.get(CONF_DATA_SOURCE, DEFAULT_SOURCE),
        ),
    }


# ── Config Flow (Ersteinrichtung) ─────────────────────────────────────────────

class MyPortfolioCandidateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Erstellt eine neue Kandidatenliste."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            liste_name = user_input[CONF_LISTE_NAME].strip()
            if not liste_name:
                errors[CONF_LISTE_NAME] = "invalid_name"
            else:
                await self.async_set_unique_id(liste_name.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=liste_name,
                    data={
                        CONF_LISTE_NAME:   liste_name,
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_DATA_SOURCE:  user_input.get(CONF_DATA_SOURCE, DEFAULT_SOURCE),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LISTE_NAME, default="Meine Purchase Candidates"): selector.selector(
                    {"text": {"type": "text"}}
                ),
                vol.Required(CONF_DATA_SOURCE, default=DEFAULT_SOURCE): selector.selector({
                    "select": {
                        "options": [
                            {"value": SOURCE_ING,   "label": _source_label(SOURCE_ING)},
                            {"value": SOURCE_YAHOO, "label": _source_label(SOURCE_YAHOO)},
                        ],
                        "mode": "list",
                    }
                }),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): selector.selector(
                    {"number": {"min": 1, "max": 1440, "step": 1, "mode": "box",
                                "unit_of_measurement": "min"}}
                ),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "MyPortfolioCandidateOptionsFlow":
        return MyPortfolioCandidateOptionsFlow()


# ── Options Flow (Kandidaten-Verwaltung) ──────────────────────────────────────

class MyPortfolioCandidateOptionsFlow(config_entries.OptionsFlow):
    """Mehrstufiges Menü: Kandidaten verwalten + Einstellungen."""

    def __init__(self) -> None:
        self._selected_kid_id: str | None = None

    # ── Hauptmenü ─────────────────────────────────────────────────────────

    async def async_step_init(self, user_input=None):
        coordinator = self._get_coordinator()
        kandidaten = coordinator.get_kandidaten() if coordinator else {}

        kid_lines = []
        for k in kandidaten.values():
            bezeichnung = k.get(ATTR_BEZEICHNUNG, "").strip()
            label = f"{bezeichnung} ({k.get(ATTR_KUERZEL, '?')})" if bezeichnung else k.get(ATTR_KUERZEL, "?")
            ziel = k.get(ATTR_ZIELKURS, "–")
            kid_lines.append(f"• {label}  —  Ziel: {ziel}")
        overview = "\n".join(kid_lines) if kid_lines else "–"

        if user_input is not None:
            action = user_input.get("action")
            if action == "add":
                return await self.async_step_add_kandidat()
            if action == "edit":
                return await self.async_step_select_kandidat()
            if action == "settings":
                return await self.async_step_settings()

        actions = [selector.SelectOptionDict(value="add", label="➕ Kandidat hinzufügen")]
        if kandidaten:
            actions.append(selector.SelectOptionDict(value="edit", label="✏️  Kandidat bearbeiten / löschen"))
        actions.append(selector.SelectOptionDict(value="settings", label="⚙️  Einstellungen"))

        return self.async_show_form(
            step_id="init",
            description_placeholders={"overview": overview},
            data_schema=vol.Schema({
                vol.Required("action"): selector.selector(
                    {"select": {"options": actions, "mode": "list"}}
                )
            }),
        )

    # ── Kandidat hinzufügen ───────────────────────────────────────────────

    async def async_step_add_kandidat(self, user_input=None):
        errors: dict[str, str] = {}
        coordinator = self._get_coordinator()

        if user_input is not None:
            kuerzel = str(user_input.get(ATTR_KUERZEL, "")).strip().upper()
            isin    = str(user_input.get(ATTR_ISIN, "")).strip().upper()
            quelle  = user_input.get(ATTR_DATENQUELLE, SOURCE_ING)
            notiz   = str(user_input.get(ATTR_NOTIZ, "")).strip()

            if not kuerzel:
                errors[ATTR_KUERZEL] = "invalid_kuerzel"
            elif quelle == SOURCE_ING and not isin:
                errors[ATTR_ISIN] = "isin_required"
            elif len(notiz) > NOTIZ_MAX_LEN:
                errors[ATTR_NOTIZ] = "notiz_too_long"
            else:
                kid_data = self._build_kandidat_data(user_input, kuerzel, isin)
                if coordinator:
                    await coordinator.async_add_kandidat(kid_data)
                return self.async_create_entry(title="", data=_current_options(self.config_entry))

        return self.async_show_form(
            step_id="add_kandidat",
            data_schema=_kandidat_schema(),
            errors=errors,
        )

    # ── Kandidat auswählen ────────────────────────────────────────────────

    async def async_step_select_kandidat(self, user_input=None):
        coordinator = self._get_coordinator()
        kandidaten = coordinator.get_kandidaten() if coordinator else {}

        if not kandidaten:
            return await self.async_step_init()

        if user_input is not None:
            self._selected_kid_id = user_input.get("kid_id")
            action = user_input.get("action")
            if action == "edit":
                return await self.async_step_edit_kandidat()
            if action == "delete":
                return await self.async_step_confirm_delete()

        options = [
            selector.SelectOptionDict(
                value=kid_id,
                label=(
                    f"{k.get(ATTR_BEZEICHNUNG,'').strip() or k.get(ATTR_KUERZEL,'?')}"
                    f" ({k.get(ATTR_KUERZEL,'?')})  —  Ziel: {k.get(ATTR_ZIELKURS,'?')}"
                )
            )
            for kid_id, k in kandidaten.items()
        ]

        return self.async_show_form(
            step_id="select_kandidat",
            data_schema=vol.Schema({
                vol.Required("kid_id"): selector.selector(
                    {"select": {"options": options, "mode": "list"}}
                ),
                vol.Required("action"): selector.selector({
                    "select": {
                        "options": [
                            selector.SelectOptionDict(value="edit",   label="✏️  Bearbeiten"),
                            selector.SelectOptionDict(value="delete", label="🗑️  Löschen"),
                        ],
                        "mode": "list",
                    }
                }),
            }),
        )

    # ── Kandidat bearbeiten ───────────────────────────────────────────────

    async def async_step_edit_kandidat(self, user_input=None):
        errors: dict[str, str] = {}
        coordinator = self._get_coordinator()
        kandidaten = coordinator.get_kandidaten() if coordinator else {}
        kid = kandidaten.get(self._selected_kid_id or "", {})

        if user_input is not None:
            kuerzel = str(user_input.get(ATTR_KUERZEL, "")).strip().upper()
            isin    = str(user_input.get(ATTR_ISIN, "")).strip().upper()
            quelle  = user_input.get(ATTR_DATENQUELLE, SOURCE_ING)
            notiz   = str(user_input.get(ATTR_NOTIZ, "")).strip()

            if not kuerzel:
                errors[ATTR_KUERZEL] = "invalid_kuerzel"
            elif quelle == SOURCE_ING and not isin:
                errors[ATTR_ISIN] = "isin_required"
            elif len(notiz) > NOTIZ_MAX_LEN:
                errors[ATTR_NOTIZ] = "notiz_too_long"
            else:
                kid_data = self._build_kandidat_data(user_input, kuerzel, isin)
                if coordinator and self._selected_kid_id:
                    await coordinator.async_update_kandidat(self._selected_kid_id, kid_data)
                return self.async_create_entry(title="", data=_current_options(self.config_entry))

        return self.async_show_form(
            step_id="edit_kandidat",
            data_schema=_kandidat_schema(defaults=kid),
            description_placeholders={"kuerzel": kid.get(ATTR_KUERZEL, "?")},
            errors=errors,
        )

    # ── Löschen bestätigen ────────────────────────────────────────────────

    async def async_step_confirm_delete(self, user_input=None):
        coordinator = self._get_coordinator()
        kandidaten = coordinator.get_kandidaten() if coordinator else {}
        kid = kandidaten.get(self._selected_kid_id or "", {})
        kuerzel = kid.get(ATTR_KUERZEL, "?")

        if user_input is not None:
            if user_input.get("confirm") and coordinator and self._selected_kid_id:
                from homeassistant.helpers.entity_registry import async_get as async_get_er
                ent_reg = async_get_er(self.hass)
                # Sensor und Binary Sensor entfernen
                for suffix in ["_kurs", "_unterschritten"]:
                    entity_id = ent_reg.async_get_entity_id(
                        "sensor" if suffix == "_kurs" else "binary_sensor",
                        DOMAIN,
                        f"{self._selected_kid_id}{suffix}",
                    )
                    if entity_id:
                        ent_reg.async_remove(entity_id)
                await coordinator.async_remove_kandidat(self._selected_kid_id)
            return self.async_create_entry(title="", data=_current_options(self.config_entry))

        return self.async_show_form(
            step_id="confirm_delete",
            description_placeholders={"kuerzel": kuerzel},
            data_schema=vol.Schema({
                vol.Required("confirm", default=False): selector.selector({"boolean": {}})
            }),
        )

    # ── Einstellungen ─────────────────────────────────────────────────────

    async def async_step_settings(self, user_input=None):
        opts = _current_options(self.config_entry)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Required(CONF_DATA_SOURCE, default=opts[CONF_DATA_SOURCE]): selector.selector({
                    "select": {
                        "options": [
                            {"value": SOURCE_ING,   "label": _source_label(SOURCE_ING)},
                            {"value": SOURCE_YAHOO, "label": _source_label(SOURCE_YAHOO)},
                        ],
                        "mode": "list",
                    }
                }),
                vol.Required(CONF_SCAN_INTERVAL, default=opts[CONF_SCAN_INTERVAL]): selector.selector(
                    {"number": {"min": 1, "max": 1440, "step": 1, "mode": "box",
                                "unit_of_measurement": "min"}}
                ),
            }),
        )

    # ── Hilfsmethoden ─────────────────────────────────────────────────────

    def _get_coordinator(self):
        return self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)

    @staticmethod
    def _build_kandidat_data(user_input: dict, kuerzel: str, isin: str) -> dict:
        zielkurs = user_input.get(ATTR_ZIELKURS, 0.0)
        memo_zielkurs = user_input.get(ATTR_MEMO_ZIELKURS, 0.0)
        memo_stoppkurs = user_input.get(ATTR_MEMO_STOPPKURS, 0.0)
        return {
            ATTR_BEZEICHNUNG: str(user_input.get(ATTR_BEZEICHNUNG, "")).strip(),
            ATTR_DATENQUELLE: user_input.get(ATTR_DATENQUELLE, SOURCE_ING),
            ATTR_KUERZEL:     kuerzel,
            ATTR_WKN:         str(user_input.get(ATTR_WKN, "")).strip().upper(),
            ATTR_ISIN:        isin,
            ATTR_ZIELKURS:    round(float(zielkurs), 3) if zielkurs else 0.0,
            ATTR_NOTIZ:           str(user_input.get(ATTR_NOTIZ, "")).strip()[:NOTIZ_MAX_LEN],
            ATTR_MEMO_ZIELKURS:   round(float(memo_zielkurs), 3) if memo_zielkurs else 0.0,
            ATTR_MEMO_STOPPKURS:  round(float(memo_stoppkurs), 3) if memo_stoppkurs else 0.0,
        }
