"""Diagnostics support for SYR Connect Local integration."""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DATA_SERVER, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    try:
        domain_data = hass.data.get(DOMAIN, {})
        entry_data = domain_data.get(config_entry.entry_id, {})
        server = entry_data.get(DATA_SERVER)
        if not server:
            return {"error": "Server not initialized"}

        now = asyncio.get_event_loop().time()
        devices_info: list[dict[str, Any]] = []

        for serial, device in server.get_all_devices().items():
            last_seen_ago = None
            if device.last_seen:
                last_seen_ago = round(max(0.0, now - device.last_seen), 3)

            devices_info.append(
                {
                    "serial": serial,
                    "identified": device.is_identified,
                    "last_seen_seconds_ago": last_seen_ago,
                    "properties_count": len(device.properties),
                    "properties": device.properties,
                    "pending_commands_count": len(device.pending_commands),
                    "pending_commands": device.pending_commands,
                }
            )

        return {
            "server": {
                "http_port": server.http_port,
                "https_port": server.https_port if server.use_https else None,
                "use_https": server.use_https,
                "enable_debug_endpoints": server.enable_debug_endpoints,
                "devices_count": len(server.get_all_devices()),
            },
            "devices": devices_info,
        }
    except Exception as err:
        return {"error": f"Failed to gather diagnostics: {err}"}
