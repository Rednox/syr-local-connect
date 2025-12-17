"""Number platform for SYR Connect Local integration."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    PROPERTY_FIRMWARE,
    PROPERTY_NAME,
    PROPERTY_REGEN_PERIOD_DAYS,
    PROPERTY_SALT_TANK2,
    PROPERTY_SALT_TANK3,
    PROPERTY_SALT_VOLUME1,
    PROPERTY_SALT_VOLUME2,
    PROPERTY_SALT_VOLUME3,
    PROPERTY_SERIAL,
    PROPERTY_TYPE,
    PROPERTY_VERSION,
    SETTER_REGEN_PERIOD_DAYS,
    SETTER_SALT_VOLUME1,
    SETTER_SALT_VOLUME2,
    SETTER_SALT_VOLUME3,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SYR Connect Local numbers."""
    coordinator: SyrConnectLocalCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    entities: list[NumberEntity] = []

    # Create numbers for each device
    for serial in coordinator.devices:
        device_data = coordinator.get_device_data(serial)
        if not device_data:
            continue

        # Salt volume numbers (one per tank)
        if device_data.get(PROPERTY_SALT_VOLUME1) is not None:
            entities.append(
                SyrSaltVolumeNumber(coordinator, serial, 1, PROPERTY_SALT_VOLUME1, SETTER_SALT_VOLUME1)
            )

        # Only add tank 2 if it exists and is not zero
        if device_data.get(PROPERTY_SALT_VOLUME2) is not None and device_data.get(PROPERTY_SALT_TANK2) is not None and device_data.get(PROPERTY_SALT_TANK2) != 0:
            entities.append(
                SyrSaltVolumeNumber(coordinator, serial, 2, PROPERTY_SALT_VOLUME2, SETTER_SALT_VOLUME2)
            )

        # Only add tank 3 if it exists and is not zero
        if device_data.get(PROPERTY_SALT_VOLUME3) is not None and device_data.get(PROPERTY_SALT_TANK3) is not None and device_data.get(PROPERTY_SALT_TANK3) != 0:
            entities.append(
                SyrSaltVolumeNumber(coordinator, serial, 3, PROPERTY_SALT_VOLUME3, SETTER_SALT_VOLUME3)
            )

        # Regeneration interval
        if device_data.get(PROPERTY_REGEN_PERIOD_DAYS) is not None:
            entities.append(
                SyrRegenIntervalNumber(coordinator, serial)
            )

    async_add_entities(entities)

    # Listen for newly discovered devices and add entities dynamically
    async def _handle_new_device(serial: str) -> None:
        _LOGGER.info("Number platform: new device signal for %s", serial)
        device_data = coordinator.get_device_data(serial)
        if device_data:
            new_entities: list[NumberEntity] = []

            # Salt volume numbers
            if device_data.get(PROPERTY_SALT_VOLUME1) is not None:
                new_entities.append(
                    SyrSaltVolumeNumber(coordinator, serial, 1, PROPERTY_SALT_VOLUME1, SETTER_SALT_VOLUME1)
                )

            if device_data.get(PROPERTY_SALT_VOLUME2) is not None and device_data.get(PROPERTY_SALT_TANK2) is not None and device_data.get(PROPERTY_SALT_TANK2) != 0:
                new_entities.append(
                    SyrSaltVolumeNumber(coordinator, serial, 2, PROPERTY_SALT_VOLUME2, SETTER_SALT_VOLUME2)
                )

            if device_data.get(PROPERTY_SALT_VOLUME3) is not None and device_data.get(PROPERTY_SALT_TANK3) is not None and device_data.get(PROPERTY_SALT_TANK3) != 0:
                new_entities.append(
                    SyrSaltVolumeNumber(coordinator, serial, 3, PROPERTY_SALT_VOLUME3, SETTER_SALT_VOLUME3)
                )

            # Regeneration interval
            if device_data.get(PROPERTY_REGEN_PERIOD_DAYS) is not None:
                new_entities.append(
                    SyrRegenIntervalNumber(coordinator, serial)
                )

            if new_entities:
                _LOGGER.info("Number platform: adding %d entities for %s", len(new_entities), serial)
                async_add_entities(new_entities)

    async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, _handle_new_device)


class SyrNumber(CoordinatorEntity, NumberEntity):
    """Base class for SYR number entities."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
        property_key: str,
        setter_command: str,
        name: str,
        unique_id_suffix: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._serial = serial
        self._property_key = property_key
        self._setter_command = setter_command
        self._attr_name = name
        self._attr_unique_id = f"{serial}_{unique_id_suffix}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_mode = NumberMode.BOX
        if icon:
            self._attr_icon = icon

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
    def native_value(self) -> float | None:
        """Return the current value."""
        device_data = self.coordinator.get_device_data(self._serial)
        if device_data:
            value = device_data.get(self._property_key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Convert to integer for transmission
        int_value = int(value)
        success = self.coordinator.queue_command(self._serial, self._setter_command, str(int_value))
        
        if success:
            _LOGGER.info("Set %s to %s for device %s", self._attr_name, int_value, self._serial)
            # Request immediate update
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set %s for device %s", self._attr_name, self._serial)


class SyrSaltVolumeNumber(SyrNumber):
    """Number entity for salt volume in kg."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
        tank_number: int,
        property_key: str,
        setter_command: str,
    ) -> None:
        """Initialize the salt volume number."""
        super().__init__(
            coordinator,
            serial,
            property_key,
            setter_command,
            f"Salt in Stock Tank {tank_number}",
            f"salt_volume_{tank_number}",
            min_value=0,
            max_value=200,  # Reasonable maximum for salt storage
            step=1,
            unit=UnitOfMass.KILOGRAMS,
            icon="mdi:shaker",
        )


class SyrRegenIntervalNumber(SyrNumber):
    """Number entity for regeneration interval in days."""

    def __init__(
        self,
        coordinator: SyrConnectLocalCoordinator,
        serial: str,
    ) -> None:
        """Initialize the regeneration interval number."""
        super().__init__(
            coordinator,
            serial,
            PROPERTY_REGEN_PERIOD_DAYS,
            SETTER_REGEN_PERIOD_DAYS,
            "Regeneration Interval",
            "regen_interval_days",
            min_value=1,
            max_value=30,  # Allow larger values than the 4 days UI limit
            step=1,
            unit=UnitOfTime.DAYS,
            icon="mdi:calendar-clock",
        )
