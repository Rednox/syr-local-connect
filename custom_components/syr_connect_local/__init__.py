"""The SYR Connect Local integration."""
from __future__ import annotations

import logging

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_CERT_FILE,
    CONF_HTTPS_PORT,
    CONF_HTTP_PORT,
    CONF_KEY_FILE,
    CONF_USE_HTTPS,
    CONF_DEBUG_ENDPOINTS,
    DATA_COORDINATOR,
    DATA_SERVER,
    DEFAULT_HTTPS_PORT,
    DEFAULT_HTTP_PORT,
    DOMAIN,
)
from .coordinator import SyrConnectLocalCoordinator
from .server import SyrConnectServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SYR Connect Local from a config entry."""
    _LOGGER.info("Setting up SYR Connect Local integration")

    # Get configuration
    http_port = entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
    https_port = entry.data.get(CONF_HTTPS_PORT, DEFAULT_HTTPS_PORT)
    use_https = entry.data.get(CONF_USE_HTTPS, False)
    cert_file = entry.data.get(CONF_CERT_FILE)
    key_file = entry.data.get(CONF_KEY_FILE)
    debug_endpoints = entry.options.get(
        CONF_DEBUG_ENDPOINTS, entry.data.get(CONF_DEBUG_ENDPOINTS, False)
    )

    # Provide sensible defaults for HTTPS cert/key if enabled but not set
    if use_https:
        if not cert_file:
            cert_file = "/config/syr_cert.pem"
        if not key_file:
            key_file = "/config/syr_key.pem"
        if not Path(cert_file).exists() or not Path(key_file).exists():
            _LOGGER.warning(
                "HTTPS disabled: cert/key not found (cert=%s, key=%s)",
                cert_file,
                key_file,
            )
            use_https = False

    # Create the server
    server = SyrConnectServer(
        http_port=http_port,
        https_port=https_port,
        use_https=use_https,
        cert_file=cert_file,
        key_file=key_file,
        enable_debug_endpoints=debug_endpoints,
    )

    # Set up device discovery callback
    def on_device_discovered(serial: str, properties: dict[str, str]) -> None:
        """Handle device discovery."""
        _LOGGER.info("Device discovered: %s", serial)
        # Trigger coordinator update to create entities
        hass.async_create_task(coordinator.async_request_refresh())

    def on_device_update(serial: str, properties: dict[str, str]) -> None:
        """Handle device update."""
        _LOGGER.debug("Device updated: %s", serial)
        # Coordinator will poll on its own schedule

    server.on_device_discovered = on_device_discovered
    server.on_device_update = on_device_update

    # Start the server
    try:
        await server.start()
    except Exception as err:
        _LOGGER.error("Failed to start server: %s", err)
        raise ConfigEntryNotReady(f"Failed to start server: {err}") from err

    # Create coordinator
    coordinator = SyrConnectLocalCoordinator(hass, server)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and server
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_SERVER: server,
    }

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_setup_services(hass, coordinator)

    _LOGGER.info("SYR Connect Local integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading SYR Connect Local integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop the server
        data = hass.data[DOMAIN].pop(entry.entry_id)
        server: SyrConnectServer = data[DATA_SERVER]
        await server.stop()

    return unload_ok


async def _async_setup_services(
    hass: HomeAssistant, coordinator: SyrConnectLocalCoordinator
) -> None:
    """Set up services for the integration."""
    from homeassistant.helpers import config_validation as cv
    import voluptuous as vol

    from .const import SERVICE_START_REGENERATION, SERVICE_UPDATE_PARAMETER, SETTER_START_REGEN

    async def async_start_regeneration(call) -> None:
        """Handle start regeneration service call."""
        device_id = call.data.get("device_id")
        serial = call.data.get("serial")

        if not serial:
            _LOGGER.error("No serial number provided for regeneration")
            return

        # Queue the regeneration command (setSIR = "0" triggers regeneration)
        success = coordinator.queue_command(serial, SETTER_START_REGEN, "0")

        if success:
            _LOGGER.info("Regeneration started for device %s", serial)
        else:
            _LOGGER.error("Failed to start regeneration for device %s", serial)

    async def async_update_parameter(call) -> None:
        """Handle update parameter service call."""
        serial = call.data.get("serial")
        parameter = call.data.get("parameter")
        value = call.data.get("value")

        if not serial or not parameter or value is None:
            _LOGGER.error("Missing required parameters for update_parameter")
            return

        # Queue the command
        success = coordinator.queue_command(serial, parameter, str(value))

        if success:
            _LOGGER.info("Parameter %s set to %s for device %s", parameter, value, serial)
        else:
            _LOGGER.error("Failed to update parameter for device %s", serial)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_REGENERATION,
        async_start_regeneration,
        schema=vol.Schema(
            {
                vol.Optional("device_id"): cv.string,
                vol.Required("serial"): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_PARAMETER,
        async_update_parameter,
        schema=vol.Schema(
            {
                vol.Required("serial"): cv.string,
                vol.Required("parameter"): cv.string,
                vol.Required("value"): cv.string,
            }
        ),
    )
