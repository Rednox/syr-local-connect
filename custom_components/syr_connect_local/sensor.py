"""Sensor platform for SYR Connect Local integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    PROPERTY_CAPACITY,
    PROPERTY_CONSUMPTION_LAST_MONTH,
    PROPERTY_CONSUMPTION_MONTH,
    PROPERTY_CONSUMPTION_TODAY,
    PROPERTY_CONSUMPTION_TOTAL,
    PROPERTY_CONSUMPTION_YESTERDAY,
    PROPERTY_FIRMWARE,
    PROPERTY_FLOW,
    PROPERTY_INLET_HARDNESS,
    PROPERTY_LAST_REGEN,
    PROPERTY_NAME,
    PROPERTY_OUTLET_HARDNESS,
    PROPERTY_PRESSURE,
    PROPERTY_SALT_TANK1,
    PROPERTY_SALT_TANK2,
    PROPERTY_SALT_TANK3,
    PROPERTY_SERIAL,
    PROPERTY_TEMPERATURE,
    PROPERTY_TOTAL_REGEN,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local sensors."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[SensorEntity] = []

    # Create sensors for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Water hardness sensors
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_INLET_HARDNESS,
                "Inlet Water Hardness",
                "°dH",
                None,
                SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_OUTLET_HARDNESS,
                "Outlet Water Hardness",
                "°dH",
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

        # Salt level sensors (only if present)
        if device_data.get(PROPERTY_SALT_TANK1) is not None:
            entities.append(
                SyrSensor(
                    coordinator,
                    serial,
                    PROPERTY_SALT_TANK1,
                    "Salt Level Tank 1",
                    PERCENTAGE,
                    None,
                    SensorStateClass.MEASUREMENT,
                )
            )

        if device_data.get(PROPERTY_SALT_TANK2) is not None and device_data.get(PROPERTY_SALT_TANK2) != 0:
            entities.append(
                SyrSensor(
                    coordinator,
                    serial,
                    PROPERTY_SALT_TANK2,
                    "Salt Level Tank 2",
                    PERCENTAGE,
                    None,
                    SensorStateClass.MEASUREMENT,
                )
            )

        if device_data.get(PROPERTY_SALT_TANK3) is not None and device_data.get(PROPERTY_SALT_TANK3) != 0:
            entities.append(
                SyrSensor(
                    coordinator,
                    serial,
                    PROPERTY_SALT_TANK3,
                    "Salt Level Tank 3",
                    PERCENTAGE,
                    None,
                    SensorStateClass.MEASUREMENT,
                )
            )

        # Capacity
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CAPACITY,
                "Capacity Remaining",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

        # Flow
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_FLOW,
                "Water Flow",
                UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

        # Pressure
        entities.append(
            SyrPressureSensor(coordinator, serial)
        )

        # Consumption sensors
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CONSUMPTION_TODAY,
                "Water Consumption Today",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.TOTAL_INCREASING,
            )
        )
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CONSUMPTION_YESTERDAY,
                "Water Consumption Yesterday",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.TOTAL,
            )
        )
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CONSUMPTION_MONTH,
                "Water Consumption This Month",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.TOTAL_INCREASING,
            )
        )
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CONSUMPTION_LAST_MONTH,
                "Water Consumption Last Month",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.TOTAL,
            )
        )
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_CONSUMPTION_TOTAL,
                "Total Water Consumption",
                UnitOfVolume.LITERS,
                None,
                SensorStateClass.TOTAL_INCREASING,
            )
        )

        # Regeneration info
        entities.append(SyrLastRegenerationSensor(coordinator, serial))
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_TOTAL_REGEN,
                "Total Regenerations",
                None,
                None,
                SensorStateClass.TOTAL_INCREASING,
            )
        )

        # Device info sensors
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_VERSION,
                "Firmware Version",
                None,
                None,
            )
        )

        # Temperature (if available - LEX Plus SL)
        if device_data.get(PROPERTY_TEMPERATURE) is not None:
            entities.append(
                SyrSensor(
                    coordinator,
                    serial,
                    PROPERTY_TEMPERATURE,
                    "Water Temperature",
                    UnitOfTemperature.CELSIUS,
                    SensorDeviceClass.TEMPERATURE,
                    SensorStateClass.MEASUREMENT,
                )
            )

    async_add_entities(entities)


class SyrSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SYR sensor."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
        property_key: str,
        name: str,
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._property_key = property_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{serial}_{property_key}"

        # Set device info
        device_data = coordinator.get_device_data(serial)
        device_name = device_data.get(PROPERTY_NAME, "SYR Device") if device_data else "SYR Device"
        firmware = device_data.get(PROPERTY_FIRMWARE, "") if device_data else ""
        device_type = device_data.get(PROPERTY_TYPE, "") if device_data else ""
        version = device_data.get(PROPERTY_VERSION, "") if device_data else ""

        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": device_name,
            "manufacturer": "SYR",
            "model": f"{firmware} Type {device_type}" if firmware and device_type else "LEX Plus",
            "sw_version": version,
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            return device_data.get(self._property_key)
        return None


class SyrPressureSensor(SyrSensor):
    """Pressure sensor with conversion from bar*10 to bar."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the pressure sensor."""
        super().__init__(
            coordinator,
            serial,
            PROPERTY_PRESSURE,
            "Water Pressure",
            UnitOfPressure.BAR,
            SensorDeviceClass.PRESSURE,
            SensorStateClass.MEASUREMENT,
        )

    @property
    def native_value(self) -> float | None:
        """Return the pressure in bar (device reports bar*10)."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            pressure_raw = device_data.get(self._property_key)
            if pressure_raw is not None:
                try:
                    return float(pressure_raw) / 10.0
                except (ValueError, TypeError):
                    return None
        return None


class SyrLastRegenerationSensor(SyrSensor):
    """Last regeneration sensor with timestamp conversion."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the last regeneration sensor."""
        super().__init__(
            coordinator,
            serial,
            PROPERTY_LAST_REGEN,
            "Last Regeneration",
            None,
            SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the last regeneration as datetime."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            timestamp = device_data.get(self._property_key)
            if timestamp is not None:
                try:
                    return datetime.fromtimestamp(int(timestamp))
                except (ValueError, TypeError, OSError):
                    return None
        return None
