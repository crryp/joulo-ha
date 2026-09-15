"""Tests for the Joulo sensor platform, focused on the ERE position sensors."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
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
    mock_sessions_response: dict,
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
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_sessions",
            return_value=mock_sessions_response,
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


async def _setup_estimated_euro_entry(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
    mock_sessions_response: dict,
) -> str:
    """Set up the integration and return the estimated_euro sensor's entity_id."""
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
        patch(
            "custom_components.joulo.api.JouloApiClient.async_get_sessions",
            return_value=mock_sessions_response,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    charger_id = mock_chargers_response["chargers"][0]["id"]
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{charger_id}_estimated_euro"
    )
    assert entity_id is not None
    return entity_id


async def test_estimated_euro_live_estimate_during_active_session(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
    mock_sessions_response: dict,
) -> None:
    """While charging, Joulo's own estimated_euro is null (it fills in only once
    the session ends), so the sensor derives a live approximation from the
    charger's last finished session's ERE-credits-per-kWh rate applied to the
    live kwh_so_far from GET /chargers."""
    entity_id = await _setup_estimated_euro_entry(
        hass,
        mock_chargers_response,
        mock_energy_response,
        mock_ere_position_response,
        mock_sessions_response,
    )

    state = hass.states.get(entity_id)
    # kwh_so_far=4.2 (from mock_chargers_response) * (2.81/8.46 ere credits/kWh,
    # from the last finished session in mock_sessions_response) * price_per_ere
    # 0.483 * (1 - 8%) = 0.62.
    assert state.state == "0.62"
    assert state.attributes["unit_of_measurement"] == "EUR"
    assert state.attributes["device_class"] == "monetary"
    assert state.attributes["is_estimate"] is True


async def test_estimated_euro_zero_while_charging_without_session_history(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
    mock_sessions_response: dict,
) -> None:
    """No finished session yet to derive a rate from -> 0 (still an estimate,
    just can't be computed yet), not unknown."""
    mock_sessions_response = {
        **mock_sessions_response,
        "sessions": [mock_sessions_response["sessions"][0]],  # only the active one
    }
    entity_id = await _setup_estimated_euro_entry(
        hass,
        mock_chargers_response,
        mock_energy_response,
        mock_ere_position_response,
        mock_sessions_response,
    )

    state = hass.states.get(entity_id)
    assert state.state == "0.0"
    assert state.attributes["is_estimate"] is True


async def test_estimated_euro_prefers_finalized_value_over_live_estimate(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
    mock_sessions_response: dict,
) -> None:
    """If Joulo has already filled in a real estimated_euro for the charger's
    session, use that exact figure instead of the live approximation."""
    mock_sessions_response = {
        **mock_sessions_response,
        "sessions": [mock_sessions_response["sessions"][1]],  # the completed one
    }
    entity_id = await _setup_estimated_euro_entry(
        hass,
        mock_chargers_response,
        mock_energy_response,
        mock_ere_position_response,
        mock_sessions_response,
    )

    state = hass.states.get(entity_id)
    assert state.state == "1.25"
    assert state.attributes["is_estimate"] is False


async def test_estimated_euro_zero_when_idle(
    hass: HomeAssistant,
    mock_chargers_response: dict,
    mock_energy_response: dict,
    mock_ere_position_response: dict,
    mock_sessions_response: dict,
) -> None:
    """No session in progress -> 0, regardless of what the last session paid out."""
    idle_chargers_response = {
        "chargers": [
            {
                **mock_chargers_response["chargers"][0],
                "is_charging": False,
                "current_session": None,
            }
        ]
    }
    entity_id = await _setup_estimated_euro_entry(
        hass,
        idle_chargers_response,
        mock_energy_response,
        mock_ere_position_response,
        mock_sessions_response,
    )

    state = hass.states.get(entity_id)
    assert state.state == "0.0"
    assert state.attributes["is_estimate"] is False
