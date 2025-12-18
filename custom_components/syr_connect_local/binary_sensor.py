"""Binary sensor platform for SYR Connect Local integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    PROPERTY_ALARM,
    PROPERTY_FIRMWARE,
    PROPERTY_FLOW,
    PROPERTY_NAME,
    PROPERTY_REGEN_TANK1,
    PROPERTY_REGEN_TANK2,
    PROPERTY_REGEN_TANK3,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)



def _create_binary_entities_for_serial(coordinator: SyrConnectLocalCoordinator, serial: str) -> list[BinarySensorEntity]:
    """Create all binary sensor entities for a given device serial."""
    entities: list[BinarySensorEntity] = []
    device_data = coordinator.get_device_data(serial)

    # Regeneration active sensors (one per tank)
    entities.append(
        SyrBinarySensor(
            coordinator,
            serial,
            PROPERTY_REGEN_TANK1,
            "Regeneration Active Tank 1",
            BinarySensorDeviceClass.RUNNING,
        )
    )

    # Add tank 2 and 3 if they exist or data not yet available
    if device_data is None or device_data.get(PROPERTY_REGEN_TANK2) is not None:
        entities.append(
            SyrBinarySensor(
                coordinator,
                serial,
                PROPERTY_REGEN_TANK2,
                "Regeneration Active Tank 2",
                BinarySensorDeviceClass.RUNNING,
            )
        )

    if device_data is None or device_data.get(PROPERTY_REGEN_TANK3) is not None:
        entities.append(
            SyrBinarySensor(
                coordinator,
                serial,
                PROPERTY_REGEN_TANK3,
                "Regeneration Active Tank 3",
                BinarySensorDeviceClass.RUNNING,
            )
        )

    # Flow active sensor
    entities.append(
        SyrFlowBinarySensor(coordinator, serial)
    )

    # Alarm sensor
    entities.append(
        SyrAlarmBinarySensor(coordinator, serial)
    )

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local binary sensors."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[BinarySensorEntity] = []

    # Create binary sensors for each device
    for serial in coordinator.devices:
        entities.extend(_create_binary_entities_for_serial(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Binary sensor platform: new device signal for %s", serial)
        new_entities = _create_binary_entities_for_serial(coordinator, serial)
        if new_entities:
            _LOGGER.info("Binary sensor platform: adding %d entities for %s", len(new_entities), serial)
            async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SYR binary sensor."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
        property_key: str,
        name: str,
        device_class: BinarySensorDeviceClass | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._property_key = property_key
        self._attr_name = name
        self._attr_device_class = device_class
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
        
        # Enable entity by default only if property is available from device
        self._attr_entity_registry_enabled_default = (
            device_data is not None and device_data.get(property_key) is not None
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._serial not in self.coordinator.devices:
            return False
        
        # Entity is available only if the property exists in device data
        device_data = self.coordinator.get_device_data(self._serial)
        return device_data is not None and device_data.get(self._property_key) is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            value = device_data.get(self._property_key)
            if isinstance(value, bool):
                return value
            # Handle empty strings as None
            if value == "":
                return None
            # Handle string values
            if value == "1":
                return True
            if value == "0":
                return False
        return None


class SyrFlowBinarySensor(SyrBinarySensor):
    """Binary sensor for water flow."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the flow binary sensor."""
        super().__init__(
            coordinator,
            serial,
            PROPERTY_FLOW,
            "Flow Active",
            BinarySensorDeviceClass.RUNNING,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if water is flowing."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            flow = device_data.get(self._property_key)
            if flow is not None and flow != "":
                try:
                    return int(flow) > 0
                except (ValueError, TypeError):
                    return None
        return None


class SyrAlarmBinarySensor(SyrBinarySensor):
    """Binary sensor for alarm status."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the alarm binary sensor."""
        super().__init__(
            coordinator,
            serial,
            PROPERTY_ALARM,
            "Alarm",
            BinarySensorDeviceClass.PROBLEM,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if there is an alarm."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            alarm = device_data.get(self._property_key)
            # Alarm is active if the value is not empty
            if alarm is not None:
                return bool(alarm and alarm != "")
        return None
