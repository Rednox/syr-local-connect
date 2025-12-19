# SYR Connect Local v0.1.0 — Initial Release

**Local SYR water softener integration for Home Assistant — no cloud required.**

## ✨ Features

### 🔌 Local-Only Communication
- Intercept SYR device traffic via DNS override—eliminates cloud dependency
- Supports firmware versions 1.7+ (HTTP) and 1.9+ (HTTPS)
- Optional HTTPS with self-signed certificate support

### 📊 Comprehensive Device Monitoring
- **Water Quality**: Real-time inlet/outlet hardness, hardness unit configuration
- **Salt Management**: Track salt tank capacity, volume, and consumption estimates (3 tanks supported)
- **Water Flow**: Current flow rate and cumulative flow counter
- **System Status**: Water pressure, power state, alarm notifications

### 💧 Water Consumption Tracking
- Daily consumption (Today, Yesterday)
- Weekly metrics (This Week, Last Week)
- Monthly metrics (This Month, Last Month)
- Total consumption and daily breakdown (Monday-Sunday)
- Water works consumption tracking

### 🔄 Regeneration Control & Monitoring
- **Start Immediate Regeneration**: Trigger on-demand via button or service
- **Regeneration Status**: Per-tank monitoring (up to 3 tanks)
- **Regeneration Scheduling**: Configure interval (days), time (hour), and preferred weekdays
- **Regeneration History**: Track cycle numbers, total count, normal/service/incomplete regenerations
- **DVGW Compliance Alerts**: Automatic warnings if interval exceeds 4-day DVGW limit

### 🎛️ Remote Device Control
- Adjust regeneration intervals and schedules
- Set salt volumes and water hardness values per tank
- Configure hardness units (°dH, °fH, °eH)
- Outlet valve shutoff control (where supported by device)
- Generic parameter updates via service calls

### 📝 Entity Types

| Platform | Capabilities |
|----------|--------------|
| **Sensors** | Water hardness, salt volume/capacity, flow, pressure, remaining liters, regeneration counts, water consumption |
| **Binary Sensors** | Regeneration active (per tank), alarm status |
| **Buttons** | Start regeneration, manual refresh |
| **Numbers** | Regeneration intervals, salt volumes, water hardness (configurable ranges) |
| **Selects** | Regeneration weekday preferences (pre-defined schedules or custom) |
| **Time** | Regeneration schedule time picker |

### 🛠️ Developer Features
- Service calls for custom automation:
  - `syr_connect_local.start_regeneration`
  - `syr_connect_local.update_parameter`
- Diagnostic data export for troubleshooting
- INFO-level command logging for debugging

## 🚀 Setup

### Prerequisites
- Home Assistant 2023.1.0 or later
- Network access with DNS override capability
- Optional: HTTPS certificates for firmware 1.9+

### Installation Steps

1. **Add DNS Overrides** to route SYR domains to your Home Assistant host IP:
   - `syrconnect.de`
   - `syrconnect.consoft.de`
   - `connect.saocal.pl`
   - `maintenance.syrconnect.de`

2. **Configure HTTPS (optional for firmware 1.9+)**:
   - Place certificates in Home Assistant config:
     - `/config/syr_cert.pem`
     - `/config/syr_key.pem`

3. **Add Integration**:
   - Settings → Devices & Services → Add Integration → "SYR Connect Local"
   - Configure HTTP port (default: 80)
   - Configure HTTPS port (default: 443, only if device uses HTTPS)
   - Enable HTTPS if your device firmware supports it

4. **Connect Device**:
   - Entities appear after the device's first connection
   - Controls and updated readings appear after the device's next poll cycle

## 📋 Requirements

- Home Assistant 2023.1.0+
- aiohttp ≥ 3.9.0
- Network-level DNS override access
- SYR Connect device with local network connectivity

## ⚙️ Configuration

All configuration is handled through the Home Assistant UI during integration setup. No manual YAML configuration required.

## 🐛 Known Limitations

- Power switch control is experimental and commented out pending device-specific testing
- Multi-device support is available but currently untested in production environments
- DVGW compliance check is informational only (user responsible for regulatory compliance)

## 📖 Additional Resources

- **Documentation**: See [README.md](README.md) for detailed protocol information
- **Troubleshooting**: Enable debug logging and export diagnostics for support
- **Device Overview**: Device controls and sensors are organized in the device detail view

## 🙏 Credits

Built for Home Assistant and HACS integration ecosystem.

---

**Version**: 0.1.0  
**Release Date**: December 2025  
**License**: MIT
