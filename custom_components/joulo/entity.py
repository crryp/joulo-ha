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
    JouloSessionsCoordinator,
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


class JouloChargerSessionEntity(CoordinatorEntity[JouloSessionsCoordinator]):
    """Base entity for a single charger's latest session (from GET /sessions).

    Shares the same device identifiers as JouloChargerEntity so these entities
    land on the same HA device as the rest of that charger's sensors.

    Also tracks JouloChargersCoordinator, since a session in progress needs its
    live kwh_so_far (from GET /chargers) - /sessions itself doesn't update that
    figure, or estimated_euro, until the session ends.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JouloSessionsCoordinator,
        chargers_coordinator: JouloChargersCoordinator,
        charger_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._chargers_coordinator = chargers_coordinator
        self._charger_id = charger_id

        session = self.session
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, charger_id)},
            name=session.get("charger_nickname") or "Joulo charger",
            manufacturer=MANUFACTURER,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Piggyback on the (faster-polling-while-charging) chargers coordinator
        # too, so the live kWh figure used below stays fresh even between two
        # of this entity's own sessions-coordinator refreshes.
        self.async_on_remove(
            self._chargers_coordinator.async_add_listener(
                self._handle_coordinator_update
            )
        )

    @property
    def session(self) -> dict:
        """Return this charger's latest known session (active or completed)."""
        return self.coordinator.data.get("by_charger", {}).get(self._charger_id, {})

    @property
    def latest_completed_session(self) -> dict:
        """Return this charger's most recent finished (non-cancelled) session."""
        return self.coordinator.data.get("latest_completed_by_charger", {}).get(
            self._charger_id, {}
        )

    @property
    def estimate_basis(self) -> dict:
        """Return the account-wide {price_per_ere, effective_fee_pct} in use."""
        return self.coordinator.data.get("estimate_basis", {})

    @property
    def live_kwh_so_far(self) -> float | None:
        """Return the charger's live in-progress kWh, straight from GET /chargers."""
        charger = self._chargers_coordinator.data.get(self._charger_id, {})
        return (charger.get("current_session") or {}).get("kwh_so_far")

    @property
    def available(self) -> bool:
        return super().available and self._charger_id in self.coordinator.data.get(
            "by_charger", {}
        )


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
