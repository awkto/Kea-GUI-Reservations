# DHCP Configuration Management Features

## Overview

This branch adds comprehensive DHCP configuration management capabilities to the KEA GUI, allowing users to configure and manage KEA DHCP server settings directly from the web interface.

## New Features

### 1. **Subnet Management**
- **View All Subnets**: See all configured DHCP subnets with their details
- **Create Subnets**: Add new DHCP subnets with custom configurations
- **Edit Subnets**: Modify existing subnet configurations
- **Delete Subnets**: Remove subnets (with confirmation)

### 2. **IP Pool Configuration**
- Define multiple IP address pools per subnet
- Specify start and end IP addresses for each pool
- Add/remove pools dynamically in the UI

### 3. **Subnet-Specific Options**
Configure common DHCP options for each subnet:
- **Router/Gateway** (Option 3)
- **DNS Servers** (Option 6) - comma-separated list
- **Domain Name** (Option 15)
- **NTP Servers** (Option 42) - comma-separated list

### 4. **Lease Time Configuration**
- Set custom lease times per subnet (in seconds)
- Override global default lease times
- Visual display of configured lease times

### 5. **Global DHCP Parameters**
Configure server-wide defaults:
- **Valid Lifetime**: Default lease time for all subnets
- **Renew Timer (T1)**: Client renewal timer
- **Rebind Timer (T2)**: Client rebinding timer

### 6. **User Interface Enhancements**
- New "DHCP Config" button in the navigation bar
- Tabbed interface for organizing configuration sections
- Responsive modal dialogs for editing
- Real-time validation and feedback
- Visual indicators for configured options

## How to Use

### Accessing DHCP Configuration
1. Click the **"DHCP Config"** button in the top navigation bar
2. The DHCP Configuration Manager modal will open

### Managing Subnets

#### View Subnets
- The **Subnets** tab shows all configured subnets in a table
- Each row displays:
  - Subnet ID
  - Network CIDR (e.g., 192.168.1.0/24)
  - Configured IP pools
  - Lease time (or "Global" if using default)
  - Number of DHCP options configured

#### Add a New Subnet
1. Click **"Add Subnet"** button
2. Fill in the required fields:
   - **Subnet ID**: Unique numeric identifier
   - **Network (CIDR)**: Network address with prefix (e.g., 192.168.1.0/24)
3. Configure at least one IP pool:
   - **Pool Start IP**: First IP in the range
   - **Pool End IP**: Last IP in the range
4. (Optional) Set a custom lease time in seconds
5. (Optional) Configure DHCP options:
   - Router/gateway IP address
   - DNS servers (comma-separated)
   - Domain name
   - NTP servers (comma-separated)
6. Click **"Save Subnet"**

#### Edit an Existing Subnet
1. Click the **pencil icon** next to the subnet you want to edit
2. Modify any fields (note: Subnet ID cannot be changed)
3. Add or remove IP pools as needed
4. Update DHCP options
5. Click **"Save Subnet"**

#### Delete a Subnet
1. Click the **trash icon** next to the subnet
2. Confirm the deletion
3. **Warning**: This will remove all reservations in that subnet

### Configuring Global Options

1. Switch to the **"Global Options"** tab
2. Configure server-wide defaults:
   - **Valid Lifetime**: Default lease time (e.g., 7200 = 2 hours)
   - **Renew Timer**: Leave empty for auto-calculation (50% of valid-lifetime)
   - **Rebind Timer**: Leave empty for auto-calculation (87.5% of valid-lifetime)
3. Click **"Save Global Options"**

## API Endpoints

### Subnet Management
- `GET /api/dhcp/subnets` - List all subnets
- `GET /api/dhcp/subnets/<id>` - Get subnet details
- `POST /api/dhcp/subnets` - Create new subnet
- `PUT /api/dhcp/subnets/<id>` - Update subnet
- `DELETE /api/dhcp/subnets/<id>` - Delete subnet

### Global Configuration
- `GET /api/dhcp/global` - Get global parameters
- `PUT /api/dhcp/global` - Update global parameters
- `GET /api/dhcp/config` - Get complete DHCP configuration

## Technical Details

### Backend Changes

#### `kea_client.py`
New methods added:
- `get_full_config()` - Retrieve complete DHCPv4 configuration
- `get_subnet_details(subnet_id)` - Get specific subnet configuration
- `create_subnet(subnet_config)` - Create new subnet
- `update_subnet(subnet_id, subnet_config)` - Update existing subnet
- `delete_subnet(subnet_id)` - Delete subnet
- `update_global_options(options)` - Update global DHCP parameters
- `get_global_parameters()` - Get global configuration
- `_set_config(dhcp4_config)` - Apply configuration changes

#### `app.py`
New API routes:
- `/api/dhcp/config` - Full configuration endpoint
- `/api/dhcp/global` - Global parameters (GET/PUT)
- `/api/dhcp/subnets` - Subnet collection (GET/POST)
- `/api/dhcp/subnets/<id>` - Individual subnet (GET/PUT/DELETE)

### Frontend Changes

#### `templates/index.html`
- Added DHCP Configuration modal with tabbed interface
- Added Subnet modal for add/edit operations
- Implemented pool management (add/remove pools)
- Added JavaScript functions for all DHCP config operations
- Enhanced UI with Bootstrap components and icons

## Example Configuration

### Creating a Basic Subnet
```json
{
  "id": 1,
  "subnet": "192.168.1.0/24",
  "pools": [
    {
      "pool": "192.168.1.100 - 192.168.1.200"
    }
  ],
  "valid-lifetime": 7200,
  "option-data": [
    {
      "name": "routers",
      "code": 3,
      "data": "192.168.1.1"
    },
    {
      "name": "domain-name-servers",
      "code": 6,
      "data": "8.8.8.8, 8.8.4.4"
    },
    {
      "name": "domain-name",
      "code": 15,
      "data": "example.local"
    }
  ]
}
```

## Common Use Cases

### 1. Setting Up a New DHCP Subnet
Perfect for deploying a new network or VLAN with DHCP service.

### 2. Adjusting IP Pools
Expand or shrink available IP ranges as network grows or changes.

### 3. Updating DNS Servers
Quickly update DNS servers for all clients in a subnet.

### 4. Configuring Multiple Subnets
Manage different networks with different DHCP settings from one interface.

### 5. Lease Time Optimization
Fine-tune lease times for different network segments (e.g., guest network vs. corporate network).

## Limitations

- Only supports DHCPv4 (not DHCPv6)
- Covers common DHCP options, not every possible option
- Changes are applied immediately to running configuration
- No built-in configuration backup/restore (use git or manual backups)

## Best Practices

1. **Always test changes** in a development environment first
2. **Document your subnets** with meaningful IDs and consistent naming
3. **Use appropriate lease times**: 
   - Shorter for guest/mobile networks (e.g., 1 hour)
   - Longer for stable/corporate networks (e.g., 8-24 hours)
4. **Configure DNS properly** to avoid connectivity issues
5. **Plan IP pools carefully** leaving room for static assignments and reservations

## Troubleshooting

### Configuration Not Saved
- Check KEA Control Agent is running and accessible
- Verify authentication credentials are correct
- Check server logs for errors

### Subnet Not Appearing
- Ensure subnet ID is unique
- Verify network CIDR is valid
- Check for overlapping IP ranges

### DHCP Options Not Working
- Verify option codes are correct
- Check option data format (IPs should be comma-separated)
- Ensure KEA server has reloaded the configuration

## Future Enhancements

Potential additions for future versions:
- DHCPv6 support
- Advanced option configuration (all DHCP options)
- Client class configuration
- Shared networks support
- Configuration import/export
- Configuration validation and testing
- Configuration history/versioning
- Bulk subnet operations

## Testing

To test the new features locally:

1. Start the application:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. Click "DHCP Config" in the navigation bar

4. Try creating, editing, and viewing subnets

5. Verify changes are reflected in KEA DHCP server

## Contributing

When contributing to these features:
- Follow existing code style
- Add appropriate error handling
- Update this documentation
- Test with actual KEA DHCP server
- Consider edge cases and validation

## License

Same as the main project.
