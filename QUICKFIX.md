# Quick Fix: No Leases Showing

## The Issue

Your KEA server (version 2.2.0) needs the `lease_cmds` hook library to view DHCP leases.

**Note**: The `host_cmds` library (for reservation management) is not installed on your system, but the GUI will use a fallback method to manage reservations via configuration updates.

## The Fix

You need to enable the KEA lease commands hook library. Here's how:

### 1. Find the Hook Library

On your KEA server, run:

```bash
ls -la /usr/lib/x86_64-linux-gnu/kea/hooks/
```

You should see `libdhcp_lease_cmds.so`.

### 2. Edit KEA Configuration

Edit `/etc/kea/kea-dhcp4.conf` and add this section:

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

**Important**: Only add `libdhcp_lease_cmds.so`. Do NOT add `libdhcp_host_cmds.so` as it's not installed on your system.

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

Restart your Python app and refresh your browser. You should now be able to:
- ✅ View all active leases
- ✅ Promote leases to reservations (using config-set fallback method)
- ✅ View existing reservations

## About Reservation Management

Since `libdhcp_host_cmds.so` is not available on your system (it may be a premium feature or not included in your KEA package), the GUI will automatically use an alternative method to create reservations by updating the configuration via the `config-set` command.

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
