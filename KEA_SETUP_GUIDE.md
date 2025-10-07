# KEA Setup Guide for Lease Management GUI

## Problem: No Leases Showing in GUI

If you're seeing "No leases found" or errors like `'lease4-get-all' command not supported`, it means the **lease_cmds hook library** is not enabled in your KEA configuration.

## Solution: Enable the lease_cmds Hook Library

### Step 1: Locate Your KEA Configuration File

Find your KEA DHCPv4 configuration file (usually one of these):
- `/etc/kea/kea-dhcp4.conf`
- `/etc/kea/kea.conf`
- `/usr/local/etc/kea/kea-dhcp4.conf`

### Step 2: Find the Hook Library File

The hook library is typically installed with KEA. Find it using:

```bash
# On Linux
find /usr -name "libdhcp_lease_cmds.so" 2>/dev/null

# Common locations:
# Debian/Ubuntu:  /usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so
# CentOS/RHEL:    /usr/lib64/kea/hooks/libdhcp_lease_cmds.so
# FreeBSD:        /usr/local/lib/kea/hooks/libdhcp_lease_cmds.so
```

### Step 3: Edit KEA Configuration

Open your `kea-dhcp4.conf` file and add the `hooks-libraries` section:

```json
{
  "Dhcp4": {
    "hooks-libraries": [
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"
      }
    ],
    
    // Your existing configuration...
    "interfaces-config": {
      // ...
    },
    "lease-database": {
      // ...
    },
    "subnet4": [
      // ...
    ]
  }
}
```

**Important Notes:**
- If you already have a `hooks-libraries` array, just add the lease_cmds library to it
- Make sure the path matches where the library is installed on your system
- The configuration must be valid JSON

### Step 4: Restart KEA Services

```bash
# Restart KEA DHCP4 server
sudo systemctl restart kea-dhcp4-server

# Restart KEA Control Agent
sudo systemctl restart kea-ctrl-agent

# Check status
sudo systemctl status kea-dhcp4-server
sudo systemctl status kea-ctrl-agent
```

### Step 5: Verify the Hook is Loaded

Test that the lease commands are now available:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"command": "list-commands", "service": ["dhcp4"]}' \
  http://localhost:8000
```

You should see these commands in the output:
- `lease4-get`
- `lease4-get-all`
- `lease4-get-page`
- `lease4-add`
- `lease4-del`
- `lease4-update`
- `lease4-wipe`

### Step 6: Test Lease Retrieval

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"command": "lease4-get-all", "service": ["dhcp4"]}' \
  http://localhost:8000
```

This should return a JSON response with all current leases.

### Step 7: Refresh the GUI

Now restart your GUI application and refresh the browser. You should see all active leases!

## Troubleshooting

### Error: "cannot open shared object file"

The hook library isn't installed. Install it:

```bash
# Debian/Ubuntu
sudo apt-get install kea-ctrl-agent kea-admin kea-dhcp4-server

# CentOS/RHEL
sudo yum install kea-hooks
```

### Error: "parse error at ..."

Your JSON configuration is invalid. Common issues:
- Missing or extra commas
- Comments (JSON doesn't support `//` comments in strict mode)
- Check with: `sudo kea-dhcp4 -t /etc/kea/kea-dhcp4.conf`

### KEA Won't Start After Changes

```bash
# Check the configuration syntax
sudo kea-dhcp4 -t /etc/kea/kea-dhcp4.conf

# Check system logs
sudo journalctl -u kea-dhcp4-server -n 50

# Check KEA log file
sudo tail -f /var/log/kea/kea-dhcp4.log
```

### Still No Leases?

1. Verify KEA is actually serving DHCP:
   ```bash
   sudo journalctl -u kea-dhcp4-server | grep DHCPACK
   ```

2. Check if leases are being stored:
   ```bash
   # For memfile backend
   cat /var/lib/kea/kea-leases4.csv
   
   # For MySQL
   mysql -u kea -p kea -e "SELECT * FROM lease4;"
   ```

3. Ensure your config.yaml points to the correct KEA server:
   ```yaml
   kea:
     control_agent_url: "http://YOUR-KEA-SERVER:8000"
   ```

## Additional Hook Libraries You Might Want

While you're editing the configuration, consider adding these useful hooks:

```json
{
  "Dhcp4": {
    "hooks-libraries": [
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"
      },
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_host_cmds.so",
        "comment": "Enables reservation management via API"
      },
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_stat_cmds.so",
        "comment": "Enables statistics commands"
      }
    ]
  }
}
```

The `libdhcp_host_cmds.so` hook enables the `reservation-add` and `reservation-del` commands that this GUI uses!

## Need More Help?

- KEA Documentation: https://kea.readthedocs.io/
- KEA Hook Libraries: https://kea.readthedocs.io/en/latest/arm/hooks.html
- This project's issues: https://github.com/awkto/Kea-GUI-Reservations/issues
