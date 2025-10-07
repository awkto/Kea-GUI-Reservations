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
- Docker (for containerized deployment)

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
