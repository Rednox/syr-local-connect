# Missing Sensors from SYR Connect Protocol

This document lists sensors from the [syrconnect-protocol.md](https://github.com/Richard-Schaller/syrlex2mqtt/blob/main/doc/syrconnect-protocol.md) that are not yet exposed in Home Assistant but could be added in future enhancements.

## Currently Implemented Sensors

### Basic Device Information
- ✅ `getSRN` - Serial number (used internally)
- ✅ `getVER` - Firmware version
- ✅ `getFIR` - Firmware type (used internally)
- ✅ `getTYP` - Device type (used internally)
- ✅ `getCNA` - Device name (used internally)

### Water Hardness
- ✅ `getIWH` - Inlet water hardness
- ✅ `getOWH` - Outlet water hardness

### Resin and Salt
- ✅ `getCS1/2/3` - Resin capacity (%)
- ✅ `getSV1/2/3` - Salt volume (kg)
- ✅ `getSD1/2/3` - Salt lasts for n days

### Flow and Capacity
- ✅ `getFLO` - Current water flow
- ✅ `getPRS` - Water pressure
- ✅ `getRES` - Remaining capacity

### Regeneration
- ✅ `getRG1/2/3` - Regeneration active (binary sensors)
- ✅ `getLAR` - Last regeneration timestamp
- ✅ `getTOR` - Total regenerations

### Consumption
- ✅ `getTOF` - Today
- ✅ `getYEF` - Yesterday
- ✅ `getCMF` - This month
- ✅ `getLMF` - Last month
- ✅ `getCOF` - Total

### Leakage Protection
- ✅ `getCEL` - Water temperature (LEX Plus SL models)

### Alarms
- ✅ `getALM` - Alarm status

## Missing Sensors (Potentially Useful)

### Salt Information
- ❌ `getSS1/2/3` - Salt lasts for n weeks (unit: weeks)
- ❌ `getSW1/2/3` - Salt lasts for n weeks (seems duplicate of getSS)

**Note**: We currently expose `getSD1/2/3` (days). Adding weeks might be redundant.

### Water Consumption Statistics
- ❌ `getCWF` - Water consumption this week (L)
- ❌ `getLWF` - Water consumption last week (L)
- ❌ `getMHF` - Hourly consumption Monday (24 values)
- ❌ `getUHF` - Hourly consumption Tuesday (24 values)
- ❌ `getWHF` - Hourly consumption Wednesday (24 values)
- ❌ `getHHF` - Hourly consumption Thursday (24 values)
- ❌ `getFHF` - Hourly consumption Friday (24 values)
- ❌ `getSHF` - Hourly consumption Saturday (24 values)
- ❌ `getNHF` - Hourly consumption Sunday (24 values)

**Priority**: Medium - useful for detailed consumption tracking and dashboards

### Regeneration Details
- ❌ `getCYN` - Current cycle number during regeneration
- ❌ `getCYT` - Current cycle time during regeneration (format: "HH:MM")
- ❌ `getRTI` - Total regeneration time (format: "HH:MM")
- ❌ `getNOR` - Number of normal regenerations
- ❌ `getSCR` - Number of service regenerations
- ❌ `getINR` - Number of incomplete regenerations

**Priority**: Low to Medium - useful for detailed regeneration monitoring

### Regeneration Settings
- ❌ `getRTM` - Regeneration mode
- ❌ `getRTH` - Regeneration time hour
- ❌ `getRPW` - Regeneration weekdays
- ❌ `getRPD` - Regeneration period days
- ❌ `getRDO` - Salt dosage setting

**Priority**: Low - mostly configuration parameters, less useful as sensors

### Flow and Pressure Details
- ❌ `getMXF` - Maximum flow within this hour (L/min)
- ❌ `getFCO` - Flow counter
- ❌ `getPST` - Power state (0=off, 1=on)

**Priority**: Low to Medium
- `getMXF` could be useful for monitoring peak usage
- `getPST` could be exposed as a binary sensor for power state

### Leakage Protection (LEX Plus SL models)
- ❌ `getAB` - Valve shut-off (1=open, 2=closed)
- ❌ `getVLV` - Valve status (10=closed, 11=closing, 20=open, 21=opening)
- ❌ `getLE` - Leakage volume setting
- ❌ `getT2` - Leakage time setting
- ❌ `getTMP` - Temp disable leakage protection (seconds)
- ❌ `getUL` - User profile (0=present, 1=absent)
- ❌ `getNPS` - Microleakage count

**Priority**: High for LEX Plus SL models - important safety features

### Device Information
- ❌ `getMAC` - MAC address
- ❌ `getMAN` - Manufacturer
- ❌ `getIPA` - IP address (deprecated in protocol)
- ❌ `getDGW` - Gateway IP
- ❌ `getCDE` - Device code

**Priority**: Low - mostly static information, useful for diagnostics

### Status and Dates
- ❌ `getSTA` - Status message
- ❌ `getHED/HEM/HEY` - Current day/month/year
- ❌ `getHSD/HSM/HSY` - Start day/month/year

**Priority**: Low - date information can be obtained from Home Assistant

### Water Hardness Settings
- ❌ `getWHU` - Water hardness unit (0=°dH, 1=°fH, 2=°eH)

**Priority**: Low - mostly static configuration

### Unknown/Uncategorized
- ❌ `getDWF` - Water works total consumption
- ❌ Various unknown properties documented in the protocol

**Priority**: Very Low - unclear purpose or benefit

## Recommendations

### High Priority Additions (Future Enhancement)
1. **Leakage Protection Sensors** (for SL models):
   - Valve status (`getVLV`)
   - Valve shut-off (`getAB`)
   - Microleakage count (`getNPS`)
   - User profile (`getUL`)
   - Leakage settings (`getLE`, `getT2`)

2. **Weekly Consumption**:
   - `getCWF` - This week
   - `getLWF` - Last week

### Medium Priority Additions
1. **Regeneration Details**:
   - Cycle information during regeneration (`getCYN`, `getCYT`, `getRTI`)
   - Regeneration statistics (`getNOR`, `getSCR`, `getINR`)

2. **Flow Details**:
   - Maximum flow this hour (`getMXF`)
   - Power state as binary sensor (`getPST`)

### Low Priority Additions
1. **Hourly Consumption** (for detailed dashboards):
   - All daily hourly consumption arrays
   - Could be exposed as attributes or separate sensors

2. **Regeneration Settings** (mostly read-only configuration):
   - Mode, time, weekdays, period, dosage

## Notes

- Some sensors may not be available on all device models
- Some properties are read-only, others can be set (setters)
- The integration already handles most critical monitoring needs
- Additional sensors should be added based on user feedback and use cases
