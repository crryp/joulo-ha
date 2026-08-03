"""Config flow for the Joulo integration."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import JouloApiClient, JouloApiError, JouloAuthError
from .const import (
    CONF_API_TOKEN,
    CONF_CHARGERS_SCAN_INTERVAL,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_ERE_POSITION_SCAN_INTERVAL,
    DEFAULT_CHARGERS_SCAN_INTERVAL,
    DEFAULT_ENERGY_SCAN_INTERVAL,
    DEFAULT_ERE_POSITION_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_TOKEN): str})


class JouloConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Joulo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: ask for a personal API token."""
        return await self._async_step_token(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user swap in a new personal API token for an existing entry."""
        return await self._async_step_token(user_input)

    async def _async_step_token(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reconfiguring = self.source == SOURCE_RECONFIGURE

        if user_input is not None:
            token = user_input[CONF_API_TOKEN].strip()
            session = async_get_clientsession(self.hass)
            client = JouloApiClient(session, token)

            try:
                chargers = await client.async_get_chargers()
            except JouloAuthError:
                errors["base"] = "invalid_auth"
            except JouloApiError:
                errors["base"] = "cannot_connect"
            else:
                # The fingerprint is derived from the token text itself (the API
                # exposes no stable account id), so it changes on every legitimate
                # token rotation too - it can only be used to dedupe on initial
                # setup, not to verify "same account" during reconfigure.
                if reconfiguring:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        unique_id=_token_fingerprint(token),
                        data={CONF_API_TOKEN: token},
                    )

                await self.async_set_unique_id(_token_fingerprint(token))
                self._abort_if_unique_id_configured()

                title = "Joulo"
                if chargers:
                    charger_word = "charger" if len(chargers) == 1 else "chargers"
                    title = f"Joulo ({len(chargers)} {charger_word})"

                return self.async_create_entry(
                    title=title,
                    data={CONF_API_TOKEN: token},
                )

        return self.async_show_form(
            step_id="reconfigure" if reconfiguring else "user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> JouloOptionsFlow:
        """Get the options flow for this handler."""
        return JouloOptionsFlow()


def _scan_interval_selector(minimum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=86400,
            step=1,
            unit_of_measurement="s",
            mode=NumberSelectorMode.BOX,
        )
    )


class JouloOptionsFlow(OptionsFlow):
    """Let the user tune per-endpoint polling intervals after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CHARGERS_SCAN_INTERVAL,
                    default=options.get(
                        CONF_CHARGERS_SCAN_INTERVAL, DEFAULT_CHARGERS_SCAN_INTERVAL
                    ),
                ): _scan_interval_selector(minimum=10),
                vol.Optional(
                    CONF_ENERGY_SCAN_INTERVAL,
                    default=options.get(
                        CONF_ENERGY_SCAN_INTERVAL, DEFAULT_ENERGY_SCAN_INTERVAL
                    ),
                ): _scan_interval_selector(minimum=60),
                vol.Optional(
                    CONF_ERE_POSITION_SCAN_INTERVAL,
                    default=options.get(
                        CONF_ERE_POSITION_SCAN_INTERVAL,
                        DEFAULT_ERE_POSITION_SCAN_INTERVAL,
                    ),
                ): _scan_interval_selector(minimum=60),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def _token_fingerprint(token: str) -> str:
    """Return a short, non-secret identifier used only for de-duplication."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]
