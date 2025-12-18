"""SYR Connect protocol handler for XML parsing and generation."""
import logging
import xml.etree.ElementTree as ET
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Property groups for type conversion
# Numeric integer properties
NUMERIC_INT_PROPERTIES = [
    "getFLO", "getPRS", "getRES", "getCS1", "getCS2", "getCS3",
    "getMXF", "getMXP", "getMNP", "getMPR",
    "getSV1", "getSV2", "getSV3",
    "getSD1", "getSD2", "getSD3", "getSW1", "getSW2", "getSW3",
    "getIWH", "getOWH",
    "getTOR", "getNOR", "getSCR", "getINR", "getCYN",
    "getRPD", "getRPW", "getRTH", "getRTM", "getRTY",
    "getFCO", "getDWF",
]

# Consumption values in liters
CONSUMPTION_PROPERTIES = [
    "getTOF", "getYEF", "getCWF", "getLWF", "getCMF", "getLMF", "getCOF",
    "getTUF", "getWEF", "getTHF", "getFRF", "getSAF", "getSUF",
    "getTFO", "getUWF",
]

# Leakage detection numeric properties
LEAKAGE_NUMERIC_PROPERTIES = [
    "getNPS", "getDBD", "getDBT", "getDST", "getDCM", "getDOM",
    "getDPL", "getDTC", "getDRP", "getTN", "getLE", "getT2", "getTMP",
    "getAB", "getVLV", "getUL", "getDMA", "getALA", "getSMR",
    "getSRE", "getVAC", "getVAT",
]

# Documented numeric properties (settings and constants)
DOCUMENTED_NUMERIC_PROPERTIES = [
    "getWHU", "getCHG", "getRDO",
]

# Unknown/undocumented numeric properties
UNKNOWN_NUMERIC_PROPERTIES = [
    "getPA1", "getPA2", "getPA3", "getVS1", "getVS2", "getVS3",
    "getBTM", "getBTS", "getCOR", "getDEN", "getDHC", "getFWM",
    "getFWS", "getHOT", "getLGO", "getMOF", "getREV", "getRPE", "getSDR",
]

# Boolean properties (0/1 values)
BOOLEAN_PROPERTIES = ["getRG1", "getRG2", "getRG3", "getPST"]


class SyrProtocol:
    """Handle SYR Connect XML protocol parsing and generation."""

    @staticmethod
    def parse_xml(xml_str: str) -> dict[str, str]:
        """Parse XML from device into property dictionary.
        
        Expected format:
        <?xml version="1.0" encoding="utf-8"?>
        <sc version="1.0">
            <d>
                <c n="property" v="value" />
                ...
            </d>
        </sc>
        """
        try:
            root = ET.fromstring(xml_str)
            properties = {}
            
            # Find all <c> elements under <sc><d>
            device_elem = root.find("d")
            if device_elem is not None:
                for cmd_elem in device_elem.findall("c"):
                    name = cmd_elem.get("n")
                    value = cmd_elem.get("v")
                    if name:
                        properties[name] = value or ""
            
            _LOGGER.debug("Parsed XML properties: %s", properties)
            return properties
            
        except ET.ParseError as err:
            _LOGGER.error("Failed to parse XML: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Unexpected error parsing XML: %s", err)
            return {}

    @staticmethod
    def generate_xml(properties: dict[str, str]) -> str:
        """Generate XML response with requested properties.
        
        Output format:
        <?xml version="1.0" encoding="utf-8"?>
        <sc version="1.0">
            <d>
                <c n="property" v="value" />
                ...
            </d>
        </sc>
        """
        try:
            # Create root element
            root = ET.Element("sc", version="1.0")
            device_elem = ET.SubElement(root, "d")
            
            # Add command elements
            for name, value in properties.items():
                ET.SubElement(device_elem, "c", n=name, v=str(value))
            
            # Convert to string with XML declaration
            xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_str += ET.tostring(root, encoding="unicode")
            
            _LOGGER.debug("Generated XML response with %d properties", len(properties))
            return xml_str
            
        except Exception as err:
            _LOGGER.error("Failed to generate XML: %s", err)
            return '<?xml version="1.0" encoding="utf-8"?><sc version="1.0"><d></d></sc>'

    @staticmethod
    def create_command_request(commands: list[str]) -> dict[str, str]:
        """Create a command request dictionary for getters only.

        Defensively filter out any setters to avoid accidentally sending
        commands in periodic polling responses.
        """
        return {cmd: "" for cmd in commands if SyrProtocol.is_getter(cmd)}

    @staticmethod
    def is_getter(property_name: str) -> bool:
        """Check if a property is a getter."""
        return property_name.startswith("get")

    @staticmethod
    def is_setter(property_name: str) -> bool:
        """Check if a property is a setter."""
        return property_name.startswith("set")

    @staticmethod
    def convert_value(property_name: str, value: str) -> Any:
        """Convert string value to appropriate type based on property."""
        if not value:
            return None
            
        # Temperature (1/10 °C) - special float conversion
        if property_name == "getCEL":
            try:
                return float(value) / 10.0
            except (ValueError, TypeError):
                return None
                
        # UNIX timestamp
        if property_name == "getLAR":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
                
        # Boolean values (0/1) - regeneration status, power state
        if property_name in BOOLEAN_PROPERTIES:
            return value == "1"
            
        # Numeric integer properties (flow, pressure, capacity, etc.)
        if property_name in NUMERIC_INT_PROPERTIES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Consumption values (all in liters)
        if property_name in CONSUMPTION_PROPERTIES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Leakage detection numeric values
        if property_name in LEAKAGE_NUMERIC_PROPERTIES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Documented numeric properties (settings)
        if property_name in DOCUMENTED_NUMERIC_PROPERTIES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Unknown/undocumented numeric constants
        if property_name in UNKNOWN_NUMERIC_PROPERTIES:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Default: return as string
        return value
