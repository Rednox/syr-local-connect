"""Switch platform for SYR Connect Local integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    PROPERTY_POWER_STATE,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local switches."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[SwitchEntity] = []

    # Create switches for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Note: Power switch is experimental and may not work on all devices
        # Commenting out until it can be properly tested
        # entities.append(SyrPowerSwitch(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Switch platform: new device signal for %s", serial)
        device_data = coordinator.get_device_data(serial)
        if device_data:
            new_entities: list[SwitchEntity] = []
            # Note: Power switch is experimental and may not work on all devices
            # Uncomment when ready to test:
            # new_entities.append(SyrPowerSwitch(coordinator, serial))
            if new_entities:
                _LOGGER.info("Switch platform: adding %d entities for %s", len(new_entities), serial)
                async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SYR switch."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
        property_key: str,
        name: str,
        setter_command: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._serial = serial
        self._property_key = property_key
        self._setter_command = setter_command
        self._attr_name = name
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
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            value = device_data.get(self._property_key)
            if isinstance(value, bool):
                return value
            # Handle string values
            if value == "1":
                return True
            if value == "0":
                return False
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = self.coordinator.queue_command(self._serial, self._setter_command, "1")
        if success:
            _LOGGER.info("Turned on %s for device %s", self._attr_name, self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on %s for device %s", self._attr_name, self._serial)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = self.coordinator.queue_command(self._serial, self._setter_command, "0")
        if success:
            _LOGGER.info("Turned off %s for device %s", self._attr_name, self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off %s for device %s", self._attr_name, self._serial)


class SyrPowerSwitch(SyrSwitch):
    """Power switch for the device.
    
    Note: The setPST setter is not officially documented in the protocol.
    This switch is experimental and may not work on all firmware versions.
    """

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the power switch."""
        # Note: setPST is not documented in the SYR Connect protocol
        # This is an experimental feature
        super().__init__(
            coordinator,
            serial,
            PROPERTY_POWER_STATE,
            "Power",
            "setPST",  # Experimental setter command
        )
