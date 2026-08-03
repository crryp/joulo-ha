"""Base entities shared by the Joulo platforms."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import (
    JouloChargersCoordinator,
    JouloEnergyCoordinator,
    JouloErePositionCoordinator,
)


class JouloChargerEntity(CoordinatorEntity[JouloChargersCoordinator]):
    """Base entity tied to a single charger, keyed by charger id."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JouloChargersCoordinator, charger_id: str) -> None:
        super().__init__(coordinator)
        self._charger_id = charger_id

        charger = self.charger
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, charger_id)},
            name=charger.get("nickname") or "Joulo charger",
            manufacturer=MANUFACTURER,
            model=charger.get("connection_type"),
        )

    @property
    def charger(self) -> dict:
        """Return the latest data for this entity's charger."""
        return self.coordinator.data.get(self._charger_id, {})

    @property
    def available(self) -> bool:
        return super().available and self._charger_id in self.coordinator.data


class JouloAccountEntity(CoordinatorEntity[JouloEnergyCoordinator]):
    """Base entity for account-wide (non-charger-specific) statistics."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JouloEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Joulo account",
            manufacturer=MANUFACTURER,
        )


class JouloErePositionEntity(CoordinatorEntity[JouloErePositionCoordinator]):
    """Base entity for the account-wide ERE reserve/sell/forecast position."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: JouloErePositionCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Joulo account",
            manufacturer=MANUFACTURER,
        )
