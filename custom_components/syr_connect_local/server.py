"""SYR Connect Local HTTP/HTTPS server implementation."""
from __future__ import annotations

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
        enable_debug_endpoints: bool = False,
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
        self.enable_debug_endpoints = enable_debug_endpoints

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

        # Debug-only endpoints
        if self.enable_debug_endpoints:
            self.app.router.add_get("/status", self.handle_status)
            self.app.router.add_get("/echo", self.handle_echo)
            self.app.router.add_post("/echo", self.handle_echo)

    async def handle_basic_commands(self, request: web.Request) -> web.Response:
        """Handle GetBasicCommands endpoint."""
        try:
            # Log detailed request information
            client_ip = request.remote
            scheme = request.scheme  # 'http' or 'https'
            host = request.host
            _LOGGER.debug(
                "GetBasicCommands request: scheme=%s, client=%s, host=%s, url=%s",
                scheme, client_ip, host, request.url
            )
            _LOGGER.debug("Request headers: %s", dict(request.headers))

            # Generate response requesting basic device info
            response_data = self.protocol.create_command_request(BASIC_COMMANDS)
            response_xml = self.protocol.generate_xml(response_data)

            return web.Response(
                body=response_xml.encode("utf-8"),
                content_type="text/xml",
                charset="utf-8",
            )

        except Exception as err:
            _LOGGER.error("Error handling basic commands: %s", err)
            return web.Response(
                body='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>'.encode("utf-8"),
                content_type="text/xml",
                charset="utf-8",
            )

    async def handle_all_commands(self, request: web.Request) -> web.Response:
        """Handle GetAllCommands endpoint."""
        try:
            # Log detailed request information
            client_ip = request.remote
            scheme = request.scheme  # 'http' or 'https'
            host = request.host
            _LOGGER.debug(
                "GetAllCommands request: scheme=%s, client=%s, host=%s, url=%s",
                scheme, client_ip, host, request.url
            )
            _LOGGER.debug("Request headers: %s", dict(request.headers))
            
            # Parse the POST data
            post_data = await request.post()
            xml_data = post_data.get("xml", "")

            if not xml_data:
                _LOGGER.warning("Received GetAllCommands without xml parameter")
                return web.Response(
                    body='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>'.encode("utf-8"),
                    content_type="text/xml",
                    charset="utf-8",
                )

            # Parse device properties from XML
            properties = self.protocol.parse_xml(xml_data)

            if not properties:
                _LOGGER.warning("Failed to parse device properties")
                return web.Response(
                    body='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>'.encode("utf-8"),
                    content_type="text/xml",
                    charset="utf-8",
                )

            # Get serial number to identify device
            serial = properties.get(PROPERTY_SERIAL)
            if not serial:
                _LOGGER.warning("Device did not provide serial number")
                # Still respond with command request
                response_data = self.protocol.create_command_request(ALL_COMMANDS)
                response_xml = self.protocol.generate_xml(response_data)
                return web.Response(
                    body=response_xml.encode("utf-8"),
                    content_type="text/xml",
                    charset="utf-8",
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
                _LOGGER.info(
                    "Sending %d commands to device %s: %s",
                    len(pending),
                    serial,
                    ", ".join(f"{k}={v}" for k, v in pending.items()),
                )
                response_data.update(pending)

            # Generate XML response
            response_xml = self.protocol.generate_xml(response_data)

            return web.Response(
                body=response_xml.encode("utf-8"),
                content_type="text/xml",
                charset="utf-8",
            )

        except Exception as err:
            _LOGGER.error("Error handling all commands: %s", err, exc_info=True)
            return web.Response(
                body='<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>'.encode("utf-8"),
                content_type="text/xml",
                charset="utf-8",
            )

    async def handle_status(self, request: web.Request) -> web.Response:
        """Return a JSON with integration/server status and known devices."""
        try:
            now = asyncio.get_event_loop().time()
            devices_info: list[dict[str, Any]] = []
            for serial, dev in self.devices.items():
                last_seen_ago = None
                if dev.last_seen:
                    last_seen_ago = round(max(0.0, now - dev.last_seen), 3)
                devices_info.append(
                    {
                        "serial": serial,
                        "identified": dev.is_identified,
                        "last_seen_seconds_ago": last_seen_ago,
                        "properties_count": len(dev.properties),
                        "pending_commands_count": len(dev.pending_commands),
                    }
                )

            payload = {
                "http_port": self.http_port,
                "https_port": self.https_port if self.use_https else None,
                "use_https": self.use_https,
                "devices_count": len(self.devices),
                "devices": devices_info,
            }
            return web.json_response(payload)
        except Exception as err:
            _LOGGER.error("Error building status: %s", err, exc_info=True)
            return web.json_response({"error": "internal_error"}, status=500)

    async def handle_echo(self, request: web.Request) -> web.Response:
        """Echo back request details to help diagnose connectivity."""
        try:
            info: dict[str, Any] = {
                "method": request.method,
                "scheme": request.scheme,
                "host": request.host,
                "path": request.path,
                "url": str(request.url),
                "remote": request.remote,
                "headers": dict(request.headers),
                "content_type": request.content_type,
            }

            # Try to read form fields (non-blocking if none)
            try:
                form = await request.post()
                if form:
                    # Convert MultiDict to plain dict of strings
                    info["form"] = {k: str(v) for k, v in form.items()}
            except Exception:  # best-effort
                pass

            # Safely read a small portion of raw body for reference
            try:
                body = await request.read()
                # Limit size to avoid huge payloads
                preview = body[:512]
                info["body_len"] = len(body)
                # Show a utf-8 safe preview if possible
                try:
                    info["body_preview"] = preview.decode("utf-8", errors="replace")
                except Exception:
                    info["body_preview_base64"] = preview.hex()
            except Exception:  # best-effort
                pass

            return web.json_response(info)
        except Exception as err:
            _LOGGER.error("Error handling echo: %s", err, exc_info=True)
            return web.json_response({"error": "internal_error"}, status=500)

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

            # Start HTTP server (gracefully handle port already in use)
            try:
                http_site = web.TCPSite(
                    self.runner,
                    None,  # Listen on all interfaces
                    self.http_port,
                )
                await http_site.start()
                self.sites.append(http_site)
                _LOGGER.info("SYR Connect Local HTTP server started on port %d", self.http_port)
            except OSError as err:
                # If port is in use, continue with HTTPS only
                _LOGGER.warning(
                    "HTTP port %d unavailable (%s); continuing without HTTP server",
                    self.http_port,
                    err,
                )

            # Start HTTPS server if configured
            if self.use_https and self.cert_file and self.key_file:
                _LOGGER.info(
                    "Starting HTTPS server on port %d with cert=%s, key=%s",
                    self.https_port, self.cert_file, self.key_file
                )
                try:
                    loop = asyncio.get_event_loop()
                    ssl_context = await loop.run_in_executor(
                        None, self._create_ssl_context
                    )

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
            else:
                _LOGGER.debug(
                    "HTTPS not started: use_https=%s, cert_file=%s, key_file=%s",
                    self.use_https, self.cert_file, self.key_file
                )

        except Exception as err:
            _LOGGER.error("Failed to start server: %s", err)
            raise

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context (runs in thread pool executor)."""
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(self.cert_file, self.key_file)
        
        # Allow older TLS versions and weaker ciphers for compatibility with legacy SYR devices
        # SYR devices may use TLS 1.0/1.1 with older cipher suites
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1
        ssl_context.set_ciphers("DEFAULT:@SECLEVEL=0")
        
        _LOGGER.debug("SSL context created with TLS 1.0+ support and relaxed cipher policy")
        return ssl_context

    async def stop(self) -> None:
        """Stop the server."""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.sites.clear()
            _LOGGER.info("SYR Connect Local server stopped")
