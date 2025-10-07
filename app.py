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

# Load configuration
config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format=config['logging']['format']
)
logger = logging.getLogger(__name__)

# Initialize KEA client
kea_client = KeaClient(
    url=config['kea']['control_agent_url'],
    username=config['kea'].get('username'),
    password=config['kea'].get('password')
)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test connection to KEA
        kea_client.get_version()
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
    try:
        subnet_id = request.args.get('subnet_id', type=int)
        leases = kea_client.get_leases(subnet_id=subnet_id)
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
        subnet_id = request.args.get('subnet_id', type=int)
        reservations = kea_client.get_reservations(subnet_id=subnet_id)
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
        
        logger.info(f"Promoting lease: IP={ip_address}, MAC={hw_address}")
        
        result = kea_client.create_reservation(
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
    try:
        subnets = kea_client.get_subnets()
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


@app.route('/api/reservation/<ip_address>', methods=['DELETE'])
def delete_reservation(ip_address):
    """Delete a reservation"""
    try:
        subnet_id = request.args.get('subnet_id', type=int)
        kea_client.delete_reservation(ip_address, subnet_id)
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
    app.run(
        host=config['app']['host'],
        port=config['app']['port'],
        debug=config['app']['debug']
    )
