"""SYR Connect Local HTTP/HTTPS server implementation."""
from __future__ import annotations

import asyncio
import logging
import ssl
import time
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
    PROPERTY_CODE,
    PROPERTY_MAC,
    PROPERTY_SERIAL,
)
from .protocol import SyrProtocol

_LOGGER = logging.getLogger(__name__)


@web.middleware
async def _request_debug_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Any],
) -> web.StreamResponse:
    """Log every incoming request to this plugin server."""
    started = time.perf_counter()
    _LOGGER.debug(
        "Incoming request: method=%s scheme=%s host=%s path=%s client=%s",
        request.method,
        request.scheme,
        request.host,
        request.path_qs,
        request.remote,
    )

    try:
        response = await handler(request)
    except Exception as err:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _LOGGER.debug(
            "Request failed: method=%s path=%s client=%s error=%s duration_ms=%.2f",
            request.method,
            request.path_qs,
            request.remote,
            err,
            elapsed_ms,
        )
        raise

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    _LOGGER.debug(
        "Request completed: method=%s path=%s client=%s status=%s duration_ms=%.2f",
        request.method,
        request.path_qs,
        request.remote,
        response.status,
        elapsed_ms,
    )
    return response


class DeviceState:
    """Store state for a single SYR device."""

    def __init__(self, serial_number: str):
        """Initialize device state."""
        self.serial_number = serial_number
        self.properties: dict[str, str] = {}
        self.pending_commands: dict[str, str] = {}
        self.last_seen: float = 0
        self.is_identified = False
        self.auth_token: str | None = None
        self.source_ip: str | None = None

    def bootstrap_auth(self, properties: dict[str, str], source_ip: str | None) -> None:
        """Capture trust anchors from the first successful device update."""
        token = properties.get(PROPERTY_CODE)
        if token:
            self.auth_token = token

        if source_ip:
            self.source_ip = source_ip

    def is_authenticated(self, properties: dict[str, str], source_ip: str | None) -> bool:
        """Validate that a request matches this known device identity."""
        request_token = properties.get(PROPERTY_CODE)

        if self.auth_token:
            if not request_token:
                _LOGGER.warning(
                    "Rejecting request for %s: missing device token",
                    self.serial_number,
                )
                return False
            if request_token != self.auth_token:
                _LOGGER.warning(
                    "Rejecting request for %s: invalid device token",
                    self.serial_number,
                )
                return False

        if self.source_ip and source_ip and self.source_ip != source_ip:
            _LOGGER.warning(
                "Rejecting request for %s: source IP changed (%s -> %s)",
                self.serial_number,
                self.source_ip,
                source_ip,
            )
            return False

        known_mac = self.properties.get(PROPERTY_MAC)
        request_mac = properties.get(PROPERTY_MAC)
        if known_mac and request_mac and known_mac != request_mac:
            _LOGGER.warning(
                "Rejecting request for %s: MAC mismatch",
                self.serial_number,
            )
            return False

        return True

    def update_properties(self, properties: dict[str, str]) -> None:
        """Update device properties from received data."""
        if not self.auth_token:
            token = properties.get(PROPERTY_CODE)
            if token:
                self.auth_token = token

        self.properties.update(properties)

    def queue_command(self, command: str, value: str) -> None:
        """Queue a command to be sent to the device."""
        self.pending_commands[command] = value
        _LOGGER.info(
            "[CMD_QUEUE] Device %s (obj=%s): Queued %s=%s (total pending: %d)",
            self.serial_number,
            id(self),
            command,
            value,
            len(self.pending_commands),
        )

    def get_pending_commands(self) -> dict[str, str]:
        """Get and clear pending commands."""
        count = len(self.pending_commands)
        _LOGGER.info(
            "[CMD_GET] Device %s (obj=%s): Retrieving %d pending commands: %s",
            self.serial_number,
            id(self),
            count,
            list(self.pending_commands.keys()) if count > 0 else "none",
        )
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
        legacy_tls_compat: bool = False,
    ):
        """Initialize the server."""
        self.http_port = http_port
        self.https_port = https_port
        self.use_https = use_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.legacy_tls_compat = legacy_tls_compat

        self.devices: dict[str, DeviceState] = {}
        self.protocol = SyrProtocol()
        self.app = web.Application(middlewares=[_request_debug_middleware])
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
            is_new_device = serial not in self.devices
            if is_new_device:
                _LOGGER.info("New device discovered: %s", serial)
                device = DeviceState(serial)
                self.devices[serial] = device
                device.bootstrap_auth(properties, client_ip)
            else:
                device = self.devices[serial]
                if not device.is_authenticated(properties, client_ip):
                    return web.Response(status=403, text="forbidden")

            # Update device properties
            device.update_properties(properties)
            device.last_seen = asyncio.get_event_loop().time()

            # Mark as identified after first complete update
            was_unidentified = not device.is_identified
            if was_unidentified and len(properties) > 5:
                device.is_identified = True
                _LOGGER.info("Device %s fully identified", serial)

            # Notify about new device AFTER it's been identified
            # This ensures coordinator can fetch device data when entities are created
            if is_new_device and device.is_identified:
                if self.on_device_discovered:
                    self.on_device_discovered(serial, properties)

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
        _LOGGER.info(
            "[SERVER_QUEUE] For serial %s: got device obj=%s from self.devices",
            serial,
            id(device) if device else "None",
        )
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
        self._apply_tls_policy(ssl_context, legacy_compat=self.legacy_tls_compat)

        return ssl_context

    @staticmethod
    def _apply_tls_policy(ssl_context: ssl.SSLContext, legacy_compat: bool) -> None:
        """Apply TLS policy.

        Policy goals:
        - Default: modern TLS (prefer TLS 1.3, allow TLS 1.2 fallback).
        - Optional legacy mode: broaden compatibility for old device firmware.
        """
        if legacy_compat:
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1
            # Keep compatibility with older TLS stacks that require OpenSSL security
            # level 0. This is intentionally opt-in and should be used only when needed.
            try:
                ssl_context.set_ciphers("DEFAULT:@SECLEVEL=0")
            except ssl.SSLError as err:
                _LOGGER.warning("Could not apply legacy cipher profile: %s", err)

            _LOGGER.warning(
                "Legacy TLS compatibility mode enabled: allows TLS 1.0+ and weaker ciphers"
            )
            return

        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

        max_tls = getattr(ssl.TLSVersion, "TLSv1_3", None)
        if max_tls is not None:
            ssl_context.maximum_version = max_tls

        ssl_context.options |= ssl.OP_NO_COMPRESSION

        _LOGGER.debug(
            "SSL context created with modern policy: min=%s, max=%s, default ciphers",
            ssl_context.minimum_version.name,
            ssl_context.maximum_version.name if ssl_context.maximum_version else "system-default",
        )

    async def stop(self) -> None:
        """Stop the server."""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.sites.clear()
            _LOGGER.info("SYR Connect Local server stopped")
