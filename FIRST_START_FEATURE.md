# First-Start Mode Feature

## Overview

The KEA DHCP Lease Manager now includes a "first-start" mode that prevents the application from hanging during startup when the configuration is unconfigured or set to default values.

## Problem Solved

**Before:** When starting the application with a blank or default configuration pointing to `localhost`, the GUI would hang for a long time trying to connect to a non-existent KEA server, resulting in poor user experience.

**After:** The application now detects unconfigured state and immediately shows the configuration dialog without attempting to connect to KEA, providing a smooth first-time setup experience.

## How It Works

### Backend Detection (`app.py`)

The application now includes an `is_config_valid()` function that detects if the configuration is in an unconfigured state:

```python
def is_config_valid():
    """
    Check if the configuration is valid (not in first-start/unconfigured state).
    Returns True if config is properly set up, False if it's still using defaults.
    """
    kea_url = config['kea']['control_agent_url']
    
    # Check if using default localhost URL or empty URL
    if not kea_url or kea_url.strip() == '':
        return False
    
    # Check if it's still pointing to localhost (default config)
    if 'localhost' in kea_url.lower() or '127.0.0.1' in kea_url:
        return False
    
    return True
```

### Unconfigured State Handling

When the configuration is detected as invalid:

1. **Health Check Endpoint** (`/api/health`):
   - Returns `status: 'unconfigured'` instead of attempting connection
   - No timeout or hanging
   - HTTP 200 response with clear message

2. **Leases Endpoint** (`/api/leases`):
   - Returns `unconfigured: true` flag
   - Friendly error message directing user to configure
   - No KEA connection attempt

3. **Subnets Endpoint** (`/api/subnets`):
   - Returns empty subnets array with unconfigured flag
   - No KEA connection attempt

### Frontend Experience (`index.html`)

On page load, the application:

1. **Checks health status first** before loading any data
2. **Detects unconfigured state** from health response
3. **Shows warning banner** with clear instructions
4. **Automatically opens configuration modal** after 500ms delay
5. **Skips data loading** until properly configured

#### Visual Indicators

- **Connection Status**: Shows "Not Configured" in red
- **Warning Banner**: Yellow alert at top of page with first-time setup message
- **Configuration Modal**: Opens automatically with empty/default values
- **Error Messages**: Shows friendly "not configured" message instead of timeout errors

## User Flow

### First-Time Setup

1. User starts the application with default/blank config
2. Health check detects unconfigured state (instant, no timeout)
3. Yellow warning banner appears at top of page
4. Configuration modal opens automatically after brief delay
5. User enters KEA server details and saves
6. Page reloads with new configuration
7. Application connects to KEA and loads data normally

### Subsequent Starts

- If configuration is valid (not localhost), normal startup occurs
- Health check attempts connection to KEA
- Data loads as expected

## Configuration Validation Rules

The configuration is considered **invalid/unconfigured** if:

- KEA Control Agent URL is empty or blank
- URL contains "localhost" (case-insensitive)
- URL contains "127.0.0.1"

The configuration is considered **valid** if:

- URL points to a non-localhost address (e.g., `http://kea.tux42.au:8000`)
- URL is properly formatted with http:// or https://

## Benefits

✅ **No hanging or timeouts** on first start  
✅ **Clear user guidance** with automatic modal opening  
✅ **Instant feedback** - no waiting for connection attempts  
✅ **Better UX** - users know exactly what to do  
✅ **Prevents confusion** - clear unconfigured state vs connection errors  
✅ **Faster startup** - skips unnecessary connection attempts  

## API Changes

### Health Check Response

**Unconfigured State:**
```json
{
  "status": "unconfigured",
  "kea_connection": "not_configured",
  "message": "KEA server not configured. Please update configuration."
}
```

**Healthy State:**
```json
{
  "status": "healthy",
  "kea_connection": "ok"
}
```

**Unhealthy State:**
```json
{
  "status": "unhealthy",
  "kea_connection": "failed",
  "error": "Connection refused"
}
```

### Leases/Subnets Response (Unconfigured)

```json
{
  "success": false,
  "unconfigured": true,
  "error": "KEA server not configured. Please update configuration to connect."
}
```

## Testing

To test the first-start mode:

1. **Reset to default config:**
   ```bash
   cp config.yaml.template config.yaml
   ```

2. **Start the application:**
   ```bash
   python app.py
   # or in Docker
   docker-compose up
   ```

3. **Expected behavior:**
   - Page loads instantly (no hanging)
   - Yellow warning banner appears
   - Configuration modal opens automatically
   - Status shows "Not Configured"

4. **Configure KEA URL:**
   - Enter valid KEA server URL (not localhost)
   - Save configuration
   - Page reloads and connects normally

## Docker Considerations

When running in Docker with volume-mounted config:

```bash
docker run -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  awkto/kea-gui-reservations:latest
```

- If `config.yaml` has default localhost URL, first-start mode activates
- User can configure through web UI, but changes won't persist without writable volume
- For persistent config, mount as read-write: `-v $(pwd)/config.yaml:/app/config/config.yaml:rw`

## Future Enhancements

Possible improvements:

- [ ] Add "skip localhost check" option for legitimate localhost setups
- [ ] Persist "first-start complete" flag to only show banner once
- [ ] Add config validation before save (test KEA connection)
- [ ] Remember last successful config for rollback
- [ ] Add guided setup wizard with multiple steps
