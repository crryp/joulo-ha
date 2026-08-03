"""Tests for the Joulo config flow."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joulo.api import JouloAuthError
from custom_components.joulo.config_flow import _token_fingerprint
from custom_components.joulo.const import (
    CONF_API_TOKEN,
    CONF_CHARGERS_SCAN_INTERVAL,
    CONF_ENERGY_SCAN_INTERVAL,
    CONF_ERE_POSITION_SCAN_INTERVAL,
    DOMAIN,
)


async def test_user_flow_success(
    hass: HomeAssistant, mock_chargers_response: dict
) -> None:
    """A valid token creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "custom_components.joulo.config_flow.JouloApiClient.async_get_chargers",
        return_value=mock_chargers_response["chargers"],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "test-token"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_API_TOKEN] == "test-token"


async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """An invalid token surfaces an error on the form instead of creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.joulo.config_flow.JouloApiClient.async_get_chargers",
        side_effect=JouloAuthError("bad token"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "bad-token"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_flow_updates_token(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
) -> None:
    """Reconfigure swaps in a rotated token for the same entry, no re-add needed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "old-token"},
        unique_id=_token_fingerprint("old-token"),
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_chargers",
            return_value=mock_chargers_response["chargers"],
        ),
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_energy",
            return_value=mock_energy_response,
        ),
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_ere_position",
            return_value=mock_ere_position_response,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "new-token"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_API_TOKEN] == "new-token"
    assert entry.unique_id == _token_fingerprint("new-token")


async def test_options_flow_updates_scan_intervals(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
) -> None:
    """Changing the options reloads the entry with new coordinator polling intervals."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_API_TOKEN: "test-token"})
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_chargers",
            return_value=mock_chargers_response["chargers"],
        ),
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_energy",
            return_value=mock_energy_response,
        ),
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_ere_position",
            return_value=mock_ere_position_response,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_CHARGERS_SCAN_INTERVAL: 30,
                CONF_ENERGY_SCAN_INTERVAL: 1800,
                CONF_ERE_POSITION_SCAN_INTERVAL: 1800,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_CHARGERS_SCAN_INTERVAL] == 30
    assert entry.runtime_data.chargers_coordinator.update_interval == timedelta(
        seconds=30
    )
    assert entry.runtime_data.energy_coordinator.update_interval == timedelta(
        seconds=1800
    )
