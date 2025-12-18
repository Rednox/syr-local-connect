"""Button platform for SYR Connect Local integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    PROPERTY_FIRMWARE,
    PROPERTY_NAME,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    PROPERTY_VALVE_SHUTOFF,
    SETTER_START_REGEN,
    SETTER_VALVE_SHUTOFF,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local buttons."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[ButtonEntity] = []

    # Create buttons for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Always add the regeneration button
        entities.append(SyrStartRegenerationButton(coordinator, serial))
        
        # Add valve control button if valve shutoff property exists
        if device_data.get(PROPERTY_VALVE_SHUTOFF) is not None:
            entities.append(SyrValveOpenButton(coordinator, serial))
            entities.append(SyrValveCloseButton(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Button platform: new device signal for %s", serial)
        device_data = coordinator.get_device_data(serial)
        
        new_entities: list[ButtonEntity] = [
            SyrStartRegenerationButton(coordinator, serial)
        ]
        
        # Add valve control buttons if available
        if device_data and device_data.get(PROPERTY_VALVE_SHUTOFF) is not None:
            new_entities.append(SyrValveOpenButton(coordinator, serial))
            new_entities.append(SyrValveCloseButton(coordinator, serial))
        
        _LOGGER.info("Button platform: adding %d entities for %s", len(new_entities), serial)
        async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrStartRegenerationButton(CoordinatorEntity, ButtonEntity):
    """Button to start immediate regeneration."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "Start Regeneration"
        self._attr_unique_id = f"{serial}_start_regeneration"
        self._attr_icon = "mdi:refresh"
        # No entity_category - places button in Controls section
        self._attr_has_entity_name = True
        # Entity is enabled by default since regeneration is a core feature
        self._attr_entity_registry_enabled_default = True

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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._serial in self.coordinator.devices

    @property
    def state(self) -> str:
        """Expose a stable state to avoid showing unknown in UI."""
        return "unpressed"

    async def async_press(self) -> None:
        """Handle the button press."""
        # Queue the regeneration command (setSIR = "0" triggers regeneration)
        success = self.coordinator.queue_command(self._serial, SETTER_START_REGEN, "0")
        
        if success:
            _LOGGER.info("Regeneration started for device %s", self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to start regeneration for device %s", self._serial)


class SyrValveOpenButton(CoordinatorEntity, ButtonEntity):
    """Button to open the valve (leakage protection devices)."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "Open Valve"
        self._attr_unique_id = f"{serial}_valve_open"
        self._attr_icon = "mdi:valve-open"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        
        # Check if property is available from device
        device_data = coordinator.get_device_data(serial)
        self._attr_entity_registry_enabled_default = (
            device_data is not None and device_data.get(PROPERTY_VALVE_SHUTOFF) is not None
        )

        # Set device info
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
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._serial not in self.coordinator.devices:
            return False
        
        # Check if the valve shutoff property is available
        device_data = self.coordinator.get_device_data(self._serial)
        return device_data is not None and device_data.get(PROPERTY_VALVE_SHUTOFF) is not None

    @property
    def state(self) -> str:
        """Expose a stable state to avoid showing unknown in UI."""
        return "unpressed"

    async def async_press(self) -> None:
        """Handle the button press."""
        # Queue the valve open command (setAB = "1" opens valve)
        success = self.coordinator.queue_command(self._serial, SETTER_VALVE_SHUTOFF, "1")
        
        if success:
            _LOGGER.info("Valve open command sent for device %s", self._serial)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to send valve open command for device %s", self._serial)


class SyrValveCloseButton(CoordinatorEntity, ButtonEntity):
    """Button to close the valve (leakage protection devices)."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = "Close Valve"
        self._attr_unique_id = f"{serial}_valve_close"
        self._attr_icon = "mdi:valve-closed"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        
        # Check if property is available from device
        device_data = coordinator.get_device_data(serial)
        self._attr_entity_registry_enabled_default = (
            device_data is not None and device_data.get(PROPERTY_VALVE_SHUTOFF) is not None
        )

        # Set device info
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
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._serial not in self.coordinator.devices:
            return False
        
        # Check if the valve shutoff property is available
        device_data = self.coordinator.get_device_data(self._serial)
        return device_data is not None and device_data.get(PROPERTY_VALVE_SHUTOFF) is not None

    @property
    def state(self) -> str:
        """Expose a stable state to avoid showing unknown in UI."""
        return "unpressed"

    async def async_press(self) -> None:
        """Handle the button press."""
        # Queue the valve close command (setAB = "2" closes valve)
        success = self.coordinator.queue_command(self._serial, SETTER_VALVE_SHUTOFF, "2")
        
        if success:
            _LOGGER.info("Valve close command sent for device %s", self._serial)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to send valve close command for device %s", self._serial)
