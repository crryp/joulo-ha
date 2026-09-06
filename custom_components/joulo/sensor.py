"""Sensor platform for the Joulo integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import JouloConfigEntry
from .entity import JouloAccountEntity, JouloChargerEntity, JouloErePositionEntity

EUR_PER_ERE = "EUR/ERE"


@dataclass(frozen=True, kw_only=True)
class JouloChargerSensorDescription(SensorEntityDescription):
    """Describes a Joulo per-charger sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class JouloAccountSensorDescription(SensorEntityDescription):
    """Describes a Joulo account-wide sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class JouloErePositionSensorDescription(SensorEntityDescription):
    """Describes a Joulo ERE position sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


CHARGER_SENSORS: tuple[JouloChargerSensorDescription, ...] = (
    JouloChargerSensorDescription(
        key="status",
        translation_key="status",
        value_fn=lambda charger: charger.get("status"),
    ),
    JouloChargerSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        # HA disallows state_class=measurement for device_class=energy. total_increasing
        # is the documented pattern for this exact case: a value that only increases
        # within a session and is allowed to reset to 0 when a new session starts.
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda charger: (charger.get("current_session") or {}).get("kwh_so_far"),
    ),
    JouloChargerSensorDescription(
        key="active_tag_id",
        translation_key="active_tag_id",
        icon="mdi:credit-card-wireless-outline",
        # RFID/TAG id of the active session, e.g. to identify the vehicle/driver
        # behind a charge. None (unknown) when no session is active.
        value_fn=lambda charger: (charger.get("current_session") or {}).get("id_tag")
        or None,
    ),
    JouloChargerSensorDescription(
        key="meter_reading",
        translation_key="meter_reading",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        entity_registry_enabled_default=False,
        value_fn=lambda charger: charger.get("latest_meter_wh"),
    ),
)

ACCOUNT_SENSORS: tuple[JouloAccountSensorDescription, ...] = (
    JouloAccountSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda energy: energy.get("total_kwh"),
    ),
    JouloAccountSensorDescription(
        key="total_ere_credits",
        translation_key="total_ere_credits",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="credits",
        value_fn=lambda energy: energy.get("total_ere_credits"),
    ),
    JouloAccountSensorDescription(
        key="total_sessions",
        translation_key="total_sessions",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="sessions",
        value_fn=lambda energy: energy.get("total_sessions"),
    ),
)

def _current_quarter(pos: dict[str, Any]) -> dict[str, Any]:
    """Return the in-progress quarter (final == False), or the most recent one."""
    quarters = pos.get("quarters") or []
    for quarter in quarters:
        if not quarter.get("final"):
            return quarter
    return quarters[-1] if quarters else {}


ERE_POSITION_SENSORS: tuple[JouloErePositionSensorDescription, ...] = (
    JouloErePositionSensorDescription(
        key="ere_compliance_year",
        translation_key="ere_compliance_year",
        entity_category=EntityCategory.DIAGNOSTIC,
        # /ere-position defaults to the current calendar year and every other
        # ere_* sensor is scoped to it. Exposed so it's unambiguous which
        # year the rest of the figures apply to, especially right at the
        # New Year boundary.
        value_fn=lambda pos: pos.get("compliance_year"),
    ),
    JouloErePositionSensorDescription(
        key="ere_paid",
        translation_key="ere_paid",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("paid") or {}).get("net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_payable",
        translation_key="ere_payable",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("payable") or {}).get("net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_reserved",
        translation_key="ere_reserved",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("reserved") or {}).get("net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_unsold_forecast",
        translation_key="ere_unsold_forecast",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("unsold") or {}).get("forecast_net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_unsold_future_forecast",
        translation_key="ere_unsold_future_forecast",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("unsold") or {}).get("future_forecast_net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_unsold_ytd_forecast",
        translation_key="ere_unsold_ytd_forecast",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: (pos.get("unsold") or {}).get("ytd_forecast_net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_unsold_ytd_ere",
        translation_key="ere_unsold_ytd_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="credits",
        value_fn=lambda pos: (pos.get("unsold") or {}).get("ytd_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_pending_forecast",
        translation_key="ere_pending_forecast",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: pos.get("pending_forecast_net_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_pending_ere",
        translation_key="ere_pending_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="credits",
        value_fn=lambda pos: pos.get("pending_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_ytd_expected",
        translation_key="ere_ytd_expected",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: pos.get("ytd_expected_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_total_expected",
        translation_key="ere_total_expected",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: pos.get("total_expected_eur"),
    ),
    JouloErePositionSensorDescription(
        key="ere_indicative_price",
        translation_key="ere_indicative_price",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=EUR_PER_ERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("indicative_price_per_ere"),
        extra_attrs_fn=lambda pos: {"quarters": pos.get("quarters")},
    ),
    JouloErePositionSensorDescription(
        key="ere_realized_avg_price",
        translation_key="ere_realized_avg_price",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=EUR_PER_ERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("realized_avg_price"),
    ),
    JouloErePositionSensorDescription(
        key="ere_paid_price_per_ere",
        translation_key="ere_paid_price_per_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=EUR_PER_ERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: (pos.get("paid") or {}).get("price_per_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_fee_pct",
        translation_key="ere_fee_pct",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("effective_fee_pct"),
    ),
    JouloErePositionSensorDescription(
        key="ere_allocatable",
        translation_key="ere_allocatable",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="credits",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("allocatable_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_forecast_confidence",
        translation_key="ere_forecast_confidence",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("forecast_confidence"),
    ),
    JouloErePositionSensorDescription(
        key="ere_forecast_history",
        translation_key="ere_forecast_history",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: pos.get("forecast_history_days"),
    ),
    JouloErePositionSensorDescription(
        key="ere_current_quarter",
        translation_key="ere_current_quarter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: _current_quarter(pos).get("quarter"),
    ),
    JouloErePositionSensorDescription(
        key="ere_current_quarter_price_per_ere",
        translation_key="ere_current_quarter_price_per_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=EUR_PER_ERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda pos: _current_quarter(pos).get("price_per_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_current_quarter_sold_ere",
        translation_key="ere_current_quarter_sold_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="credits",
        value_fn=lambda pos: _current_quarter(pos).get("sold_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_current_quarter_unsold_ere",
        translation_key="ere_current_quarter_unsold_ere",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="credits",
        value_fn=lambda pos: _current_quarter(pos).get("unsold_ere"),
    ),
    JouloErePositionSensorDescription(
        key="ere_current_quarter_realized",
        translation_key="ere_current_quarter_realized",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="EUR",
        value_fn=lambda pos: _current_quarter(pos).get("realized_net_eur"),
        extra_attrs_fn=lambda pos: {
            "net_eur_by_status": _current_quarter(pos).get("net_eur_by_status")
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JouloConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Joulo sensors from a config entry."""
    runtime_data = entry.runtime_data
    chargers_coordinator = runtime_data.chargers_coordinator
    energy_coordinator = runtime_data.energy_coordinator
    ere_position_coordinator = runtime_data.ere_position_coordinator

    entities: list[SensorEntity] = [
        JouloAccountSensor(energy_coordinator, entry, description)
        for description in ACCOUNT_SENSORS
    ] + [
        JouloErePositionSensor(ere_position_coordinator, entry, description)
        for description in ERE_POSITION_SENSORS
    ]

    known_charger_ids: set[str] = set()

    def _add_charger_entities(charger_id: str) -> None:
        known_charger_ids.add(charger_id)
        async_add_entities(
            JouloChargerSensor(chargers_coordinator, charger_id, description)
            for description in CHARGER_SENSORS
        )

    for charger_id in chargers_coordinator.data:
        _add_charger_entities(charger_id)

    def _handle_new_chargers() -> None:
        for charger_id in chargers_coordinator.data:
            if charger_id not in known_charger_ids:
                _add_charger_entities(charger_id)

    entry.async_on_unload(chargers_coordinator.async_add_listener(_handle_new_chargers))

    async_add_entities(entities)


class JouloChargerSensor(JouloChargerEntity, SensorEntity):
    """A sensor derived from a single charger's data."""

    entity_description: JouloChargerSensorDescription

    def __init__(
        self,
        coordinator,
        charger_id: str,
        description: JouloChargerSensorDescription,
    ) -> None:
        super().__init__(coordinator, charger_id)
        self.entity_description = description
        self._attr_unique_id = f"{charger_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.charger)


class JouloAccountSensor(JouloAccountEntity, SensorEntity):
    """A sensor derived from the account-wide /energy endpoint."""

    entity_description: JouloAccountSensorDescription

    def __init__(
        self,
        coordinator,
        entry: JouloConfigEntry,
        description: JouloAccountSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)


class JouloErePositionSensor(JouloErePositionEntity, SensorEntity):
    """A sensor derived from the account-wide /ere-position endpoint."""

    entity_description: JouloErePositionSensorDescription

    def __init__(
        self,
        coordinator,
        entry: JouloConfigEntry,
        description: JouloErePositionSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra_attrs_fn is None:
            return None
        return self.entity_description.extra_attrs_fn(self.coordinator.data)
