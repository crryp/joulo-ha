"""Data update coordinators for the Joulo integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import JouloApiClient, JouloApiError, JouloAuthError
from .const import DOMAIN, SESSIONS_POLL_LIMIT

_LOGGER = logging.getLogger(__name__)


class JouloChargersCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls GET /chargers and indexes the result by charger id."""

    def __init__(
        self, hass: HomeAssistant, client: JouloApiClient, update_interval: timedelta
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_chargers",
            update_interval=update_interval,
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            chargers = await self._client.async_get_chargers()
        except JouloAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication error: {err}") from err
        except JouloApiError as err:
            raise UpdateFailed(f"Error fetching chargers: {err}") from err

        return {charger["id"]: charger for charger in chargers}


class JouloEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls GET /energy for lifetime + monthly totals."""

    def __init__(
        self, hass: HomeAssistant, client: JouloApiClient, update_interval: timedelta
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_energy",
            update_interval=update_interval,
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._client.async_get_energy()
        except JouloAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication error: {err}") from err
        except JouloApiError as err:
            raise UpdateFailed(f"Error fetching energy statistics: {err}") from err


class JouloErePositionCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls GET /ere-position for the account's ERE reserve/sell/forecast position."""

    def __init__(
        self, hass: HomeAssistant, client: JouloApiClient, update_interval: timedelta
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_ere_position",
            update_interval=update_interval,
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._client.async_get_ere_position()
        except JouloAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication error: {err}") from err
        except JouloApiError as err:
            raise UpdateFailed(f"Error fetching ERE position: {err}") from err


class JouloSessionsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls GET /sessions and indexes it per charger.

    Sessions come back newest-first, so the first entry seen for a given
    charger_id is that charger's latest session (active or completed); the
    first one with a non-null estimated_euro is its latest *finished* one
    (Joulo only fills in estimated_euro/ere_credits once a session ends).
    """

    def __init__(
        self, hass: HomeAssistant, client: JouloApiClient, update_interval: timedelta
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_sessions",
            update_interval=update_interval,
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            result = await self._client.async_get_sessions(limit=SESSIONS_POLL_LIMIT)
        except JouloAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication error: {err}") from err
        except JouloApiError as err:
            raise UpdateFailed(f"Error fetching sessions: {err}") from err

        by_charger: dict[str, dict[str, Any]] = {}
        latest_completed_by_charger: dict[str, dict[str, Any]] = {}
        for session in result.get("sessions", []):
            charger_id = session.get("charger_id")
            if charger_id is None:
                continue
            if charger_id not in by_charger:
                by_charger[charger_id] = session
            if (
                charger_id not in latest_completed_by_charger
                and session.get("estimated_euro") is not None
            ):
                latest_completed_by_charger[charger_id] = session

        return {
            "by_charger": by_charger,
            "latest_completed_by_charger": latest_completed_by_charger,
            "estimate_basis": result.get("estimate_basis", {}),
        }
