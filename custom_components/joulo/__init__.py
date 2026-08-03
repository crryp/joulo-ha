"""The Joulo integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JouloApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_CHARGERS_SCAN_INTERVAL,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_ERE_POSITION_SCAN_INTERVAL,
    DEFAULT_CHARGERS_SCAN_INTERVAL,
    DEFAULT_ENERGY_SCAN_INTERVAL,
    DEFAULT_ERE_POSITION_SCAN_INTERVAL,
)
from .coordinator import (
    JouloChargersCoordinator,
    JouloEnergyCoordinator,
    JouloErePositionCoordinator,
)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass
class JouloRuntimeData:
    """Runtime data stored on the config entry."""

    client: JouloApiClient
    chargers_coordinator: JouloChargersCoordinator
    energy_coordinator: JouloEnergyCoordinator
    ere_position_coordinator: JouloErePositionCoordinator


JouloConfigEntry = ConfigEntry[JouloRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: JouloConfigEntry) -> bool:
    """Set up Joulo from a config entry."""
    session = async_get_clientsession(hass)
    client = JouloApiClient(session, entry.data[CONF_API_TOKEN])

    chargers_coordinator = JouloChargersCoordinator(
        hass,
        client,
        timedelta(
            seconds=entry.options.get(
                CONF_CHARGERS_SCAN_INTERVAL, DEFAULT_CHARGERS_SCAN_INTERVAL
            )
        ),
    )
    energy_coordinator = JouloEnergyCoordinator(
        hass,
        client,
        timedelta(
            seconds=entry.options.get(
                CONF_ENERGY_SCAN_INTERVAL, DEFAULT_ENERGY_SCAN_INTERVAL
            )
        ),
    )
    ere_position_coordinator = JouloErePositionCoordinator(
        hass,
        client,
        timedelta(
            seconds=entry.options.get(
                CONF_ERE_POSITION_SCAN_INTERVAL, DEFAULT_ERE_POSITION_SCAN_INTERVAL
            )
        ),
    )

    await chargers_coordinator.async_config_entry_first_refresh()
    await energy_coordinator.async_config_entry_first_refresh()
    await ere_position_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = JouloRuntimeData(
        client=client,
        chargers_coordinator=chargers_coordinator,
        energy_coordinator=energy_coordinator,
        ere_position_coordinator=ere_position_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: JouloConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: JouloConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
