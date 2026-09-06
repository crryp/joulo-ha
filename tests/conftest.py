"""Fixtures for Joulo tests."""
from __future__ import annotations

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components discoverable in every test."""
    yield


@pytest.fixture
def mock_chargers_response() -> dict:
    """A representative /chargers response."""
    return {
        "chargers": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "nickname": "Garage",
                "connection_type": "easee",
                "status": "active",
                "mid_certified": True,
                "is_charging": True,
                "current_session": {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "started_at": "2026-08-03T08:00:00Z",
                    "kwh_so_far": 4.2,
                    "id_tag": "04A3B2C1",
                },
                "latest_meter_wh": 1234500,
                "meter_updated_at": "2026-08-03T09:00:00Z",
            }
        ]
    }


@pytest.fixture
def mock_energy_response() -> dict:
    """A representative /energy response."""
    return {
        "total_kwh": 2847.52,
        "total_ere_credits": 427.13,
        "total_sessions": 186,
        "total_kwh_all": 3102.18,
        "total_sessions_all": 203,
        "months": [],
    }


@pytest.fixture
def mock_ere_position_response() -> dict:
    """A representative /ere-position response."""
    return {
        "effective_fee_pct": 8,
        "indicative_price_per_ere": 78.5,
        "realized_avg_price": 74.2,
        "paid": {"net_eur": 12450.30, "price_per_ere": 73.1},
        "payable": {"net_eur": 890.15},
        "reserved": {"net_eur": 320.0},
        "unsold": {
            "forecast_net_eur": 1580.4,
            "future_forecast_net_eur": 2100.75,
            "ytd_forecast_net_eur": 24.15,
            "ytd_ere": 30.75,
        },
        "pending_forecast_net_eur": 12.4,
        "pending_ere": 15.5,
        "ytd_expected_eur": 14920.85,
        "total_expected_eur": 19241.6,
        "allocatable_ere": 427.13,
        "forecast_confidence": "high",
        "forecast_history_days": 90,
        "quarters": [
            {
                "quarter": "2026-Q1",
                "final": True,
                "price_per_ere": 71.4,
                "sold_ere": 40.0,
                "unsold_ere": 0.0,
                "realized_net_eur": 28.56,
                "net_eur_by_status": {"paid": 28.56, "payable": 0, "reserved": 0},
            },
            {
                "quarter": "2026-Q2",
                "final": False,
                "price_per_ere": 74.9,
                "sold_ere": 15.0,
                "unsold_ere": 6.75,
                "realized_net_eur": 11.24,
                "net_eur_by_status": {"paid": 0, "payable": 0, "reserved": 11.24},
            },
        ],
    }
