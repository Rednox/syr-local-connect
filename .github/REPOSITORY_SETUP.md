# Repository Setup for HACS Validation

This document outlines the **required manual step** to complete HACS validation.

## ⚠️ Action Required: Add GitHub Repository Topics

HACS validation requires at least one repository topic to be set. This is a **GitHub repository setting** that cannot be configured through code.

### Steps to Add Topics

1. Go to https://github.com/Rednox/syr-local-connect
2. Click the gear icon (⚙️) next to "About" in the right sidebar
3. In the "Topics" field, add the following topics (one at a time):
   ```
   home-assistant
   hacs
   homeassistant-integration
   syr
   water-softener
   local-control
   ```
4. Click "Save changes"

### Verification

After adding topics, the HACS validation workflow will pass. You can verify by:
- Checking the Actions tab to see if the HACS validation job passes
- The error "The repository has no valid topics" will no longer appear

### Note

The `hacs.json` file has been updated to remove the invalid `domains` field. This change is already committed and will resolve the second validation error automatically.
