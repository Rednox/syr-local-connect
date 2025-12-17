"""SYR Connect protocol handler for XML parsing and generation."""
import logging
import xml.etree.ElementTree as ET
from typing import Any

_LOGGER = logging.getLogger(__name__)

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
        """Create a command request dictionary (empty values for getters)."""
        return {cmd: "" for cmd in commands}

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
            
        # Numeric values (flow, pressure, capacity, resin capacity, max flow, max/min pressure)
        if property_name in ["getFLO", "getPRS", "getRES", "getCS1", "getCS2", "getCS3", 
                            "getMXF", "getMXP", "getMNP", "getMPR"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Salt volume in kg
        if property_name in ["getSV1", "getSV2", "getSV3"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Salt duration in days/weeks
        if property_name in ["getSD1", "getSD2", "getSD3", "getSW1", "getSW2", "getSW3"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
                
        # Water hardness
        if property_name in ["getIWH", "getOWH"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
                
        # Temperature (1/10 °C)
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
        if property_name in ["getRG1", "getRG2", "getRG3", "getPST"]:
            return value == "1"
            
        # Consumption values (all in liters)
        if property_name in ["getTOF", "getYEF", "getCWF", "getLWF", "getCMF", "getLMF", "getCOF",
                            "getTUF", "getWEF", "getTHF", "getFRF", "getSAF", "getSUF", 
                            "getTFO", "getUWF", "getDWF", "getFCO"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Regeneration settings (days, weekdays, hour, mode, type)
        if property_name in ["getRPD", "getRPW", "getRTH", "getRTM", "getRTY"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Regeneration counters
        if property_name in ["getTOR", "getNOR", "getSCR", "getINR", "getCYN"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Leakage detection numeric values
        if property_name in ["getNPS", "getDBD", "getDBT", "getDST", "getDCM", "getDOM", 
                            "getDPL", "getDTC", "getDRP", "getTN", "getLE", "getT2", "getTMP"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Leakage detection boolean/enum values
        if property_name in ["getAB", "getVLV", "getUL", "getDMA", "getALA", "getSMR", 
                            "getSRE", "getVAC", "getVAT"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Unknown numeric constants
        if property_name in ["getPA1", "getPA2", "getPA3", "getVS1", "getVS2", "getVS3",
                            "getBTM", "getBTS", "getCOR", "getDEN", "getDHC", "getFWM", 
                            "getFWS", "getHOT", "getLGO", "getMOF", "getREV", "getRPE", 
                            "getSDR", "getWHU", "getCHG", "getRDO"]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Default: return as string
        return value
