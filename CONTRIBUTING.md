# Contributing to SYR Connect Local

Thank you for your interest in contributing to the SYR Connect Local integration!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Home Assistant development environment (optional but recommended)
- A SYR LEX Plus device for testing (optional)

### Local Development

1. Copy the `custom_components/syr_connect_local` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI

### Testing Without Hardware

You can test the protocol implementation without actual hardware:

```python
python3 -c "
import sys
sys.path.insert(0, 'custom_components/syr_connect_local')
from protocol import SyrProtocol

# Test XML parsing
protocol = SyrProtocol()
test_xml = '...'
properties = protocol.parse_xml(test_xml)
print(properties)
"
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

Before submitting a PR:

1. Verify all Python files compile: `python3 -m py_compile custom_components/syr_connect_local/*.py`
2. Test with actual hardware if possible
3. Check the Home Assistant logs for errors

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include test results if applicable
- Update documentation if needed
- Ensure all checks pass

## Reporting Issues

When reporting an issue, please include:

- Home Assistant version
- Integration version
- Device model and firmware version
- Relevant log entries
- Steps to reproduce

## Protocol Documentation

The integration implements the SYR Connect protocol documented here:
https://github.com/Richard-Schaller/syrlex2mqtt/blob/main/doc/syrconnect-protocol.md

If you discover new protocol features or properties, please contribute them back to the documentation.

## Questions?

Feel free to open an issue for questions or discussions.
