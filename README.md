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
- **KEA Hook Libraries** (required):
  - `lease_cmds` - For viewing leases
  - `host_cmds` - For creating/managing reservations
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

### 2. Enable Required Hook Libraries (CRITICAL)

**Both of these libraries are essential for the GUI to work!**

Edit your DHCPv4 configuration (`/etc/kea/kea-dhcp4.conf`) and add both hook libraries:

```json
{
  "Dhcp4": {
    "hooks-libraries": [
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so",
        "parameters": {}
      },
      {
        "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_host_cmds.so",
        "parameters": {}
      }
    ],
    // ... rest of your configuration
  }
}
```

**Common hook library paths:**
- **Debian/Ubuntu**: `/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_*.so`
- **CentOS/RHEL**: `/usr/lib64/kea/hooks/libdhcp_*.so`
- **FreeBSD**: `/usr/local/lib/kea/hooks/libdhcp_*.so`
- **Alpine Linux**: `/usr/lib/kea/hooks/libdhcp_*.so`

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

# You should see these commands:
# - lease4-get-all (from lease_cmds)
# - reservation-add (from host_cmds)
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

### Using Pre-built Image (Recommended)

**Important:** You must mount a configuration file for the container to work properly!

```bash
# 1. Create a config.yaml file on your host
cat > config.yaml << 'EOF'
kea:
  control_agent_url: "https://your-kea-server:8000"
  username: "admin"
  password: "your-password"
  default_subnet_id: 1

app:
  host: "0.0.0.0"
  port: 5000
  debug: false
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EOF

# 2. Pull the latest image
docker pull awkto/kea-gui-reservations:latest

# 3. Run with your config mounted
docker run -d \
  --name kea-gui \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  awkto/kea-gui-reservations:latest

# 4. Check logs to verify config was loaded
docker logs kea-gui | head -20
# Should see: "✅ Loaded configuration from /app/config/config.yaml"
```

**⚠️ Common Mistake:** Forgetting to mount the config file will cause the container to use default settings (localhost), which will fail!

### Using Docker Compose (Easiest)

```bash
# 1. Clone the repository or create these files:
# - docker-compose.yml
# - config.yaml

# 2. Edit config.yaml with your KEA server details

# 3. Start the container
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

### Verifying Configuration

After starting the container, verify the config was loaded:

```bash
# Check config file exists in container
docker exec kea-gui cat /app/config/config.yaml

# Check via API
curl http://localhost:5000/api/config | jq '.config.kea.control_agent_url'

# Check health
curl http://localhost:5000/api/health
```

**Troubleshooting:** If you see errors connecting to localhost when you configured a different server, see [DOCKER_CONFIG_TROUBLESHOOTING.md](DOCKER_CONFIG_TROUBLESHOOTING.md)

### Building from Source

```bash
docker build -t kea-gui .
docker run -d -p 5000:5000 -v $(pwd)/config.yaml:/app/config/config.yaml:ro kea-gui
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

## CI/CD

This project includes GitHub Actions for automated Docker image builds. See [CICD_SETUP.md](CICD_SETUP.md) for setup instructions.

Docker images are automatically published to Docker Hub on tagged releases.

## License

MIT
