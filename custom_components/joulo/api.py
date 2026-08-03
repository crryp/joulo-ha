"""Thin async client for the Joulo API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


class JouloApiError(Exception):
    """Generic error talking to the Joulo API."""


class JouloAuthError(JouloApiError):
    """Raised on 401/403 responses (bad token or missing scope)."""


class JouloApiClient:
    """Wraps the handful of read endpoints the integration needs."""

    def __init__(self, session: aiohttp.ClientSession, api_token: str) -> None:
        self._session = session
        self._api_token = api_token

    async def async_get_chargers(self) -> list[dict[str, Any]]:
        """Return all chargers linked to the account."""
        data = await self._request("GET", "/chargers")
        return data.get("chargers", [])

    async def async_get_energy(self) -> dict[str, Any]:
        """Return lifetime + monthly energy statistics."""
        return await self._request("GET", "/energy")

    async def async_get_ere_position(self) -> dict[str, Any]:
        """Return the account's ERE reserve/sell/forecast position (euro-denominated)."""
        return await self._request("GET", "/ere-position")

    async def async_get_sessions(
        self,
        *,
        charger_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return charging sessions, optionally filtered to one charger."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if charger_id is not None:
            params["charger_id"] = charger_id
        return await self._request("GET", "/sessions", params=params)

    async def _request(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{API_BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {self._api_token}"}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(
                    method, url, headers=headers, params=params
                )
        except asyncio.TimeoutError as err:
            raise JouloApiError(f"Timeout communicating with Joulo API: {path}") from err
        except aiohttp.ClientError as err:
            raise JouloApiError(f"Error communicating with Joulo API: {err}") from err

        if response.status in (401, 403):
            body = await response.text()
            raise JouloAuthError(f"Joulo API authentication failed ({response.status}): {body}")

        if response.status != 200:
            body = await response.text()
            raise JouloApiError(f"Joulo API returned {response.status} for {path}: {body}")

        return await response.json()
