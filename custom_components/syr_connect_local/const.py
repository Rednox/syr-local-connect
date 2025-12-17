"""Constants for the SYR Connect Local integration."""
from typing import Final

DOMAIN: Final = "syr_connect_local"

# Configuration constants
CONF_HTTP_PORT: Final = "http_port"
CONF_HTTPS_PORT: Final = "https_port"
CONF_CERT_FILE: Final = "cert_file"
CONF_KEY_FILE: Final = "key_file"
CONF_USE_HTTPS: Final = "use_https"
CONF_DEBUG_ENDPOINTS: Final = "debug_endpoints"

# Default values
DEFAULT_HTTP_PORT: Final = 80
DEFAULT_HTTPS_PORT: Final = 443
DEFAULT_NAME: Final = "SYR Connect Local"

# Server domains to handle
HANDLED_DOMAINS: Final = [
    "syrconnect.de",
    "syrconnect.consoft.de",
    "connect.saocal.pl",
    "maintenance.syrconnect.de",
]

# API endpoints
ENDPOINT_BASIC: Final = "/WebServices/SyrConnectLimexWebService.asmx/GetBasicCommands"
ENDPOINT_ALL: Final = "/WebServices/SyrConnectLimexWebService.asmx/GetAllCommands"
ENDPOINT_BASIC_ALT: Final = "/GetBasicCommands"
ENDPOINT_ALL_ALT: Final = "/GetAllCommands"

# Property mappings for sensors
# Basic device information
PROPERTY_SERIAL: Final = "getSRN"  # Serial number
PROPERTY_VERSION: Final = "getVER"  # Firmware version
PROPERTY_FIRMWARE: Final = "getFIR"  # Firmware type (e.g., SLPS)
PROPERTY_TYPE: Final = "getTYP"  # Device type code
PROPERTY_NAME: Final = "getCNA"  # Device name
PROPERTY_MAC: Final = "getMAC"  # MAC address
PROPERTY_MANUFACTURER: Final = "getMAN"  # Manufacturer
PROPERTY_IP_ADDRESS: Final = "getIPA"  # IP address (deprecated)
PROPERTY_GATEWAY: Final = "getDGW"  # Gateway IP
PROPERTY_CODE: Final = "getCDE"  # Device code

# Water hardness
PROPERTY_INLET_HARDNESS: Final = "getIWH"  # Inlet water hardness
PROPERTY_OUTLET_HARDNESS: Final = "getOWH"  # Outlet water hardness (residual)
PROPERTY_HARDNESS_UNIT: Final = "getWHU"  # Water hardness unit (0=°dH, 1=°fH, 2=°eH)

# Salt levels (up to 3 tanks)
PROPERTY_SALT_TANK1: Final = "getCS1"  # Salt level tank 1 (%)
PROPERTY_SALT_TANK2: Final = "getCS2"  # Salt level tank 2 (%)
PROPERTY_SALT_TANK3: Final = "getCS3"  # Salt level tank 3 (%)
PROPERTY_SALT_RANGE1: Final = "getSS1"  # Salt range tank 1
PROPERTY_SALT_RANGE2: Final = "getSS2"  # Salt range tank 2
PROPERTY_SALT_RANGE3: Final = "getSS3"  # Salt range tank 3
PROPERTY_SALT_VOLUME1: Final = "getSV1"  # Salt volume tank 1
PROPERTY_SALT_VOLUME2: Final = "getSV2"  # Salt volume tank 2
PROPERTY_SALT_VOLUME3: Final = "getSV3"  # Salt volume tank 3
PROPERTY_SALT_DAYS1: Final = "getSD1"  # Salt lasts for n days tank 1
PROPERTY_SALT_DAYS2: Final = "getSD2"  # Salt lasts for n days tank 2
PROPERTY_SALT_DAYS3: Final = "getSD3"  # Salt lasts for n days tank 3
PROPERTY_SALT_WEEKS1: Final = "getSW1"  # Salt lasts for n weeks tank 1
PROPERTY_SALT_WEEKS2: Final = "getSW2"  # Salt lasts for n weeks tank 2
PROPERTY_SALT_WEEKS3: Final = "getSW3"  # Salt lasts for n weeks tank 3

# Water flow and pressure
PROPERTY_FLOW: Final = "getFLO"  # Current water flow (L/min)
PROPERTY_FLOW_COUNT: Final = "getFCO"  # Flow counter
PROPERTY_PRESSURE: Final = "getPRS"  # Water pressure (bar * 10)
PROPERTY_POWER_STATE: Final = "getPST"  # Power state (0=off, 1=on)

# Capacity and residual
PROPERTY_CAPACITY: Final = "getRES"  # Remaining capacity (L)
PROPERTY_SALT_DOSAGE: Final = "getRDO"  # Salt dosage setting

# Regeneration status (up to 3 tanks)
PROPERTY_REGEN_TANK1: Final = "getRG1"  # Regeneration active tank 1 (0/1)
PROPERTY_REGEN_TANK2: Final = "getRG2"  # Regeneration active tank 2 (0/1)
PROPERTY_REGEN_TANK3: Final = "getRG3"  # Regeneration active tank 3 (0/1)
PROPERTY_CYCLE_NUMBER: Final = "getCYN"  # Current cycle number
PROPERTY_CYCLE_TIME: Final = "getCYT"  # Current cycle time
PROPERTY_REGEN_TIME_TOTAL: Final = "getRTI"  # Total regeneration time
PROPERTY_LAST_REGEN: Final = "getLAR"  # Last regeneration timestamp
PROPERTY_TOTAL_REGEN: Final = "getTOR"  # Total regeneration count
PROPERTY_NORMAL_REGEN: Final = "getNOR"  # Normal regeneration count
PROPERTY_SERVICE_REGEN: Final = "getSCR"  # Service regeneration count
PROPERTY_INCOMPLETE_REGEN: Final = "getINR"  # Incomplete regeneration count

# Regeneration settings
PROPERTY_REGEN_MODE: Final = "getRTM"  # Regeneration mode
PROPERTY_REGEN_TIME_HOUR: Final = "getRTH"  # Regeneration time hour
PROPERTY_REGEN_WEEKDAYS: Final = "getRPW"  # Regeneration weekdays
PROPERTY_REGEN_PERIOD_DAYS: Final = "getRPD"  # Regeneration period days

# Alarm and status
PROPERTY_ALARM: Final = "getALM"  # Alarm status
PROPERTY_STATUS: Final = "getSTA"  # Status message

# Water consumption statistics
PROPERTY_CONSUMPTION_TODAY: Final = "getTOF"  # Today (L)
PROPERTY_CONSUMPTION_YESTERDAY: Final = "getYEF"  # Yesterday (L)
PROPERTY_CONSUMPTION_WEEK: Final = "getCWF"  # This week (L)
PROPERTY_CONSUMPTION_LAST_WEEK: Final = "getLWF"  # Last week (L)
PROPERTY_CONSUMPTION_MONTH: Final = "getCMF"  # This month (L)
PROPERTY_CONSUMPTION_LAST_MONTH: Final = "getLMF"  # Last month (L)
PROPERTY_CONSUMPTION_TOTAL: Final = "getCOF"  # Total (L)
PROPERTY_CONSUMPTION_WATER_WORKS: Final = "getDWF"  # Water works total

# Hourly consumption (24 values each)
PROPERTY_HOURLY_MONDAY: Final = "getMHF"  # Monday hourly
PROPERTY_HOURLY_TUESDAY: Final = "getUHF"  # Tuesday hourly
PROPERTY_HOURLY_WEDNESDAY: Final = "getWHF"  # Wednesday hourly
PROPERTY_HOURLY_THURSDAY: Final = "getHHF"  # Thursday hourly
PROPERTY_HOURLY_FRIDAY: Final = "getFHF"  # Friday hourly
PROPERTY_HOURLY_SATURDAY: Final = "getSHF"  # Saturday hourly
PROPERTY_HOURLY_SUNDAY: Final = "getNHF"  # Sunday hourly

# Date information
PROPERTY_DATE_DAY: Final = "getHED"  # Current day
PROPERTY_DATE_MONTH: Final = "getHEM"  # Current month
PROPERTY_DATE_YEAR: Final = "getHEY"  # Current year
PROPERTY_START_DAY: Final = "getHSD"  # Start day
PROPERTY_START_MONTH: Final = "getHSM"  # Start month
PROPERTY_START_YEAR: Final = "getHSY"  # Start year

# Leakage protection (LEX Plus SL models)
PROPERTY_VALVE_SHUTOFF: Final = "getAB"  # Valve shut-off (1=open, 2=closed)
PROPERTY_VALVE_STATUS: Final = "getVLV"  # Valve status
PROPERTY_LEAKAGE_VOLUME: Final = "getLE"  # Leakage volume setting
PROPERTY_LEAKAGE_TIME: Final = "getT2"  # Leakage time setting
PROPERTY_LEAKAGE_TEMP_DISABLE: Final = "getTMP"  # Temp disable (seconds)
PROPERTY_LEAKAGE_USER_PROFILE: Final = "getUL"  # User profile (0=present, 1=absent)
PROPERTY_TEMPERATURE: Final = "getCEL"  # Water temperature (1/10 °C)
PROPERTY_MICROLEAKAGE_COUNT: Final = "getNPS"  # Microleakage count

# Setters (commands)
SETTER_START_REGEN: Final = "setSIR"  # Start immediate regeneration (0 to trigger)
SETTER_VALVE_SHUTOFF: Final = "setAB"  # Set valve shut-off
SETTER_LEAKAGE_VOLUME: Final = "setLE"  # Set leakage volume
SETTER_LEAKAGE_TIME: Final = "setT2"  # Set leakage time
SETTER_LEAKAGE_TEMP_DISABLE: Final = "setTMP"  # Set temp disable
SETTER_LEAKAGE_USER_PROFILE: Final = "setUL"  # Set user profile

# Basic commands requested on first connection
BASIC_COMMANDS = [
    PROPERTY_SERIAL,
    PROPERTY_VERSION,
    PROPERTY_FIRMWARE,
    PROPERTY_TYPE,
    PROPERTY_NAME,
]

# All commands requested after identification
ALL_COMMANDS = [
    PROPERTY_SERIAL,
    PROPERTY_VERSION,
    PROPERTY_FIRMWARE,
    PROPERTY_TYPE,
    PROPERTY_NAME,
    PROPERTY_ALARM,
    PROPERTY_CODE,
    PROPERTY_SALT_TANK1,
    PROPERTY_SALT_TANK2,
    PROPERTY_SALT_TANK3,
    PROPERTY_CYCLE_NUMBER,
    PROPERTY_CYCLE_TIME,
    PROPERTY_DATE_DAY,
    PROPERTY_GATEWAY,
    PROPERTY_CONSUMPTION_WATER_WORKS,
    PROPERTY_FLOW_COUNT,
    PROPERTY_FLOW,
    PROPERTY_INCOMPLETE_REGEN,
    PROPERTY_IP_ADDRESS,
    PROPERTY_INLET_HARDNESS,
    PROPERTY_LAST_REGEN,
    PROPERTY_MAC,
    PROPERTY_MANUFACTURER,
    PROPERTY_NORMAL_REGEN,
    "getNOT",  # Notes (usually empty)
    PROPERTY_OUTLET_HARDNESS,
    PROPERTY_PRESSURE,
    PROPERTY_POWER_STATE,
    PROPERTY_SALT_DOSAGE,
    PROPERTY_CAPACITY,
    PROPERTY_REGEN_TANK1,
    PROPERTY_REGEN_TANK2,
    PROPERTY_REGEN_TANK3,
    PROPERTY_REGEN_PERIOD_DAYS,
    PROPERTY_REGEN_WEEKDAYS,
    PROPERTY_REGEN_TIME_HOUR,
    PROPERTY_REGEN_TIME_TOTAL,
    PROPERTY_REGEN_MODE,
    PROPERTY_SERVICE_REGEN,
    SETTER_START_REGEN,
    "getSRE",  # Unknown
    PROPERTY_SALT_RANGE1,
    PROPERTY_SALT_RANGE2,
    PROPERTY_SALT_RANGE3,
    PROPERTY_STATUS,
    PROPERTY_SALT_VOLUME1,
    PROPERTY_SALT_VOLUME2,
    PROPERTY_SALT_VOLUME3,
    PROPERTY_TOTAL_REGEN,
    "getVS1",  # Unknown
    "getVS2",  # Unknown
    "getVS3",  # Unknown
    PROPERTY_HARDNESS_UNIT,
]

# Additional properties for extended monitoring
EXTENDED_PROPERTIES = [
    PROPERTY_CONSUMPTION_TODAY,
    PROPERTY_CONSUMPTION_YESTERDAY,
    PROPERTY_CONSUMPTION_WEEK,
    PROPERTY_CONSUMPTION_LAST_WEEK,
    PROPERTY_CONSUMPTION_MONTH,
    PROPERTY_CONSUMPTION_LAST_MONTH,
    PROPERTY_CONSUMPTION_TOTAL,
    PROPERTY_DATE_MONTH,
    PROPERTY_DATE_YEAR,
    PROPERTY_START_DAY,
    PROPERTY_START_MONTH,
    PROPERTY_START_YEAR,
    PROPERTY_SALT_DAYS1,
    PROPERTY_SALT_DAYS2,
    PROPERTY_SALT_DAYS3,
    PROPERTY_SALT_WEEKS1,
    PROPERTY_SALT_WEEKS2,
    PROPERTY_SALT_WEEKS3,
]

# Leakage protection properties (for LEX Plus SL models)
LEAKAGE_PROPERTIES = [
    PROPERTY_VALVE_SHUTOFF,
    PROPERTY_VALVE_STATUS,
    PROPERTY_LEAKAGE_VOLUME,
    PROPERTY_LEAKAGE_TIME,
    PROPERTY_LEAKAGE_TEMP_DISABLE,
    PROPERTY_LEAKAGE_USER_PROFILE,
    PROPERTY_TEMPERATURE,
    PROPERTY_MICROLEAKAGE_COUNT,
]

# Events
EVENT_REGENERATION_STARTED: Final = f"{DOMAIN}_regeneration_started"
EVENT_REGENERATION_COMPLETED: Final = f"{DOMAIN}_regeneration_completed"
EVENT_ALARM_TRIGGERED: Final = f"{DOMAIN}_alarm_triggered"
EVENT_DEVICE_CONNECTED: Final = f"{DOMAIN}_device_connected"

# Service names
SERVICE_START_REGENERATION: Final = "start_regeneration"
SERVICE_UPDATE_PARAMETER: Final = "update_parameter"

# Data keys
DATA_COORDINATOR: Final = "coordinator"
DATA_SERVER: Final = "server"
DATA_DEVICES: Final = "devices"

# Dispatcher signals
SIGNAL_NEW_DEVICE: Final = f"{DOMAIN}_new_device"
