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
# NOTE: getCS1/2/3 are "Remaining capacity of the resin" in % - not actual salt level!
PROPERTY_SALT_TANK1: Final = "getCS1"  # Resin capacity tank 1 (%)
PROPERTY_SALT_TANK2: Final = "getCS2"  # Resin capacity tank 2 (%)
PROPERTY_SALT_TANK3: Final = "getCS3"  # Resin capacity tank 3 (%)
PROPERTY_SALT_RANGE1: Final = "getSS1"  # Salt range tank 1
PROPERTY_SALT_RANGE2: Final = "getSS2"  # Salt range tank 2
PROPERTY_SALT_RANGE3: Final = "getSS3"  # Salt range tank 3
PROPERTY_SALT_VOLUME1: Final = "getSV1"  # Salt volume tank 1 (kg)
PROPERTY_SALT_VOLUME2: Final = "getSV2"  # Salt volume tank 2 (kg)
PROPERTY_SALT_VOLUME3: Final = "getSV3"  # Salt volume tank 3 (kg)
PROPERTY_SALT_DAYS1: Final = "getSD1"  # Salt lasts for n days tank 1
PROPERTY_SALT_DAYS2: Final = "getSD2"  # Salt lasts for n days tank 2
PROPERTY_SALT_DAYS3: Final = "getSD3"  # Salt lasts for n days tank 3
PROPERTY_SALT_WEEKS1: Final = "getSW1"  # Salt lasts for n weeks tank 1
PROPERTY_SALT_WEEKS2: Final = "getSW2"  # Salt lasts for n weeks tank 2
PROPERTY_SALT_WEEKS3: Final = "getSW3"  # Salt lasts for n weeks tank 3

# Water flow and pressure
PROPERTY_FLOW: Final = "getFLO"  # Current water flow (L/min)
PROPERTY_FLOW_COUNT: Final = "getFCO"  # Flow counter
PROPERTY_MAX_FLOW: Final = "getMXF"  # Maximum flow (L/min)
PROPERTY_PRESSURE: Final = "getPRS"  # Water pressure (bar * 10)
PROPERTY_MAX_PRESSURE: Final = "getMXP"  # Maximum pressure
PROPERTY_MIN_PRESSURE: Final = "getMNP"  # Minimum pressure
PROPERTY_POWER_STATE: Final = "getPST"  # Power state (0=off, 1=on)
PROPERTY_MICROPULSE_RATE: Final = "getMPR"  # Micropulse rate
PROPERTY_CHARGE: Final = "getCHG"  # Charge setting

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
PROPERTY_REGEN_TYPE: Final = "getRTY"  # Regeneration type
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

# Daily consumption (for each day of the week)
PROPERTY_CONSUMPTION_TUESDAY_DAILY: Final = "getTUF"  # Tuesday daily consumption (L)
PROPERTY_CONSUMPTION_WEDNESDAY_DAILY: Final = "getWEF"  # Wednesday daily consumption (L)
PROPERTY_CONSUMPTION_THURSDAY_DAILY: Final = "getTHF"  # Thursday daily consumption (L)
PROPERTY_CONSUMPTION_FRIDAY_DAILY: Final = "getFRF"  # Friday daily consumption (L)
PROPERTY_CONSUMPTION_SATURDAY_DAILY: Final = "getSAF"  # Saturday daily consumption (L)
PROPERTY_CONSUMPTION_SUNDAY_DAILY: Final = "getSUF"  # Sunday daily consumption (L)
PROPERTY_CONSUMPTION_TOTAL_FLOW: Final = "getTFO"  # Total flow consumption
PROPERTY_CONSUMPTION_UNKNOWN_WEEKLY: Final = "getUWF"  # Unknown weekly consumption

# Date information
PROPERTY_DATE: Final = "getDAT"  # Current date
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

# Leakage protection - unknown/undocumented properties (LEX Plus SL models)
PROPERTY_LEAKAGE_DMA: Final = "getDMA"  # Leakage detection DMA (unknown)
PROPERTY_LEAKAGE_AVO: Final = "getAVO"  # Leakage detection AVO (unknown)
PROPERTY_LEAKAGE_BSA: Final = "getBSA"  # Leakage detection BSA (unknown)
PROPERTY_LEAKAGE_DBD: Final = "getDBD"  # Leakage detection DBD (unknown)
PROPERTY_LEAKAGE_DBT: Final = "getDBT"  # Leakage detection DBT (unknown)
PROPERTY_LEAKAGE_DST: Final = "getDST"  # Leakage detection DST (unknown)
PROPERTY_LEAKAGE_DCM: Final = "getDCM"  # Leakage detection DCM (unknown)
PROPERTY_LEAKAGE_DOM: Final = "getDOM"  # Leakage detection DOM (unknown)
PROPERTY_LEAKAGE_DPL: Final = "getDPL"  # Leakage detection DPL (unknown)
PROPERTY_LEAKAGE_DTC: Final = "getDTC"  # Leakage detection DTC (unknown)
PROPERTY_LEAKAGE_DRP: Final = "getDRP"  # Leakage detection DRP (unknown)
PROPERTY_LEAKAGE_ALA: Final = "getALA"  # Leakage alarm (unknown)
PROPERTY_LEAKAGE_TN: Final = "getTN"  # Leakage TN (unknown)
PROPERTY_LEAKAGE_SMR: Final = "getSMR"  # Leakage SMR (unknown)
PROPERTY_LEAKAGE_SRE: Final = "getSRE"  # Leakage SRE (unknown)
PROPERTY_LEAKAGE_VAC: Final = "getVAC"  # Leakage VAC (unknown)
PROPERTY_LEAKAGE_VAT: Final = "getVAT"  # Leakage VAT (unknown)

# Network settings
PROPERTY_LAN_MODE: Final = "getLAN"  # LAN mode setting
PROPERTY_NETWORK_CONFIG: Final = "getNET"  # Network configuration
PROPERTY_DNS_SERVER: Final = "getDNS"  # DNS server address
PROPERTY_SUBNET_MASK: Final = "getSNM"  # Subnet mask
PROPERTY_TIMEZONE: Final = "getTMZ"  # Timezone setting

# Unknown/undocumented properties
PROPERTY_PARAM1: Final = "getPA1"  # Parameter 1 (unknown)
PROPERTY_PARAM2: Final = "getPA2"  # Parameter 2 (unknown)
PROPERTY_PARAM3: Final = "getPA3"  # Parameter 3 (unknown)
PROPERTY_VALUE1: Final = "getVS1"  # Value 1 (unknown)
PROPERTY_VALUE2: Final = "getVS2"  # Value 2 (unknown)
PROPERTY_VALUE3: Final = "getVS3"  # Value 3 (unknown)
PROPERTY_NOTES: Final = "getNOT"  # Notes (usually empty)
PROPERTY_BTM: Final = "getBTM"  # BTM (unknown constant)
PROPERTY_BTS: Final = "getBTS"  # BTS (unknown constant)
PROPERTY_COR: Final = "getCOR"  # COR (unknown constant)
PROPERTY_DEN: Final = "getDEN"  # DEN (unknown constant)
PROPERTY_DHC: Final = "getDHC"  # DHC (unknown constant)
PROPERTY_FWM: Final = "getFWM"  # FWM (unknown constant)
PROPERTY_FWS: Final = "getFWS"  # FWS (unknown constant)
PROPERTY_HOT: Final = "getHOT"  # HOT (unknown constant)
PROPERTY_IPH: Final = "getIPH"  # IPH (unknown constant)
PROPERTY_LGO: Final = "getLGO"  # LGO (unknown constant)
PROPERTY_MOF: Final = "getMOF"  # MOF (unknown constant)
PROPERTY_REV: Final = "getREV"  # REV (unknown constant)
PROPERTY_RPE: Final = "getRPE"  # RPE (unknown constant)
PROPERTY_SDR: Final = "getSDR"  # SDR (unknown constant)

# Setters (commands)
SETTER_START_REGEN: Final = "setSIR"  # Start immediate regeneration (0 to trigger)
SETTER_VALVE_SHUTOFF: Final = "setAB"  # Set valve shut-off
SETTER_LEAKAGE_VOLUME: Final = "setLE"  # Set leakage volume
SETTER_LEAKAGE_TIME: Final = "setT2"  # Set leakage time
SETTER_LEAKAGE_TEMP_DISABLE: Final = "setTMP"  # Set temp disable
SETTER_LEAKAGE_USER_PROFILE: Final = "setUL"  # Set user profile

# Configuration setters
SETTER_SALT_VOLUME1: Final = "setSV1"  # Set salt volume tank 1 (kg)
SETTER_SALT_VOLUME2: Final = "setSV2"  # Set salt volume tank 2 (kg)
SETTER_SALT_VOLUME3: Final = "setSV3"  # Set salt volume tank 3 (kg)
SETTER_REGEN_PERIOD_DAYS: Final = "setRPD"  # Set regeneration period (days)
SETTER_REGEN_WEEKDAYS: Final = "setRPW"  # Set regeneration weekdays
SETTER_REGEN_TIME_HOUR: Final = "setRTH"  # Set regeneration time (hour)
SETTER_REGEN_MODE: Final = "setRTM"  # Set regeneration mode
SETTER_REGEN_TYPE: Final = "setRTY"  # Set regeneration type
SETTER_INLET_HARDNESS: Final = "setIWH"  # Set inlet water hardness
SETTER_OUTLET_HARDNESS: Final = "setOWH"  # Set outlet water hardness (residual)
SETTER_HARDNESS_UNIT: Final = "setWHU"  # Set water hardness unit
SETTER_SALT_DOSAGE: Final = "setRDO"  # Set salt dosage
SETTER_POWER_STATE: Final = "setPST"  # Set power state
SETTER_WATER_WORKS_FLOW: Final = "setDWF"  # Set water works flow
SETTER_FLOW_COUNTER: Final = "setFCO"  # Set flow counter
SETTER_MICROPULSE_RATE: Final = "setMPR"  # Set micropulse rate
SETTER_CHARGE: Final = "setCHG"  # Set charge

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
    PROPERTY_NOTES,  # Notes (usually empty)
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
    PROPERTY_LEAKAGE_SRE,  # Unknown
    PROPERTY_SALT_RANGE1,
    PROPERTY_SALT_RANGE2,
    PROPERTY_SALT_RANGE3,
    PROPERTY_STATUS,
    PROPERTY_SALT_VOLUME1,
    PROPERTY_SALT_VOLUME2,
    PROPERTY_SALT_VOLUME3,
    PROPERTY_TOTAL_REGEN,
    PROPERTY_VALUE1,  # Unknown
    PROPERTY_VALUE2,  # Unknown
    PROPERTY_VALUE3,  # Unknown
    PROPERTY_HARDNESS_UNIT,
    # Additional properties from protocol
    PROPERTY_PARAM1,
    PROPERTY_PARAM2,
    PROPERTY_PARAM3,
    PROPERTY_DEN,
    PROPERTY_REV,
    PROPERTY_IPH,
    PROPERTY_BTM,
    PROPERTY_BTS,
    PROPERTY_COR,
    PROPERTY_DHC,
    PROPERTY_FWM,
    PROPERTY_FWS,
    PROPERTY_HOT,
    PROPERTY_LGO,
    PROPERTY_MOF,
    PROPERTY_RPE,
    PROPERTY_SDR,
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
    PROPERTY_CONSUMPTION_TUESDAY_DAILY,
    PROPERTY_CONSUMPTION_WEDNESDAY_DAILY,
    PROPERTY_CONSUMPTION_THURSDAY_DAILY,
    PROPERTY_CONSUMPTION_FRIDAY_DAILY,
    PROPERTY_CONSUMPTION_SATURDAY_DAILY,
    PROPERTY_CONSUMPTION_SUNDAY_DAILY,
    PROPERTY_CONSUMPTION_TOTAL_FLOW,
    PROPERTY_CONSUMPTION_UNKNOWN_WEEKLY,
    PROPERTY_DATE,
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
    PROPERTY_MAX_FLOW,
    PROPERTY_MAX_PRESSURE,
    PROPERTY_MIN_PRESSURE,
    PROPERTY_MICROPULSE_RATE,
    PROPERTY_CHARGE,
    PROPERTY_REGEN_TYPE,
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
    # Unknown leakage properties
    PROPERTY_LEAKAGE_DMA,
    PROPERTY_LEAKAGE_AVO,
    PROPERTY_LEAKAGE_BSA,
    PROPERTY_LEAKAGE_DBD,
    PROPERTY_LEAKAGE_DBT,
    PROPERTY_LEAKAGE_DST,
    PROPERTY_LEAKAGE_DCM,
    PROPERTY_LEAKAGE_DOM,
    PROPERTY_LEAKAGE_DPL,
    PROPERTY_LEAKAGE_DTC,
    PROPERTY_LEAKAGE_DRP,
    PROPERTY_LEAKAGE_ALA,
    PROPERTY_LEAKAGE_TN,
    PROPERTY_LEAKAGE_SMR,
    PROPERTY_LEAKAGE_SRE,
    PROPERTY_LEAKAGE_VAC,
    PROPERTY_LEAKAGE_VAT,
]

# Network configuration properties
NETWORK_PROPERTIES = [
    PROPERTY_LAN_MODE,
    PROPERTY_NETWORK_CONFIG,
    PROPERTY_DNS_SERVER,
    PROPERTY_SUBNET_MASK,
    PROPERTY_TIMEZONE,
]

# Signals
SIGNAL_NEW_DEVICE: Final = f"{DOMAIN}_new_device"
SIGNAL_DEVICE_UPDATE: Final = f"{DOMAIN}_device_update"

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
