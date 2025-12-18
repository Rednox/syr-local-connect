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
    SETTER_START_REGEN,
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

        entities.append(SyrStartRegenerationButton(coordinator, serial))

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Button platform: new device signal for %s", serial)
        # Create button entities - device_data will be available when coordinator updates
        new_entities: list[ButtonEntity] = [
            SyrStartRegenerationButton(coordinator, serial)
        ]
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
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True

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
