"""Tests for the Joulo sensor platform, focused on the ERE position sensors."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joulo.const import CONF_API_TOKEN, DOMAIN


async def test_ere_position_sensors(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
) -> None:
    """The /ere-position euro fields are exposed as sensors on the account device."""
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

    state = hass.states.get("sensor.joulo_account_ere_paid_out")
    assert state is not None
    assert state.state == "12450.3"
    assert state.attributes["unit_of_measurement"] == "EUR"
    assert state.attributes["device_class"] == "monetary"

    payable = hass.states.get("sensor.joulo_account_ere_payable")
    assert payable.state == "890.15"

    ytd_expected = hass.states.get(
        "sensor.joulo_account_ere_expected_revenue_year_to_date"
    )
    assert ytd_expected.state == "14920.85"

    indicative_price = hass.states.get("sensor.joulo_account_ere_indicative_price")
    assert indicative_price.state == "78.5"
    assert (
        indicative_price.attributes["quarters"]
        == mock_ere_position_response["quarters"]
    )

    confidence = hass.states.get("sensor.joulo_account_ere_forecast_confidence")
    assert confidence.state == "high"
