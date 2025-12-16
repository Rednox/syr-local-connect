"""SYR Connect Local HTTP/HTTPS server implementation."""
import asyncio
import logging
import ssl
from typing import Any, Callable

from aiohttp import web

from .const import (
    ALL_COMMANDS,
    BASIC_COMMANDS,
    ENDPOINT_ALL,
    ENDPOINT_ALL_ALT,
    ENDPOINT_BASIC,
    ENDPOINT_BASIC_ALT,
    EXTENDED_PROPERTIES,
    LEAKAGE_PROPERTIES,
    PROPERTY_SERIAL,
)
from .protocol import SyrProtocol

_LOGGER = logging.getLogger(__name__)


class DeviceState:
    """Store state for a single SYR device."""

    def __init__(self, serial_number: str):
        """Initialize device state."""
        self.serial_number = serial_number
        self.properties: dict[str, str] = {}
        self.pending_commands: dict[str, str] = {}
        self.last_seen: float = 0
        self.is_identified = False

    def update_properties(self, properties: dict[str, str]) -> None:
        """Update device properties from received data."""
        self.properties.update(properties)

    def queue_command(self, command: str, value: str) -> None:
        """Queue a command to be sent to the device."""
        self.pending_commands[command] = value
        _LOGGER.debug(
            "Queued command %s=%s for device %s", command, value, self.serial_number
        )

    def get_pending_commands(self) -> dict[str, str]:
        """Get and clear pending commands."""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()
        return commands


class SyrConnectServer:
    """SYR Connect local server implementation."""

    def __init__(
        self,
        http_port: int = 80,
        https_port: int = 443,
        use_https: bool = False,
        cert_file: str | None = None,
        key_file: str | None = None,
    ):
        """Initialize the server."""
        self.http_port = http_port
        self.https_port = https_port
        self.use_https = use_https
        self.cert_file = cert_file
        self.key_file = key_file

        self.devices: dict[str, DeviceState] = {}
        self.protocol = SyrProtocol()
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.sites: list[web.TCPSite] = []

        # Callbacks for device events
        self.on_device_discovered: Callable[[str, dict[str, str]], None] | None = None
        self.on_device_update: Callable[[str, dict[str, str]], None] | None = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        # Main endpoints
        self.app.router.add_post(ENDPOINT_BASIC, self.handle_basic_commands)
        self.app.router.add_post(ENDPOINT_ALL, self.handle_all_commands)

        # Alternative endpoints
        self.app.router.add_post(ENDPOINT_BASIC_ALT, self.handle_basic_commands)
        self.app.router.add_post(ENDPOINT_ALL_ALT, self.handle_all_commands)

    async def handle_basic_commands(self, request: web.Request) -> web.Response:
        """Handle GetBasicCommands endpoint."""
        try:
            # For basic commands, we just request device identification
            _LOGGER.debug("Received GetBasicCommands request")

            # Generate response requesting basic device info
            response_data = self.protocol.create_command_request(BASIC_COMMANDS)
            response_xml = self.protocol.generate_xml(response_data)

            return web.Response(
                text=response_xml,
                content_type="text/xml; charset=utf-8",
            )

        except Exception as err:
            _LOGGER.error("Error handling basic commands: %s", err)
            return web.Response(
                text='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>',
                content_type="text/xml; charset=utf-8",
            )

    async def handle_all_commands(self, request: web.Request) -> web.Response:
        """Handle GetAllCommands endpoint."""
        try:
            # Parse the POST data
            post_data = await request.post()
            xml_data = post_data.get("xml", "")

            if not xml_data:
                _LOGGER.warning("Received GetAllCommands without xml parameter")
                return web.Response(
                    text='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>',
                    content_type="text/xml; charset=utf-8",
                )

            # Parse device properties from XML
            properties = self.protocol.parse_xml(xml_data)

            if not properties:
                _LOGGER.warning("Failed to parse device properties")
                return web.Response(
                    text='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>',
                    content_type="text/xml; charset=utf-8",
                )

            # Get serial number to identify device
            serial = properties.get(PROPERTY_SERIAL)
            if not serial:
                _LOGGER.warning("Device did not provide serial number")
                # Still respond with command request
                response_data = self.protocol.create_command_request(ALL_COMMANDS)
                response_xml = self.protocol.generate_xml(response_data)
                return web.Response(
                    text=response_xml,
                    content_type="text/xml; charset=utf-8",
                )

            # Get or create device state
            if serial not in self.devices:
                _LOGGER.info("New device discovered: %s", serial)
                device = DeviceState(serial)
                self.devices[serial] = device

                # Notify about new device
                if self.on_device_discovered:
                    self.on_device_discovered(serial, properties)
            else:
                device = self.devices[serial]

            # Update device properties
            device.update_properties(properties)
            device.last_seen = asyncio.get_event_loop().time()

            # Mark as identified after first complete update
            if not device.is_identified and len(properties) > 5:
                device.is_identified = True
                _LOGGER.info("Device %s fully identified", serial)

            # Notify about device update
            if self.on_device_update:
                self.on_device_update(serial, properties)

            # Prepare response
            # Start with requesting all standard commands
            response_data = self.protocol.create_command_request(ALL_COMMANDS)

            # Add extended properties periodically
            if device.is_identified:
                for prop in EXTENDED_PROPERTIES:
                    response_data[prop] = ""

                # Add leakage properties if device supports them
                # Check if device has leakage detection (type 80+ or has leakage data)
                if properties.get("getAB") is not None or properties.get("getVLV") is not None:
                    for prop in LEAKAGE_PROPERTIES:
                        response_data[prop] = ""

            # Add any pending commands (setters)
            pending = device.get_pending_commands()
            if pending:
                _LOGGER.debug("Adding %d pending commands for device %s", len(pending), serial)
                response_data.update(pending)

            # Generate XML response
            response_xml = self.protocol.generate_xml(response_data)

            return web.Response(
                text=response_xml,
                content_type="text/xml; charset=utf-8",
            )

        except Exception as err:
            _LOGGER.error("Error handling all commands: %s", err, exc_info=True)
            return web.Response(
                text='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>',
                content_type="text/xml; charset=utf-8",
            )

    def get_device(self, serial: str) -> DeviceState | None:
        """Get device state by serial number."""
        return self.devices.get(serial)

    def get_all_devices(self) -> dict[str, DeviceState]:
        """Get all device states."""
        return self.devices

    def queue_command(self, serial: str, command: str, value: str) -> bool:
        """Queue a command for a device."""
        device = self.get_device(serial)
        if device:
            device.queue_command(command, value)
            return True
        _LOGGER.warning("Cannot queue command for unknown device: %s", serial)
        return False

    async def start(self) -> None:
        """Start the server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            # Start HTTP server
            http_site = web.TCPSite(
                self.runner,
                None,  # Listen on all interfaces
                self.http_port,
            )
            await http_site.start()
            self.sites.append(http_site)
            _LOGGER.info("SYR Connect Local HTTP server started on port %d", self.http_port)

            # Start HTTPS server if configured
            if self.use_https and self.cert_file and self.key_file:
                try:
                    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ssl_context.load_cert_chain(self.cert_file, self.key_file)

                    https_site = web.TCPSite(
                        self.runner,
                        None,  # Listen on all interfaces
                        self.https_port,
                        ssl_context=ssl_context,
                    )
                    await https_site.start()
                    self.sites.append(https_site)
                    _LOGGER.info(
                        "SYR Connect Local HTTPS server started on port %d",
                        self.https_port,
                    )
                except Exception as err:
                    _LOGGER.error("Failed to start HTTPS server: %s", err)

        except Exception as err:
            _LOGGER.error("Failed to start server: %s", err)
            raise

    async def stop(self) -> None:
        """Stop the server."""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.sites.clear()
            _LOGGER.info("SYR Connect Local server stopped")
