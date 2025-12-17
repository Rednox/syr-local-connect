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
    UnitOfMass,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
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
    PROPERTY_SALT_DAYS1,
    PROPERTY_SALT_DAYS2,
    PROPERTY_SALT_DAYS3,
    PROPERTY_SALT_TANK1,
    PROPERTY_SALT_TANK2,
    PROPERTY_SALT_TANK3,
    PROPERTY_SALT_VOLUME1,
    PROPERTY_SALT_VOLUME2,
    PROPERTY_SALT_VOLUME3,
    PROPERTY_SALT_WEEKS1,
    PROPERTY_SALT_WEEKS2,
    PROPERTY_SALT_WEEKS3,
    PROPERTY_SERIAL,
    PROPERTY_TEMPERATURE,
    PROPERTY_TOTAL_REGEN,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


def _create_entities_for_serial(coordinator: SyrConnectLocalCoordinator, serial: str) -> list[SensorEntity]:
    """Create all sensor entities for a given device serial."""
    entities: list[SensorEntity] = []
    device_data = coordinator.get_device_data(serial)

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

    # Resin capacity sensors (getCS1/2/3 - remaining capacity of resin, not salt level)
    if device_data is None or device_data.get(PROPERTY_SALT_TANK1) is not None:
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_TANK1,
                "Resin Capacity Tank 1",
                PERCENTAGE,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_TANK2) is not None and device_data.get(PROPERTY_SALT_TANK2) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_TANK2,
                "Resin Capacity Tank 2",
                PERCENTAGE,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_TANK3) is not None and device_data.get(PROPERTY_SALT_TANK3) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_TANK3,
                "Resin Capacity Tank 3",
                PERCENTAGE,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    # Actual salt volume sensors (getSV1/2/3 - salt stored in kg)
    if device_data is None or device_data.get(PROPERTY_SALT_VOLUME1) is not None:
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_VOLUME1,
                "Salt Volume Tank 1",
                UnitOfMass.KILOGRAMS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_VOLUME2) is not None and device_data.get(PROPERTY_SALT_VOLUME2) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_VOLUME2,
                "Salt Volume Tank 2",
                UnitOfMass.KILOGRAMS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_VOLUME3) is not None and device_data.get(PROPERTY_SALT_VOLUME3) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_VOLUME3,
                "Salt Volume Tank 3",
                UnitOfMass.KILOGRAMS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    # Salt duration in days (getSD1/2/3 - salt lasts for n days)
    if device_data is None or device_data.get(PROPERTY_SALT_DAYS1) is not None:
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_DAYS1,
                "Salt Remaining Days Tank 1",
                UnitOfTime.DAYS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_DAYS2) is not None and device_data.get(PROPERTY_SALT_DAYS2) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_DAYS2,
                "Salt Remaining Days Tank 2",
                UnitOfTime.DAYS,
                None,
                SensorStateClass.MEASUREMENT,
            )
        )

    if device_data is None or (device_data.get(PROPERTY_SALT_DAYS3) is not None and device_data.get(PROPERTY_SALT_DAYS3) != 0):
        entities.append(
            SyrSensor(
                coordinator,
                serial,
                PROPERTY_SALT_DAYS3,
                "Salt Remaining Days Tank 3",
                UnitOfTime.DAYS,
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
    if device_data is None or device_data.get(PROPERTY_TEMPERATURE) is not None:
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

    return entities


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
        entities.extend(_create_entities_for_serial(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Sensor platform: new device signal for %s", serial)
        new_entities = _create_entities_for_serial(coordinator, serial)
        if new_entities:
            _LOGGER.info("Sensor platform: adding %d entities for %s", len(new_entities), serial)
            async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


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
            value = device_data.get(self._property_key)
            # Handle empty strings as None
            if value == "":
                return None
            return value
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
            if pressure_raw is not None and pressure_raw != "":
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
        from datetime import timezone
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            timestamp = device_data.get(self._property_key)
            if timestamp is not None and timestamp != "":
                try:
                    # Create timezone-aware datetime (UTC)
                    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                except (ValueError, TypeError, OSError):
                    return None
        return None
