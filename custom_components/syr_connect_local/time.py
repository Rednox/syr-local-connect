"""Time platform for SYR Connect Local integration."""
from __future__ import annotations

from datetime import time
import logging

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    PROPERTY_FIRMWARE,
    PROPERTY_NAME,
    PROPERTY_REGEN_TIME_HOUR,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SETTER_REGEN_TIME_HOUR,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local time entities."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[TimeEntity] = []

    # Create time entities for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Regeneration time
        if device_data.get(PROPERTY_REGEN_TIME_HOUR) is not None:
            entities.append(SyrRegenTimeEntity(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Time platform: new device signal for %s", serial)
        device_data = coordinator.get_device_data(serial)
        if device_data:
            new_entities: list[TimeEntity] = []

            # Regeneration time
            if device_data.get(PROPERTY_REGEN_TIME_HOUR) is not None:
                new_entities.append(SyrRegenTimeEntity(coordinator, serial))

            if new_entities:
                _LOGGER.info("Time platform: adding %d entities for %s", len(new_entities), serial)
                async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrRegenTimeEntity(CoordinatorEntity, TimeEntity):
    """Time entity for regeneration time."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "Regeneration Time"
        self._attr_unique_id = f"{serial}_regen_time"
        self._attr_icon = "mdi:clock-time-four"

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
            device_data is not None and device_data.get(PROPERTY_REGEN_TIME_HOUR) is not None
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._serial not in self.coordinator.devices:
            return False
        
        # Entity is available only if the property exists in device data
        device_data = self.coordinator.get_device_data(self._serial)
        return device_data is not None and device_data.get(PROPERTY_REGEN_TIME_HOUR) is not None

    @property
    def native_value(self) -> time | None:
        """Return the current time value."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            value = device_data.get(PROPERTY_REGEN_TIME_HOUR)
            if value is not None:
                try:
                    # The protocol uses getRTH which returns hours (0-23)
                    # Format: "HH:MM" where minutes are typically "00"
                    if isinstance(value, str) and ":" in value:
                        # Value is already in HH:MM format
                        hour_str, minute_str = value.split(":", 1)
                        hour = int(hour_str)
                        minute = int(minute_str)
                    else:
                        # Value is just the hour
                        hour = int(value)
                        minute = 0
                    
                    return time(hour=hour, minute=minute)
                except (ValueError, TypeError) as err:
                    _LOGGER.error("Failed to parse regeneration time: %s", err)
                    return None
        return None

    async def async_set_value(self, value: time) -> None:
        """Set the time value."""
        # The protocol setRTH expects the hour value (0-23)
        # Per the documentation, this sets the regeneration hour
        hour_str = str(value.hour)
        
        success = self.coordinator.queue_command(self._serial, SETTER_REGEN_TIME_HOUR, hour_str)
        
        if success:
            _LOGGER.info("Set regeneration time to hour %s for device %s", hour_str, self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set regeneration time for device %s", self._serial)
