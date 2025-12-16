"""Data coordinator for SYR Connect Local integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PROPERTY_SERIAL
from .server import DeviceState, SyrConnectServer

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)


class SyrConnectLocalCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching SYR Connect Local data."""

    def __init__(self, hass: HomeAssistant, server: SyrConnectServer) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.server = server
        self.devices: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the server's device states."""
        try:
            # Get all devices from the server
            devices = self.server.get_all_devices()

            # Convert device states to data dictionary
            data: dict[str, dict[str, Any]] = {}

            for serial, device_state in devices.items():
                if not device_state.is_identified:
                    # Skip devices that haven't been fully identified yet
                    continue

                # Convert properties to appropriate types
                device_data = self._convert_device_data(device_state)
                data[serial] = device_data

            self.devices = data
            return data

        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            raise UpdateFailed(f"Error communicating with server: {err}") from err

    def _convert_device_data(self, device_state: DeviceState) -> dict[str, Any]:
        """Convert device state to typed data dictionary."""
        from .protocol import SyrProtocol

        protocol = SyrProtocol()
        data: dict[str, Any] = {}

        for prop_name, prop_value in device_state.properties.items():
            converted_value = protocol.convert_value(prop_name, prop_value)
            data[prop_name] = converted_value

        return data

    def get_device_data(self, serial: str) -> dict[str, Any] | None:
        """Get data for a specific device."""
        return self.devices.get(serial)

    def queue_command(self, serial: str, command: str, value: str) -> bool:
        """Queue a command for a device."""
        return self.server.queue_command(serial, command, value)
