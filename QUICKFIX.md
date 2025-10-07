# Quick Fix: No Leases Showing

## The Issue

Your KEA server (version 2.2.0) doesn't have the `lease_cmds` hook library loaded, which is required for the GUI to fetch and display DHCP leases via the API.

## The Fix

You need to enable the KEA lease commands hook library. Here's how:

### 1. Find the Hook Library

On your KEA server, run:

```bash
find /usr -name "libdhcp_lease_cmds.so" 2>/dev/null
```

Common locations:
- Ubuntu/Debian: `/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so`
- CentOS/RHEL: `/usr/lib64/kea/hooks/libdhcp_lease_cmds.so`

### 2. Edit KEA Configuration

Edit `/etc/kea/kea-dhcp4.conf` and add this section (adjust the path if needed):

```json
{
  "Dhcp4": {
    "hooks-libraries": [
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"
      }
    ],
    
    // ... rest of your existing configuration ...
  }
}
```

### 3. Restart KEA

```bash
sudo systemctl restart kea-dhcp4-server
sudo systemctl restart kea-ctrl-agent
```

### 4. Verify It Works

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"command": "list-commands", "service": ["dhcp4"]}' \
  http://localhost:8001
```

Look for `lease4-get-all` in the output.

### 5. Refresh the GUI

Restart your Python app and refresh your browser. Leases should now appear!

## Alternative: If Hook Library Isn't Installed

Install the KEA hook packages:

```bash
# Ubuntu/Debian
sudo apt-get install kea-ctrl-agent kea-admin kea-dhcp4-server

# CentOS/RHEL
sudo yum install kea-hooks
```

## For More Details

See the complete guide: `KEA_SETUP_GUIDE.md`
