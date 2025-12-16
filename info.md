# SYR Connect Local

Local control for SYR LEX Plus water softening units without cloud dependency.

## What it does

This integration simulates the SYR Connect cloud server locally, allowing you to:

- Monitor water hardness, salt levels, and consumption
- Track regeneration cycles
- Control your SYR device locally
- Eliminate cloud dependency

## Supported Devices

- SYR LEX Plus 10 Connect
- SYR LEX Plus 10 S Connect  
- SYR LEX Plus 10 SL Connect (with leakage detection)
- Firmware versions 1.7 and 1.9+

## Important Setup Step

⚠️ **DNS Configuration Required**: You must configure your router or DNS server to redirect SYR cloud domains to your Home Assistant instance. See the [README](https://github.com/Rednox/syr-local-connect#step-1-dns-configuration-required) for detailed instructions.

## Features

✅ Comprehensive monitoring (hardness, salt, flow, pressure, consumption)  
✅ Manual regeneration control  
✅ Multi-device support  
✅ Automatic device discovery  
✅ No cloud dependency  
✅ Works with firmware 1.7 and 1.9+  

## Quick Start

1. Install via HACS
2. Configure DNS redirection (see README)
3. Add integration via Settings → Devices & Services
4. Configure port settings (default: HTTP 80, HTTPS 443)
5. Device will be auto-discovered when it connects

For detailed setup instructions, see the [full README](https://github.com/Rednox/syr-local-connect).
