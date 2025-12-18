"""Select platform for SYR Connect Local integration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
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
    PROPERTY_REGEN_WEEKDAYS,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SETTER_REGEN_WEEKDAYS,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)

# Weekday encoding: Each bit represents a day (bit 0 = Monday, bit 6 = Sunday)
# The protocol uses a string representation of a number where each bit is a day
WEEKDAY_OPTIONS = {
    "Every Day": "127",  # 1111111
    "Weekdays (Mon-Fri)": "31",  # 0011111
    "Weekends (Sat-Sun)": "96",  # 1100000
    "Monday": "1",  # 0000001
    "Tuesday": "2",  # 0000010
    "Wednesday": "4",  # 0000100
    "Thursday": "8",  # 0001000
    "Friday": "16",  # 0010000
    "Saturday": "32",  # 0100000
    "Sunday": "64",  # 1000000
    "Mon, Wed, Fri": "21",  # 0010101
    "Tue, Thu, Sat": "42",  # 0101010
}

# Reverse mapping for display
WEEKDAY_VALUES = {v: k for k, v in WEEKDAY_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local selects."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[SelectEntity] = []

    # Create selects for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Regeneration weekdays
        if device_data.get(PROPERTY_REGEN_WEEKDAYS) is not None:
            entities.append(SyrRegenWeekdaysSelect(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Select platform: new device signal for %s", serial)
        device_data = coordinator.get_device_data(serial)
        if device_data:
            new_entities: list[SelectEntity] = []

            # Regeneration weekdays
            if device_data.get(PROPERTY_REGEN_WEEKDAYS) is not None:
                new_entities.append(SyrRegenWeekdaysSelect(coordinator, serial))

            if new_entities:
                _LOGGER.info("Select platform: adding %d entities for %s", len(new_entities), serial)
                async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrRegenWeekdaysSelect(CoordinatorEntity, SelectEntity):
    """Select entity for regeneration weekdays."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "Regeneration Week Days"
        self._attr_unique_id = f"{serial}_regen_weekdays"
        self._attr_icon = "mdi:calendar-week"
        self._attr_options = list(WEEKDAY_OPTIONS.keys())

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
            device_data is not None and device_data.get(PROPERTY_REGEN_WEEKDAYS) is not None
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._serial not in self.coordinator.devices:
            return False
        
        # Entity is available only if the property exists in device data
        device_data = self.coordinator.get_device_data(self._serial)
        return device_data is not None and device_data.get(PROPERTY_REGEN_WEEKDAYS) is not None

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            value = device_data.get(PROPERTY_REGEN_WEEKDAYS)
            if value is not None:
                # Convert value to string and look up in mapping
                value_str = str(value)
                if value_str in WEEKDAY_VALUES:
                    return WEEKDAY_VALUES[value_str]
                # If not in predefined options, log warning and return None
                # This allows the UI to show "Unknown" state
                _LOGGER.warning(
                    "Unknown weekday value %s for device %s. Use service to set custom values.",
                    value_str, self._serial
                )
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in WEEKDAY_OPTIONS:
            _LOGGER.error("Invalid weekday option: %s", option)
            return

        value = WEEKDAY_OPTIONS[option]
        success = self.coordinator.queue_command(self._serial, SETTER_REGEN_WEEKDAYS, value)
        
        if success:
            _LOGGER.info("Set regeneration weekdays to %s (%s) for device %s", option, value, self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set regeneration weekdays for device %s", self._serial)
