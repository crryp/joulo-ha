"""Binary sensor platform for the Joulo integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import JouloConfigEntry
from .coordinator import JouloChargersCoordinator
from .entity import JouloChargerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JouloConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Joulo 'is charging' binary sensor from a config entry."""
    coordinator = entry.runtime_data.chargers_coordinator

    known_charger_ids: set[str] = set()

    def _add_charger_entities(charger_id: str) -> None:
        known_charger_ids.add(charger_id)
        async_add_entities([JouloChargingBinarySensor(coordinator, charger_id)])

    for charger_id in coordinator.data:
        _add_charger_entities(charger_id)

    def _handle_new_chargers() -> None:
        for charger_id in coordinator.data:
            if charger_id not in known_charger_ids:
                _add_charger_entities(charger_id)

    entry.async_on_unload(coordinator.async_add_listener(_handle_new_chargers))


class JouloChargingBinarySensor(JouloChargerEntity, BinarySensorEntity):
    """Whether a charger currently has an active charging session."""

    _attr_translation_key = "is_charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: JouloChargersCoordinator, charger_id: str) -> None:
        super().__init__(coordinator, charger_id)
        self._attr_unique_id = f"{charger_id}_is_charging"

    @property
    def is_on(self) -> bool | None:
        return self.charger.get("is_charging")
