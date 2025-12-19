# Repository Setup for HACS

This document outlines the manual steps required to complete the HACS validation.

## Required GitHub Repository Topics

HACS requires that the repository has at least one topic set. To add topics to this repository:

1. Go to the repository on GitHub: https://github.com/Rednox/syr-local-connect
2. Click on the gear icon (⚙️) next to "About" on the right side
3. Add the following recommended topics:
   - `home-assistant`
   - `hacs`
   - `homeassistant-integration`
   - `syr`
   - `water-softener`
   - `local-control`
4. Click "Save changes"

### Why These Topics?

- `home-assistant` and `hacs` - Required for HACS discovery
- `homeassistant-integration` - Identifies this as a Home Assistant integration
- `syr` - Brand/manufacturer identifier
- `water-softener` - Device category
- `local-control` - Key feature identifier

After adding topics, the HACS validation error "The repository has no valid topics" will be resolved.
