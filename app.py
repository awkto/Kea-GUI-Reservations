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
    return render_template('index.html')


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


if __name__ == '__main__':
    runtime_config = load_config()
    app.run(
        host=runtime_config['app']['host'],
        port=runtime_config['app']['port'],
        debug=runtime_config['app']['debug']
    )
