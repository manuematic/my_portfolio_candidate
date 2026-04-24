"""Sensor-Platform für Börsenkandidaten – aktueller Kurs."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    NAME,
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
from .coordinator import BoersenKandidatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BoersenKandidatCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_ids: set[str] = set()

    @callback
    def _handle_coordinator_update() -> None:
        new_entities = []
        for kid_id in coordinator.get_kandidaten():
            if kid_id not in known_ids:
                known_ids.add(kid_id)
                new_entities.append(KandidatKursSensor(coordinator, entry, kid_id))
        if new_entities:
            async_add_entities(new_entities, update_before_add=True)

    for kid_id in coordinator.get_kandidaten():
        known_ids.add(kid_id)

    initial_entities = [
        KandidatKursSensor(coordinator, entry, kid_id)
        for kid_id in coordinator.get_kandidaten()
    ]
    async_add_entities(initial_entities, update_before_add=True)

    entry.async_on_unload(coordinator.async_add_listener(_handle_coordinator_update))


class KandidatKursSensor(CoordinatorEntity[BoersenKandidatCoordinator], SensorEntity):
    """Aktueller Kurs eines Börsenkandidaten."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "EUR"

    def __init__(
        self,
        coordinator: BoersenKandidatCoordinator,
        entry: ConfigEntry,
        kid_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._kid_id = kid_id
        self._attr_unique_id = f"{kid_id}_kurs"
        self._attr_name = self._display_name(coordinator.get_kandidaten().get(kid_id, {}))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"{NAME} – {coordinator.liste_name}",
            manufacturer="Börsenkandidaten",
            model="ING / Yahoo Finance",
            entry_type=DeviceEntryType.SERVICE,
        )

    @staticmethod
    def _display_name(kid: dict) -> str:
        bezeichnung = (kid.get(ATTR_BEZEICHNUNG) or "").strip()
        return bezeichnung if bezeichnung else kid.get(ATTR_KUERZEL, "Unbekannt")

    @property
    def _base(self) -> dict[str, Any]:
        return self.coordinator.get_kandidaten().get(self._kid_id, {})

    @property
    def _data(self) -> dict[str, Any]:
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.get(self._kid_id, {})

    @property
    def native_value(self) -> float | None:
        val = self._data.get(ATTR_AKTUELLER_KURS)
        return round(float(val), 4) if val is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        base, data = self._base, self._data
        return {
            "liste":              self.coordinator.liste_name,
            ATTR_DATENQUELLE:     base.get(ATTR_DATENQUELLE, ""),
            ATTR_BEZEICHNUNG:     base.get(ATTR_BEZEICHNUNG, ""),
            ATTR_KUERZEL:         base.get(ATTR_KUERZEL, ""),
            ATTR_WKN:             base.get(ATTR_WKN, ""),
            ATTR_ISIN:            base.get(ATTR_ISIN, ""),
            ATTR_ZIELKURS:        base.get(ATTR_ZIELKURS),
            ATTR_AKTUELLER_KURS:  data.get(ATTR_AKTUELLER_KURS),
            ATTR_DIFFERENZ_ABS:   data.get(ATTR_DIFFERENZ_ABS),
            ATTR_DIFFERENZ_PCT:   data.get(ATTR_DIFFERENZ_PCT),
            ATTR_KURS_UNTERSCHRITTEN: data.get(ATTR_KURS_UNTERSCHRITTEN, False),
            ATTR_KURS_VORTAG:     data.get(ATTR_KURS_VORTAG),
            ATTR_TAGES_ABS:       data.get(ATTR_TAGES_ABS),
            ATTR_TAGES_PCT:       data.get(ATTR_TAGES_PCT),
        }

    @property
    def icon(self) -> str:
        if self._data.get(ATTR_KURS_UNTERSCHRITTEN):
            return "mdi:alarm-light"
        return "mdi:chart-line"

    @callback
    def _handle_coordinator_update(self) -> None:
        new_name = self._display_name(self._base)
        if new_name != self._attr_name:
            self._attr_name = new_name
        super()._handle_coordinator_update()
