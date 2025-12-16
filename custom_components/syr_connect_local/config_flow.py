"""Config flow for SYR Connect Local integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HTTPS_PORT,
    CONF_HTTP_PORT,
    CONF_USE_HTTPS,
    DEFAULT_HTTPS_PORT,
    DEFAULT_HTTP_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SyrConnectLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SYR Connect Local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Only allow a single instance
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            try:
                # Validate port numbers
                http_port = user_input.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
                https_port = user_input.get(CONF_HTTPS_PORT, DEFAULT_HTTPS_PORT)

                if not (1 <= http_port <= 65535):
                    errors["http_port"] = "invalid_port"
                elif not (1 <= https_port <= 65535):
                    errors["https_port"] = "invalid_port"
                else:
                    # Create the entry
                    return self.async_create_entry(
                        title="SYR Connect Local",
                        data=user_input,
                    )

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HTTP_PORT, default=DEFAULT_HTTP_PORT
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_HTTPS_PORT, default=DEFAULT_HTTPS_PORT
                    ): vol.Coerce(int),
                    vol.Optional(CONF_USE_HTTPS, default=False): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SyrConnectLocalOptionsFlow:
        """Get the options flow for this handler."""
        return SyrConnectLocalOptionsFlow(config_entry)


class SyrConnectLocalOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SYR Connect Local."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate port numbers
                http_port = user_input.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
                https_port = user_input.get(CONF_HTTPS_PORT, DEFAULT_HTTPS_PORT)

                if not (1 <= http_port <= 65535):
                    errors["http_port"] = "invalid_port"
                elif not (1 <= https_port <= 65535):
                    errors["https_port"] = "invalid_port"
                else:
                    return self.async_create_entry(title="", data=user_input)

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Get current values
        current_http = self.config_entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
        current_https = self.config_entry.data.get(CONF_HTTPS_PORT, DEFAULT_HTTPS_PORT)
        current_use_https = self.config_entry.data.get(CONF_USE_HTTPS, False)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_HTTP_PORT, default=current_http): vol.Coerce(int),
                    vol.Optional(CONF_HTTPS_PORT, default=current_https): vol.Coerce(
                        int
                    ),
                    vol.Optional(CONF_USE_HTTPS, default=current_use_https): bool,
                }
            ),
            errors=errors,
        )
