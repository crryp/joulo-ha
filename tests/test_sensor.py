"""Tests for the Joulo sensor platform, focused on the ERE position sensors."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.joulo.const import CONF_API_TOKEN, DOMAIN
from custom_components.joulo.sensor import _current_quarter


def test_current_quarter_falls_back_to_last_when_none_in_progress() -> None:
    """If every quarter is final (e.g. between Joulo's own rollovers), use the
    most recent one instead of returning nothing."""
    pos = {
        "quarters": [
            {"quarter": "2026-Q1", "final": True},
            {"quarter": "2026-Q2", "final": True},
        ]
    }
    assert _current_quarter(pos)["quarter"] == "2026-Q2"


def test_current_quarter_handles_missing_quarters_data() -> None:
    """No /ere-position 'quarters' data yet: return an empty dict, not an error."""
    assert _current_quarter({}) == {}


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

    compliance_year = hass.states.get("sensor.joulo_account_ere_compliance_year")
    assert compliance_year.state == "2026"

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

    unsold_ytd_forecast = hass.states.get(
        "sensor.joulo_account_ere_unsold_forecast_year_to_date"
    )
    assert unsold_ytd_forecast.state == "24.15"

    unsold_ytd_ere = hass.states.get(
        "sensor.joulo_account_ere_unsold_credits_year_to_date"
    )
    assert unsold_ytd_ere.state == "30.75"

    pending_forecast = hass.states.get(
        "sensor.joulo_account_ere_pending_forecast_in_review"
    )
    assert pending_forecast.state == "12.4"

    pending_ere = hass.states.get("sensor.joulo_account_ere_pending_credits_in_review")
    assert pending_ere.state == "15.5"

    current_quarter = hass.states.get("sensor.joulo_account_ere_current_quarter")
    assert current_quarter.state == "2026-Q2"

    current_quarter_price = hass.states.get(
        "sensor.joulo_account_ere_current_quarter_price"
    )
    assert current_quarter_price.state == "74.9"

    current_quarter_sold = hass.states.get(
        "sensor.joulo_account_ere_current_quarter_sold_credits"
    )
    assert current_quarter_sold.state == "15.0"

    current_quarter_unsold = hass.states.get(
        "sensor.joulo_account_ere_current_quarter_unsold_credits"
    )
    assert current_quarter_unsold.state == "6.75"

    current_quarter_realized = hass.states.get(
        "sensor.joulo_account_ere_current_quarter_realized_revenue"
    )
    assert current_quarter_realized.state == "11.24"
    assert current_quarter_realized.attributes["net_eur_by_status"] == {
        "paid": 0,
        "payable": 0,
        "reserved": 11.24,
    }
