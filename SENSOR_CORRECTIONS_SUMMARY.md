# Sensor Corrections Summary

This document summarizes the corrections made to align sensor naming with the official [syrconnect-protocol.md](https://github.com/Richard-Schaller/syrlex2mqtt/blob/main/doc/syrconnect-protocol.md).

## Problem Statement

The original implementation incorrectly named the `getCS1`, `getCS2`, and `getCS3` sensors as "Salt Level Tank 1/2/3". According to the official protocol documentation, these properties actually represent "Remaining capacity of the resin in tank 1, 2 or 3" measured in percentage (%).

## Changes Made

### 1. Sensor Name Corrections (sensor.py)

#### Before:
- `sensor.syr_salt_level_tank_1` - Salt Level Tank 1 (%)
- `sensor.syr_salt_level_tank_2` - Salt Level Tank 2 (%)
- `sensor.syr_salt_level_tank_3` - Salt Level Tank 3 (%)

#### After:
- `sensor.syr_resin_capacity_tank_1` - Resin Capacity Tank 1 (%)
- `sensor.syr_resin_capacity_tank_2` - Resin Capacity Tank 2 (%)
- `sensor.syr_resin_capacity_tank_3` - Resin Capacity Tank 3 (%)

**Rationale**: The protocol clearly states these are resin capacity measurements, not salt levels.

### 2. New Salt Sensors Added (sensor.py)

To provide actual salt level information, we added three new types of sensors:

#### Salt Volume (getSV1/2/3)
- `sensor.syr_salt_volume_tank_1` - Salt Volume Tank 1 (kg)
- `sensor.syr_salt_volume_tank_2` - Salt Volume Tank 2 (kg)
- `sensor.syr_salt_volume_tank_3` - Salt Volume Tank 3 (kg)

These show the actual amount of salt stored in each tank in kilograms.

#### Salt Duration (getSD1/2/3)
- `sensor.syr_salt_remaining_days_tank_1` - Salt Remaining Days Tank 1 (days)
- `sensor.syr_salt_remaining_days_tank_2` - Salt Remaining Days Tank 2 (days)
- `sensor.syr_salt_remaining_days_tank_3` - Salt Remaining Days Tank 3 (days)

These show how many days until the salt runs out in each tank.

### 3. Protocol Conversion Updates (protocol.py)

Added proper value conversion for the new sensor types:
- `getSV1/2/3` - Converted to integer (kg)
- `getSD1/2/3` - Converted to integer (days)
- `getSW1/2/3` - Converted to integer (weeks) - available for future use

### 4. Documentation Updates

#### const.py
- Added clarifying comment: "NOTE: getCS1/2/3 are 'Remaining capacity of the resin' in % - not actual salt level!"
- Updated inline comments for all salt-related properties

#### README.md
- Updated sensor table with corrected names
- Updated automation examples to use the correct sensor entities
- Added new sensors to the entity list

#### info.md
- Updated feature descriptions to mention both resin and salt monitoring

### 5. Future Enhancements Document (MISSING_SENSORS.md)

Created a comprehensive document cataloging all protocol sensors not yet exposed in Home Assistant, prioritized by usefulness:
- High priority: Leakage protection sensors (for SL models)
- Medium priority: Weekly consumption, regeneration details, flow details
- Low priority: Hourly consumption arrays, regeneration settings

## Regeneration Sensors Verification

The "Regeneration Active Tank 1/2/3" sensors were reviewed and confirmed to be correctly implemented:
- ✅ Use correct property keys: `getRG1`, `getRG2`, `getRG3`
- ✅ Use correct naming: "Regeneration Active Tank X"
- ✅ Use correct device class: `BinarySensorDeviceClass.RUNNING`
- ✅ Correctly interpret protocol values: "1" = regeneration running, "0" = not running
- ✅ Implemented as binary sensors (not regular sensors)

**No changes were needed for regeneration sensors.**

## Breaking Changes

⚠️ **Users will need to update their automations and dashboards** if they were using the old sensor names:

### Entity ID Changes:
- `sensor.syr_salt_level_tank_1` → `sensor.syr_resin_capacity_tank_1`
- `sensor.syr_salt_level_tank_2` → `sensor.syr_resin_capacity_tank_2`
- `sensor.syr_salt_level_tank_3` → `sensor.syr_resin_capacity_tank_3`

### New Entities Available:
- `sensor.syr_salt_volume_tank_1/2/3` (kg)
- `sensor.syr_salt_remaining_days_tank_1/2/3` (days)

## Migration Guide for Users

### For Resin Capacity Monitoring (formerly "Salt Level")
If you were monitoring resin capacity with percentage values:
```yaml
# OLD
entity_id: sensor.syr_salt_level_tank_1

# NEW
entity_id: sensor.syr_resin_capacity_tank_1
```

### For Actual Salt Level Monitoring
If you want to monitor actual salt levels, use the new sensors:
```yaml
# Salt volume in kilograms
entity_id: sensor.syr_salt_volume_tank_1

# OR salt duration in days
entity_id: sensor.syr_salt_remaining_days_tank_1
```

### Updated Automation Example
```yaml
# Before
automation:
  - alias: "SYR Low Salt Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.syr_salt_level_tank_1
        below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Salt level low ({{ states('sensor.syr_salt_level_tank_1') }}%)"

# After (using actual salt volume)
automation:
  - alias: "SYR Low Salt Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.syr_salt_volume_tank_1
        below: 2  # Alert when less than 2kg
    action:
      - service: notify.mobile_app
        data:
          message: "Salt level low ({{ states('sensor.syr_salt_volume_tank_1') }}kg)"

# OR using salt duration
automation:
  - alias: "SYR Low Salt Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.syr_salt_remaining_days_tank_1
        below: 7  # Alert when less than 7 days remaining
    action:
      - service: notify.mobile_app
        data:
          message: "Salt runs out in {{ states('sensor.syr_salt_remaining_days_tank_1') }} days"
```

## Technical Details

### Property Mappings
| Old Sensor Name | Property | New Sensor Name | Description | Unit |
|----------------|----------|-----------------|-------------|------|
| Salt Level Tank 1 | getCS1 | Resin Capacity Tank 1 | Remaining resin capacity | % |
| Salt Level Tank 2 | getCS2 | Resin Capacity Tank 2 | Remaining resin capacity | % |
| Salt Level Tank 3 | getCS3 | Resin Capacity Tank 3 | Remaining resin capacity | % |
| *(new)* | getSV1 | Salt Volume Tank 1 | Actual salt stored | kg |
| *(new)* | getSV2 | Salt Volume Tank 2 | Actual salt stored | kg |
| *(new)* | getSV3 | Salt Volume Tank 3 | Actual salt stored | kg |
| *(new)* | getSD1 | Salt Remaining Days Tank 1 | Salt duration | days |
| *(new)* | getSD2 | Salt Remaining Days Tank 2 | Salt duration | days |
| *(new)* | getSD3 | Salt Remaining Days Tank 3 | Salt duration | days |

### Files Modified
1. `custom_components/syr_connect_local/sensor.py` - Sensor definitions and names
2. `custom_components/syr_connect_local/const.py` - Property constants and comments
3. `custom_components/syr_connect_local/protocol.py` - Value conversion logic
4. `README.md` - User documentation
5. `info.md` - Integration description

### Files Created
1. `MISSING_SENSORS.md` - Future enhancement roadmap
2. `SENSOR_CORRECTIONS_SUMMARY.md` - This document

## References

- Protocol Documentation: https://github.com/Richard-Schaller/syrlex2mqtt/blob/main/doc/syrconnect-protocol.md
- Issue: Correct sensors according to syrconnect-protocol.md

## Testing Recommendations

Since this is a Home Assistant custom component for hardware devices:

1. **Manual Testing Required**: Connect a real SYR device and verify:
   - Resin capacity sensors show correct percentage values
   - Salt volume sensors show correct kilogram values
   - Salt duration sensors show correct day values
   - All sensors update properly during device communication

2. **Automation Testing**: 
   - Verify automations using the new entity IDs work correctly
   - Test threshold alerts with the new sensors

3. **Backward Compatibility**:
   - Old entity IDs will no longer exist
   - Users must update their configurations

## Conclusion

These changes align the integration with the official protocol specification, providing more accurate sensor naming and additional salt monitoring capabilities. The changes are breaking but necessary for correctness and to prevent user confusion about what the sensors actually measure.
