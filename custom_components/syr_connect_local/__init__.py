"""The SYR Connect Local integration."""
from __future__ import annotations

import logging

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_CERT_FILE,
    CONF_HTTPS_PORT,
    CONF_HTTP_PORT,
    CONF_KEY_FILE,
    CONF_USE_HTTPS,
    CONF_DEBUG_ENDPOINTS,
    CONF_LEGACY_TLS_ALLOWED_TUPLES,
    DATA_COORDINATOR,
    DATA_SERVER,
    DEFAULT_HTTPS_PORT,
    DEFAULT_HTTP_PORT,
    DOMAIN,
    HANDLED_DOMAINS,
    SIGNAL_NEW_DEVICE,
)
from .coordinator import SyrConnectLocalCoordinator
from .server import SyrConnectServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TIME,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SYR Connect Local from a config entry."""
    _LOGGER.info("Setting up SYR Connect Local integration")

    # Get configuration
    http_port = entry.options.get(
        CONF_HTTP_PORT, entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
    )
    https_port = entry.options.get(
        CONF_HTTPS_PORT, entry.data.get(CONF_HTTPS_PORT, DEFAULT_HTTPS_PORT)
    )
    use_https = entry.options.get(
        CONF_USE_HTTPS, entry.data.get(CONF_USE_HTTPS, False)
    )
    cert_file = entry.options.get(CONF_CERT_FILE, entry.data.get(CONF_CERT_FILE))
    key_file = entry.options.get(CONF_KEY_FILE, entry.data.get(CONF_KEY_FILE))
    debug_endpoints = entry.options.get(
        CONF_DEBUG_ENDPOINTS, entry.data.get(CONF_DEBUG_ENDPOINTS, False)
    )
    legacy_tls_allowed_tuples = entry.options.get(
        CONF_LEGACY_TLS_ALLOWED_TUPLES,
        entry.data.get(CONF_LEGACY_TLS_ALLOWED_TUPLES, []),
    )

    # Provide sensible defaults for HTTPS cert/key if enabled but not set
    if use_https:
        cert_file, key_file = await _async_resolve_or_create_certs(hass, cert_file, key_file)
        if not cert_file or not key_file:
            _LOGGER.warning(
                "HTTPS disabled: could not resolve or create certificates"
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
        legacy_tls_allowed_tuples=legacy_tls_allowed_tuples,
    )

    # Set up device discovery callback
    async def on_device_discovered_async(serial: str, properties: dict[str, str]) -> None:
        """Handle device discovery asynchronously."""
        _LOGGER.info("Device discovered: %s", serial)
        # Trigger coordinator update to create entities
        await coordinator.async_request_refresh()
        # Signal to platform listeners after coordinator has updated
        async_dispatcher_send(hass, SIGNAL_NEW_DEVICE, serial)

    def on_device_discovered(serial: str, properties: dict[str, str]) -> None:
        """Handle device discovery."""
        hass.async_create_task(on_device_discovered_async(serial, properties))

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

    # Reload the integration when options change so server TLS policy updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

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


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when config entry options change."""
    _LOGGER.info("Config entry updated for %s; reloading integration", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


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


async def _async_resolve_or_create_certs(
    hass: HomeAssistant,
    cert_file: str | None,
    key_file: str | None,
) -> tuple[str | None, str | None]:
    """Resolve certificate paths or create self-signed if missing.

    Preference order:
    1) User-provided paths if both exist
    2) Generate self-signed certs in /config with SYR domains
    """
    try:
        # 1) If user provided and both exist, use them
        if cert_file and key_file and Path(cert_file).exists() and Path(key_file).exists():
            _LOGGER.info("Using provided HTTPS cert/key (cert=%s, key=%s)", cert_file, key_file)
            return cert_file, key_file

        # 2) Generate self-signed certs with expected SYR hostnames
        target_cert = Path(cert_file or "/config/syr_cert.pem")
        target_key = Path(key_file or "/config/syr_key.pem")
        created = await _async_generate_self_signed_cert(hass, target_cert, target_key)
        if created:
            _LOGGER.info("Generated self-signed SYR HTTPS cert at %s", target_cert)
            return str(target_cert), str(target_key)
        else:
            _LOGGER.error("Failed to generate self-signed certificates")
            return None, None
    except Exception as err:
        _LOGGER.error("Error resolving/creating certificates: %s", err, exc_info=True)
        return None, None


async def _async_generate_self_signed_cert(
    hass: HomeAssistant,
    cert_path: Path,
    key_path: Path,
) -> bool:
    """Generate a self-signed RSA certificate for the SYR domains."""
    return await hass.async_add_executor_job(
        _generate_self_signed_cert_sync,
        cert_path,
        key_path,
    )


def _generate_self_signed_cert_sync(cert_path: Path, key_path: Path) -> bool:
    """Generate a self-signed RSA certificate for the SYR domains."""
    try:
        # Import cryptography lazily to avoid import cost if not needed
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
        import datetime as dt

        # Ensure parent directory exists
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate RSA private key
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Build subject/issuer (self-signed)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HANDLED_DOMAINS[0])])
        issuer = subject

        # Subject Alternative Names for handled domains
        san = x509.SubjectAlternativeName([x509.DNSName(d) for d in HANDLED_DOMAINS])

        # Validity window
        not_before = dt.datetime.utcnow() - dt.timedelta(days=1)
        not_after = dt.datetime.utcnow() + dt.timedelta(days=365 * 3)

        # Serial number
        serial_number = x509.random_serial_number()

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(serial_number)
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(san, critical=False)
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
        )

        cert = builder.sign(private_key=key, algorithm=hashes.SHA256())

        # Write private key (PEM)
        with key_path.open("wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Write certificate (PEM)
        with cert_path.open("wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        return True
    except Exception as err:
        _LOGGER.error("Failed generating self-signed cert: %s", err, exc_info=True)
        return False
