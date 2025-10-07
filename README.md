# KEA DHCP Lease to Reservation Promotion GUI

A web-based GUI for promoting KEA DHCP leases to permanent reservations.

## Features

- Connect to KEA DHCP server via Control Agent API
- View active DHCPv4 leases
- Promote leases to permanent reservations with a single click
- Simple, intuitive web interface

## Architecture

- **Backend**: Python Flask application
- **Frontend**: HTML/JavaScript with Bootstrap
- **KEA Integration**: KEA Control Agent REST API
- **Deployment**: Docker container

## Prerequisites

- KEA DHCP server with Control Agent enabled
- **KEA Lease Commands Hook Library** (required for viewing leases)
- Docker (for containerized deployment)

## KEA Configuration Requirements

### 1. Enable Control Agent

Your KEA server must have the Control Agent running. Add this to your KEA configuration (`/etc/kea/kea-ctrl-agent.conf`):

```json
{
  "Control-agent": {
    "http-host": "0.0.0.0",
    "http-port": 8000,
    "control-sockets": {
      "dhcp4": {
        "socket-type": "unix",
        "socket-name": "/tmp/kea4-ctrl-socket"
      }
    }
  }
}
```

### 2. Enable Lease Commands Hook Library (REQUIRED)

**This is essential for the GUI to fetch and display leases!**

Edit your DHCPv4 configuration (`/etc/kea/kea-dhcp4.conf`) and add the hooks library:

```json
{
  "Dhcp4": {
    "hooks-libraries": [
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"
      }
    ],
    // ... rest of your configuration
  }
}
```

**Common hook library paths:**
- **Debian/Ubuntu**: `/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so`
- **CentOS/RHEL**: `/usr/lib64/kea/hooks/libdhcp_lease_cmds.so`
- **FreeBSD**: `/usr/local/lib/kea/hooks/libdhcp_lease_cmds.so`
- **Alpine Linux**: `/usr/lib/kea/hooks/libdhcp_lease_cmds.so`

After modifying the configuration, restart KEA:

```bash
sudo systemctl restart kea-dhcp4-server
sudo systemctl restart kea-ctrl-agent
```

**To verify it's working:**

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"command": "list-commands", "service": ["dhcp4"]}' \
  http://localhost:8000

# You should see "lease4-get-all" and "lease4-get-page" in the output
```

## Configuration

Edit `config.yaml` with your KEA server details:

```yaml
kea:
  control_agent_url: "http://your-kea-server:8000"
  # Optional authentication
  username: ""
  password: ""
```

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`

## Running with Docker

```bash
docker build -t kea-gui .
docker run -p 5000:5000 -v $(pwd)/config.yaml:/app/config.yaml kea-gui
```

## API Endpoints

- `GET /api/leases` - Fetch all DHCPv4 leases
- `POST /api/promote` - Promote a lease to reservation
- `GET /api/reservations` - List current reservations
- `GET /api/health` - Health check

## Usage

1. Access the web interface
2. View the list of active DHCP leases
3. Click "Promote" next to any lease
4. Confirm the action
5. The lease is converted to a permanent reservation in KEA

## Security Considerations

- Use HTTPS in production
- Secure your KEA Control Agent with authentication
- Run container with appropriate user permissions
- Consider network isolation

## License

MIT
