"""Diagnostics support for the Joulo integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import JouloConfigEntry
from .const import CONF_API_TOKEN

TO_REDACT = {CONF_API_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: JouloConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "chargers": runtime_data.chargers_coordinator.data,
        "energy": runtime_data.energy_coordinator.data,
        "ere_position": runtime_data.ere_position_coordinator.data,
    }
