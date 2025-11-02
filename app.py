"""
KEA DHCP Lease to Reservation Promotion GUI
Main Flask application
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
import yaml

from kea_client import KeaClient

# Initialize Flask app
app = Flask(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'kea': {
        'control_agent_url': 'http://localhost:8000',
        'username': '',
        'password': '',
        'default_subnet_id': 1
    },
    'app': {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': False
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}

# Load configuration
config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
config = DEFAULT_CONFIG.copy()
_config_cache = {'mtime': 0, 'config': None}

# Setup basic logging first (will be reconfigured after loading config)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_version():
    """
    Read version from version.txt file.
    Returns version string or 'unknown' if file not found.
    """
    version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"Could not read version file: {e}")
        return 'unknown'

def load_config():
    """
    Load configuration from file, with caching based on file modification time.
    This ensures all worker processes see config updates while avoiding excessive disk I/O.
    """
    global config, _config_cache
    
    # Check if file exists and get modification time
    if os.path.exists(config_path):
        current_mtime = os.path.getmtime(config_path)
        
        # Return cached config if file hasn't changed
        if _config_cache['mtime'] == current_mtime and _config_cache['config'] is not None:
            return _config_cache['config']
        
        # File changed or first load - reload from disk
        try:
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                
            if loaded_config:
                # Deep merge loaded config with defaults
                new_config = DEFAULT_CONFIG.copy()
                for key in loaded_config:
                    if isinstance(loaded_config[key], dict) and key in new_config:
                        new_config[key].update(loaded_config[key])
                    else:
                        new_config[key] = loaded_config[key]
                
                # Update cache
                _config_cache['mtime'] = current_mtime
                _config_cache['config'] = new_config
                config = new_config
                
                logger.debug(f"✅ Reloaded config from {config_path} (mtime: {current_mtime})")
                logger.debug(f"   KEA URL: {config['kea']['control_agent_url']}")
                return new_config
        except Exception as e:
            logger.error(f"❌ Error loading config from {config_path}: {e}")
    
    # Fall back to defaults if file doesn't exist or load failed
    if _config_cache['config'] is None:
        logger.warning(f"⚠️  Using default configuration")
        _config_cache['config'] = DEFAULT_CONFIG.copy()
        config = _config_cache['config']
    
    return config

# Initial load at startup
initial_config = load_config()

# Reconfigure logging with loaded config
logging.basicConfig(
    level=getattr(logging, initial_config['logging']['level']),
    format=initial_config['logging']['format'],
    force=True  # Force reconfiguration
)

logger_msg = f"✅ Initial configuration loaded"
logger_msg += f"\n   Config path: {config_path}"
logger_msg += f"\n   KEA URL: {initial_config['kea']['control_agent_url']}"
if not os.path.exists(config_path):
    logger_msg += f"\n   💡 Tip: Mount your config.yaml to /app/config/config.yaml in Docker"

logger.info(logger_msg)


def get_kea_client():
    """
    Get KEA client instance with current configuration.
    Reloads config from file to ensure all worker processes see updates.
    """
    current_config = load_config()
    return KeaClient(
        url=current_config['kea']['control_agent_url'],
        username=current_config['kea'].get('username'),
        password=current_config['kea'].get('password')
    )


def is_config_valid():
    """
    Check if the configuration is valid (not in first-start/unconfigured state).
    Returns True if config is properly set up, False if it's still using defaults.
    """
    current_config = load_config()
    kea_url = current_config['kea']['control_agent_url']
    
    # Check if using empty URL
    if not kea_url or kea_url.strip() == '':
        return False
    
    # Check if it's still pointing to localhost (default/unconfigured)
    # This is OK for development but indicates first-start state in production
    if 'localhost' in kea_url.lower() or '127.0.0.1' in kea_url:
        # But if running in Docker and localhost is intentional, that's fine
        # We'll be lenient and only reject if it's the exact default
        if kea_url == 'http://localhost:8000':
            return False
    
    return True


@app.route('/')
def index():
    """Render the main page"""
    version = get_version()
    return render_template('index.html', version=version)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if configuration is valid first
    if not is_config_valid():
        return jsonify({
            'status': 'unconfigured',
            'kea_connection': 'not_configured',
            'message': 'KEA server not configured. Please update configuration.'
        }), 200
    
    try:
        # Test connection to KEA
        client = get_kea_client()
        client.get_version()
        return jsonify({
            'status': 'healthy',
            'kea_connection': 'ok'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'kea_connection': 'failed',
            'error': str(e)
        }), 503


@app.route('/api/leases', methods=['GET'])
def get_leases():
    """Fetch all DHCPv4 leases"""
    # Check if configuration is valid first
    if not is_config_valid():
        return jsonify({
            'success': False,
            'unconfigured': True,
            'error': 'KEA server not configured. Please update configuration to connect.'
        }), 200
    
    try:
        client = get_kea_client()
        subnet_id = request.args.get('subnet_id', type=int)
        leases = client.get_leases(subnet_id=subnet_id)
        return jsonify({
            'success': True,
            'leases': leases,
            'count': len(leases)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching leases: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    """Fetch all DHCPv4 reservations"""
    try:
        client = get_kea_client()
        subnet_id = request.args.get('subnet_id', type=int)
        reservations = client.get_reservations(subnet_id=subnet_id)
        return jsonify({
            'success': True,
            'reservations': reservations,
            'count': len(reservations)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching reservations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """Create a new DHCP reservation"""
    try:
        client = get_kea_client()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        ip_address = data.get('ip_address')
        hw_address = data.get('hw_address')
        hostname = data.get('hostname', '')
        subnet_id = data.get('subnet_id')
        
        if not ip_address or not hw_address:
            return jsonify({
                'success': False,
                'error': 'ip_address and hw_address are required'
            }), 400
        
        logger.info(f"Creating reservation: IP={ip_address}, MAC={hw_address}")
        
        result = client.create_reservation(
            ip_address=ip_address,
            hw_address=hw_address,
            hostname=hostname,
            subnet_id=subnet_id
        )
        
        return jsonify({
            'success': True,
            'message': f'Successfully created reservation for {ip_address}',
            'reservation': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/promote', methods=['POST'])
def promote_lease():
    """Promote a lease to a permanent reservation"""
    try:
        client = get_kea_client()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        ip_address = data.get('ip_address')
        hw_address = data.get('hw_address')
        hostname = data.get('hostname', '')
        subnet_id = data.get('subnet_id')
        
        if not ip_address or not hw_address:
            return jsonify({
                'success': False,
                'error': 'ip_address and hw_address are required'
            }), 400
        
        # Check if a reservation already exists for this IP
        try:
            reservations = client.get_reservations(subnet_id=subnet_id)
            existing_reservation = next((r for r in reservations if r.get('ip-address') == ip_address), None)
            
            if existing_reservation:
                logger.warning(f"Cannot promote: reservation already exists for IP {ip_address}")
                return jsonify({
                    'success': False,
                    'error': f'A reservation already exists for IP {ip_address}. Please choose a different IP address.'
                }), 400
        except Exception as e:
            logger.warning(f"Could not verify existing reservations: {e}")
            # Continue anyway if reservation check fails
        
        logger.info(f"Promoting lease: IP={ip_address}, MAC={hw_address}")
        
        result = client.create_reservation(
            ip_address=ip_address,
            hw_address=hw_address,
            hostname=hostname,
            subnet_id=subnet_id
        )
        
        return jsonify({
            'success': True,
            'message': f'Successfully promoted {ip_address} to reservation',
            'reservation': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error promoting lease: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/subnets', methods=['GET'])
def get_subnets():
    """Fetch configured subnets"""
    # Check if configuration is valid first
    if not is_config_valid():
        return jsonify({
            'success': False,
            'unconfigured': True,
            'error': 'KEA server not configured',
            'subnets': []
        }), 200
    
    try:
        client = get_kea_client()
        subnets = client.get_subnets()
        return jsonify({
            'success': True,
            'subnets': subnets
        }), 200
    except Exception as e:
        logger.error(f"Error fetching subnets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate-ip', methods=['POST'])
def validate_ip():
    """
    Validate if an IP address belongs to a subnet
    
    Expected JSON body:
    {
        "ip_address": "192.168.1.100",
        "subnet_id": 1
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        ip_address = data.get('ip_address')
        subnet_id = data.get('subnet_id')
        
        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'ip_address is required'
            }), 400
        
        # Get subnet information
        client = get_kea_client()
        subnets = client.get_subnets()
        
        # Find the target subnet
        target_subnet = None
        if subnet_id is not None:
            target_subnet = next((s for s in subnets if s['id'] == subnet_id), None)
        
        if not target_subnet:
            return jsonify({
                'success': False,
                'valid': False,
                'error': f'Subnet {subnet_id} not found'
            }), 400
        
        # Parse subnet CIDR
        import ipaddress
        try:
            subnet_cidr = target_subnet['subnet']
            network = ipaddress.IPv4Network(subnet_cidr, strict=False)
            ip_obj = ipaddress.IPv4Address(ip_address)
            
            # Check if IP is in subnet range
            is_in_subnet = ip_obj in network
            
            # Check if IP is network or broadcast address
            is_network_addr = ip_obj == network.network_address
            is_broadcast_addr = ip_obj == network.broadcast_address
            
            if is_network_addr:
                return jsonify({
                    'success': True,
                    'valid': False,
                    'error': f'IP {ip_address} is the network address and cannot be used',
                    'subnet': subnet_cidr
                }), 200
            
            if is_broadcast_addr:
                return jsonify({
                    'success': True,
                    'valid': False,
                    'error': f'IP {ip_address} is the broadcast address and cannot be used',
                    'subnet': subnet_cidr
                }), 200
            
            if not is_in_subnet:
                return jsonify({
                    'success': True,
                    'valid': False,
                    'error': f'IP {ip_address} is not in subnet {subnet_cidr}',
                    'subnet': subnet_cidr
                }), 200
            
            # IP is valid
            return jsonify({
                'success': True,
                'valid': True,
                'subnet': subnet_cidr
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'valid': False,
                'error': f'Invalid IP address or subnet format: {str(e)}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error validating IP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration (sanitized)"""
    try:
        # Load current config from file
        current_config = load_config()
        
        # Return sanitized config (hide password)
        sanitized_config = {}
        for key in current_config:
            if isinstance(current_config[key], dict):
                sanitized_config[key] = current_config[key].copy()
            else:
                sanitized_config[key] = current_config[key]
        
        if 'kea' in sanitized_config and 'password' in sanitized_config['kea']:
            sanitized_config['kea']['password'] = '***' if sanitized_config['kea']['password'] else ''
        
        return jsonify({
            'success': True,
            'config': sanitized_config,
            'config_path': config_path,
            'config_exists': os.path.exists(config_path)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration to file"""
    global config, _config_cache
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        new_config = data.get('config')
        if not new_config:
            return jsonify({
                'success': False,
                'error': 'Configuration object is required'
            }), 400
        
        # Validate required structure
        if 'kea' not in new_config or 'app' not in new_config:
            return jsonify({
                'success': False,
                'error': 'Configuration must include "kea" and "app" sections'
            }), 400
        
        # If password is masked, keep the existing password
        current_config = load_config()
        if new_config['kea'].get('password') == '***' and current_config['kea'].get('password'):
            new_config['kea']['password'] = current_config['kea']['password']
        
        # Write to file
        with open(config_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"✅ Configuration saved to {config_path}")
        logger.info(f"   New KEA URL: {new_config['kea']['control_agent_url']}")
        
        # Invalidate cache so all workers reload on next request
        _config_cache['mtime'] = 0
        _config_cache['config'] = None
        
        # Force immediate reload
        load_config()
        
        return jsonify({
            'success': True,
            'message': f'Configuration saved successfully. All workers will use the new config immediately.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reservation/<ip_address>', methods=['DELETE'])
def delete_reservation(ip_address):
    """Delete a reservation"""
    try:
        client = get_kea_client()
        subnet_id = request.args.get('subnet_id', type=int)
        client.delete_reservation(ip_address, subnet_id)
        return jsonify({
            'success': True,
            'message': f'Successfully deleted reservation for {ip_address}'
        }), 200
    except Exception as e:
        logger.error(f"Error deleting reservation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reservations/export', methods=['GET'])
def export_reservations():
    """Export all DHCP reservations to JSON file"""
    try:
        client = get_kea_client()
        subnet_id = request.args.get('subnet_id', type=int)
        reservations = client.get_reservations(subnet_id=subnet_id)
        
        # Format reservations for export
        export_data = {
            'export_date': __import__('datetime').datetime.now().isoformat(),
            'total_count': len(reservations),
            'reservations': reservations
        }
        
        from flask import make_response
        import json
        
        response = make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = 'attachment; filename=dhcp_reservations_export.json'
        
        logger.info(f"Exported {len(reservations)} reservations")
        return response
        
    except Exception as e:
        logger.error(f"Error exporting reservations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reservations/import', methods=['POST'])
def import_reservations():
    """Import DHCP reservations from uploaded JSON file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read and parse JSON file
        import json
        try:
            file_content = file.read().decode('utf-8')
            import_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid JSON file: {str(e)}'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to read file: {str(e)}'
            }), 400
        
        # Extract reservations from import data
        if isinstance(import_data, dict) and 'reservations' in import_data:
            reservations_to_import = import_data['reservations']
        elif isinstance(import_data, list):
            reservations_to_import = import_data
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid file format. Expected JSON with "reservations" array or array of reservations.'
            }), 400
        
        if not isinstance(reservations_to_import, list):
            return jsonify({
                'success': False,
                'error': 'Reservations data must be an array'
            }), 400
        
        # Import reservations one by one
        client = get_kea_client()
        success_count = 0
        failed_count = 0
        failed_items = []
        
        for idx, reservation in enumerate(reservations_to_import):
            try:
                # Validate required fields
                ip_address = reservation.get('ip-address')
                hw_address = reservation.get('hw-address')
                
                if not ip_address or not hw_address:
                    failed_count += 1
                    failed_items.append({
                        'index': idx + 1,
                        'ip': ip_address or 'N/A',
                        'error': 'Missing required fields (ip-address or hw-address)'
                    })
                    continue
                
                hostname = reservation.get('hostname', '')
                subnet_id = reservation.get('subnet-id')
                
                # Attempt to create reservation
                client.create_reservation(
                    ip_address=ip_address,
                    hw_address=hw_address,
                    hostname=hostname,
                    subnet_id=subnet_id
                )
                
                success_count += 1
                logger.info(f"Imported reservation: IP={ip_address}, MAC={hw_address}")
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                failed_items.append({
                    'index': idx + 1,
                    'ip': reservation.get('ip-address', 'N/A'),
                    'mac': reservation.get('hw-address', 'N/A'),
                    'error': error_msg
                })
                logger.warning(f"Failed to import reservation {idx + 1}: {error_msg}")
                # Continue with next reservation
        
        # Prepare response
        response_data = {
            'success': True,
            'total': len(reservations_to_import),
            'success_count': success_count,
            'failed_count': failed_count,
            'message': f'{success_count} reservation(s) imported successfully. {failed_count} reservation(s) failed to import.'
        }
        
        if failed_count > 0:
            response_data['failed_items'] = failed_items
            response_data['hint'] = 'Check if you have duplicates or reservations outside the subnet range.'
        
        logger.info(f"Import completed: {success_count} succeeded, {failed_count} failed")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error importing reservations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/config', methods=['GET'])
def get_dhcp_config():
    """Get complete DHCP configuration"""
    try:
        client = get_kea_client()
        config = client.get_full_config()
        return jsonify({
            'success': True,
            'config': config
        }), 200
    except Exception as e:
        logger.error(f"Error fetching DHCP config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/global', methods=['GET'])
def get_global_parameters():
    """Get global DHCP parameters"""
    try:
        client = get_kea_client()
        params = client.get_global_parameters()
        return jsonify({
            'success': True,
            'parameters': params
        }), 200
    except Exception as e:
        logger.error(f"Error fetching global parameters: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/global', methods=['PUT'])
def update_global_parameters():
    """Update global DHCP parameters"""
    try:
        client = get_kea_client()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        options = data.get('options', {})
        client.update_global_options(options)
        
        return jsonify({
            'success': True,
            'message': 'Global parameters updated successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error updating global parameters: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/subnets', methods=['GET'])
def get_dhcp_subnets():
    """Get all DHCP subnets with detailed configuration"""
    try:
        client = get_kea_client()
        config = client.get_full_config()
        subnets = config.get('subnet4', [])
        
        return jsonify({
            'success': True,
            'subnets': subnets,
            'count': len(subnets)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching DHCP subnets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/subnets/<int:subnet_id>', methods=['GET'])
def get_subnet_details(subnet_id):
    """Get detailed configuration for a specific subnet"""
    try:
        client = get_kea_client()
        subnet = client.get_subnet_details(subnet_id)
        
        if subnet is None:
            return jsonify({
                'success': False,
                'error': f'Subnet {subnet_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'subnet': subnet
        }), 200
    except Exception as e:
        logger.error(f"Error fetching subnet details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/subnets', methods=['POST'])
def create_dhcp_subnet():
    """Create a new DHCP subnet"""
    try:
        client = get_kea_client()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        subnet_config = data.get('subnet')
        if not subnet_config:
            return jsonify({
                'success': False,
                'error': 'Subnet configuration is required'
            }), 400
        
        # Validate required fields
        if 'id' not in subnet_config or 'subnet' not in subnet_config:
            return jsonify({
                'success': False,
                'error': 'Subnet ID and network CIDR are required'
            }), 400
        
        result = client.create_subnet(subnet_config)
        
        return jsonify({
            'success': True,
            'message': f'Successfully created subnet {subnet_config["subnet"]}',
            'subnet': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating subnet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/subnets/<int:subnet_id>', methods=['PUT'])
def update_dhcp_subnet(subnet_id):
    """Update an existing DHCP subnet"""
    try:
        client = get_kea_client()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        subnet_config = data.get('subnet')
        if not subnet_config:
            return jsonify({
                'success': False,
                'error': 'Subnet configuration is required'
            }), 400
        
        result = client.update_subnet(subnet_id, subnet_config)
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated subnet {subnet_id}',
            'subnet': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating subnet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dhcp/subnets/<int:subnet_id>', methods=['DELETE'])
def delete_dhcp_subnet(subnet_id):
    """Delete a DHCP subnet"""
    try:
        client = get_kea_client()
        client.delete_subnet(subnet_id)
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted subnet {subnet_id}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting subnet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    runtime_config = load_config()
    app.run(
        host=runtime_config['app']['host'],
        port=runtime_config['app']['port'],
        debug=runtime_config['app']['debug']
    )
