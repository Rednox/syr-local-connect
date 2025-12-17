# SYR Connect Local

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant custom integration that simulates the SYR Connect cloud server locally, enabling direct control and monitoring of SYR LEX Plus series water softening units without cloud dependency.

## Features

- **Local Control**: No cloud dependency - all communication stays in your local network
- **Multi-Device Support**: Handle multiple SYR devices simultaneously
- **Comprehensive Monitoring**: 
  - Water hardness (inlet/outlet)
  - Salt levels and remaining days
  - Water consumption statistics
  - Flow rate and pressure
  - Regeneration status and history
  - Temperature monitoring (LEX Plus SL models)
- **Control Functions**:
  - Start regeneration manually
  - Update device parameters
  - Power control
- **HACS Compatible**: Easy installation and updates through HACS

## Supported Devices

- SYR LEX Plus 10 Connect
- SYR LEX Plus 10 S Connect
- SYR LEX Plus 10 SL Connect (with leakage detection)
- Other LEX Plus series devices with Connect functionality

Firmware versions 1.7 and 1.9+ are supported (both HTTP and HTTPS).

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Rednox/syr-local-connect`
6. Select category "Integration"
7. Click "Add"
8. Find "SYR Connect Local" in the integration list
9. Click "Install"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/syr_connect_local` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Step 1: DNS Configuration (Required)

Before setting up the integration, you need to redirect your SYR device's cloud communication to your Home Assistant instance. This can be done in several ways:

#### Option 1: Router DNS Override

Most routers allow you to override DNS entries for specific domains. Add the following DNS overrides pointing to your Home Assistant IP address:

- `syrconnect.de` → Your Home Assistant IP
- `syrconnect.consoft.de` → Your Home Assistant IP
- `connect.saocal.pl` → Your Home Assistant IP
- `maintenance.syrconnect.de` → Your Home Assistant IP

#### Option 2: Local DNS Server (Pi-hole, AdGuard Home, etc.)

If you're running a local DNS server, add local DNS records:

**Pi-hole:**
```
# /etc/pihole/custom.list
192.168.1.100 syrconnect.de
192.168.1.100 syrconnect.consoft.de
192.168.1.100 connect.saocal.pl
192.168.1.100 maintenance.syrconnect.de
```

**AdGuard Home:**
Go to Filters → DNS rewrites and add entries for each domain.

#### Option 3: Router DHCP + DNS Server

Configure your router to assign your DNS server (Pi-hole/AdGuard) via DHCP to all devices.

### Step 2: Add Integration in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "SYR Connect Local"
4. Configure the server settings:
   - **HTTP Port**: Default 80 (for firmware 1.7)
   - **HTTPS Port**: Default 443 (for firmware 1.9+)
   - **Enable HTTPS**: Enable if using firmware 1.9+
5. Click **Submit**

The integration will start the local server and wait for your SYR device to connect. Once connected, devices will be automatically discovered and entities will be created.

### Step 3: Verify Connection

1. Check your Home Assistant logs for messages like:
   ```
   SYR Connect Local HTTP server started on port 80
   Device discovered: 123456789
   ```

2. Your SYR device should appear under **Settings** → **Devices & Services** → **SYR Connect Local**

## Entities

Once a device is discovered, the following entities are created:

### Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.syr_inlet_water_hardness` | Inlet water hardness | °dH |
| `sensor.syr_outlet_water_hardness` | Outlet water hardness (residual) | °dH |
| `sensor.syr_resin_capacity_tank_1` | Remaining resin capacity in tank 1 | % |
| `sensor.syr_salt_volume_tank_1` | Salt stored in tank 1 | kg |
| `sensor.syr_salt_remaining_days_tank_1` | Days until salt runs out in tank 1 | days |
| `sensor.syr_capacity_remaining` | Remaining softening capacity | L |
| `sensor.syr_water_flow` | Current water flow rate | L/min |
| `sensor.syr_water_pressure` | Water pressure | bar |
| `sensor.syr_water_consumption_today` | Today's water consumption | L |
| `sensor.syr_water_consumption_yesterday` | Yesterday's water consumption | L |
| `sensor.syr_water_consumption_this_month` | This month's consumption | L |
| `sensor.syr_water_consumption_last_month` | Last month's consumption | L |
| `sensor.syr_total_water_consumption` | Total water consumption | L |
| `sensor.syr_last_regeneration` | Last regeneration timestamp | - |
| `sensor.syr_total_regenerations` | Total number of regenerations | - |
| `sensor.syr_firmware_version` | Device firmware version | - |
| `sensor.syr_water_temperature` | Water temperature (SL models) | °C |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.syr_regeneration_active_tank_1` | Regeneration running on tank 1 |
| `binary_sensor.syr_flow_active` | Water currently flowing |
| `binary_sensor.syr_alarm` | Alarm/error status |

### Switches

| Entity | Description |
|--------|-------------|
| `switch.syr_power` | Device power state |

## Services

### `syr_connect_local.start_regeneration`

Start an immediate regeneration cycle.

```yaml
service: syr_connect_local.start_regeneration
data:
  serial: "123456789"
```

### `syr_connect_local.update_parameter`

Update a device parameter.

```yaml
service: syr_connect_local.update_parameter
data:
  serial: "123456789"
  parameter: "setRDO"  # Salt dosage
  value: "90"
```

## Automation Examples

### Notify when salt is low

```yaml
automation:
  - alias: "SYR Low Salt Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.syr_salt_volume_tank_1
        below: 2  # Alert when less than 2kg of salt remains
    action:
      - service: notify.mobile_app
        data:
          message: "SYR water softener salt level is low ({{ states('sensor.syr_salt_volume_tank_1') }}kg)"
```

### Start regeneration at specific time

```yaml
automation:
  - alias: "SYR Scheduled Regeneration"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.syr_capacity_remaining
        below: 500
    action:
      - service: syr_connect_local.start_regeneration
        data:
          serial: "123456789"
```

## Troubleshooting

### Device not connecting

1. **Check DNS redirection**: Verify that your SYR device is resolving the cloud domains to your Home Assistant IP
   - Use `nslookup syrconnect.de` from a device on the same network
   - It should return your Home Assistant IP

2. **Check firewall**: Ensure ports 80 (and/or 443) are accessible on your Home Assistant host

3. **Check logs**: Look for errors in Home Assistant logs:
   - **Settings** → **System** → **Logs**
   - Filter by "syr_connect_local"

4. **Verify firmware**: Check your device firmware version
   - Firmware 1.7: Uses HTTP (port 80)
   - Firmware 1.9+: Uses HTTPS (port 443)
   - Enable HTTPS in integration options if needed

### Device disconnects frequently

- The device polls every ~10 seconds. Check your network stability
- Ensure Home Assistant is always running
- Check system resources (CPU/memory) on Home Assistant host

### Entities not updating

- Check coordinator logs for errors
- Verify device is sending complete data
- Try restarting the integration

### Port already in use

If you get a "port already in use" error:

1. Check if another service is using port 80/443
2. Change the port in integration options to something else (e.g., 8080)
3. Update your DNS override to use the new port (e.g., `http://homeassistant:8080`)

## Protocol Reference

This integration implements the SYR Connect protocol as documented in:
https://github.com/Richard-Schaller/syrlex2mqtt/blob/main/doc/syrconnect-protocol.md

## Development

### Project Structure

```
custom_components/syr_connect_local/
├── __init__.py          # Integration setup and services
├── manifest.json        # Integration metadata
├── config_flow.py       # Configuration UI
├── const.py             # Constants and property mappings
├── coordinator.py       # Data update coordinator
├── server.py            # HTTP/HTTPS server implementation
├── protocol.py          # XML protocol handler
├── sensor.py            # Sensor entities
├── binary_sensor.py     # Binary sensor entities
├── switch.py            # Switch entities
├── services.yaml        # Service definitions
├── strings.json         # UI strings
└── translations/
    ├── en.json          # English translations
    └── de.json          # German translations
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Protocol documentation: [syrlex2mqtt](https://github.com/Richard-Schaller/syrlex2mqtt) by Richard Schaller
- Inspired by the [ioBroker.syrconnect](https://github.com/eifel-tech/ioBroker.syrconnect) project

## Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/Rednox/syr-local-connect/issues)
3. Create a [new issue](https://github.com/Rednox/syr-local-connect/issues/new) with:
   - Home Assistant version
   - Integration version
   - Device model and firmware version
   - Relevant log entries
   - Description of the problem
