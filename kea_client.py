"""
KEA DHCP Control Agent API Client
Handles communication with KEA DHCP server via Control Agent REST API
"""

import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class KeaClient:
    """Client for interacting with KEA DHCP Control Agent API"""
    
    def __init__(self, url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize KEA client
        
        Args:
            url: KEA Control Agent URL (e.g., http://localhost:8000)
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.url = url.rstrip('/')
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth
    
    def _send_command(self, command: str, service: List[str], arguments: Optional[Dict] = None) -> Dict:
        """
        Send a command to KEA Control Agent
        
        Args:
            command: KEA command name
            service: Target service(s) - e.g., ["dhcp4"]
            arguments: Optional command arguments
            
        Returns:
            Response from KEA
        """
        payload = {
            "command": command,
            "service": service
        }
        
        if arguments:
            payload["arguments"] = arguments
        
        logger.debug(f"Sending command to KEA: {command}")
        
        try:
            response = self.session.post(
                self.url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Check if command was successful
            if isinstance(result, list) and len(result) > 0:
                if result[0].get('result') != 0:
                    error_msg = result[0].get('text', 'Unknown error')
                    raise Exception(f"KEA command failed: {error_msg}")
                return result[0]
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to communicate with KEA: {e}")
            raise Exception(f"Failed to communicate with KEA server: {e}")
    
    def get_version(self) -> str:
        """Get KEA version"""
        result = self._send_command("version-get", ["dhcp4"])
        return result.get('arguments', {}).get('extended', 'unknown')
    
    def get_leases(self, subnet_id: Optional[int] = None) -> List[Dict]:
        """
        Get all DHCPv4 leases
        
        Args:
            subnet_id: Optional subnet ID to filter leases
            
        Returns:
            List of lease dictionaries
        """
        # Get leases using lease4-get-all command
        result = self._send_command("lease4-get-all", ["dhcp4"], arguments={})
        
        leases = result.get('arguments', {}).get('leases', [])
        
        # Filter by subnet if specified
        if subnet_id is not None:
            leases = [l for l in leases if l.get('subnet-id') == subnet_id]
        
        # Enrich lease data
        for lease in leases:
            lease['hw-address'] = lease.get('hw-address', 'unknown')
            lease['hostname'] = lease.get('hostname', '')
            lease['state'] = lease.get('state', 0)
            
        return leases
    
    def get_reservations(self, subnet_id: Optional[int] = None) -> List[Dict]:
        """
        Get all DHCPv4 reservations
        
        Args:
            subnet_id: Optional subnet ID to filter reservations
            
        Returns:
            List of reservation dictionaries
        """
        try:
            # Get config to extract reservations
            result = self._send_command("config-get", ["dhcp4"])
            config = result.get('arguments', {})
            
            reservations = []
            
            # Extract reservations from subnet configurations
            dhcp4_config = config.get('Dhcp4', {})
            subnets = dhcp4_config.get('subnet4', [])
            
            for subnet in subnets:
                current_subnet_id = subnet.get('id')
                
                # Filter by subnet if specified
                if subnet_id is not None and current_subnet_id != subnet_id:
                    continue
                
                subnet_prefix = subnet.get('subnet', '')
                
                for reservation in subnet.get('reservations', []):
                    res_data = {
                        'ip-address': reservation.get('ip-address'),
                        'hw-address': reservation.get('hw-address'),
                        'hostname': reservation.get('hostname', ''),
                        'subnet-id': current_subnet_id,
                        'subnet': subnet_prefix
                    }
                    reservations.append(res_data)
            
            return reservations
            
        except Exception as e:
            logger.warning(f"Could not fetch reservations: {e}")
            return []
    
    def create_reservation(self, ip_address: str, hw_address: str, 
                          hostname: str = "", subnet_id: Optional[int] = None) -> Dict:
        """
        Create a new DHCPv4 reservation
        
        Args:
            ip_address: IP address to reserve
            hw_address: Hardware (MAC) address
            hostname: Optional hostname
            subnet_id: Subnet ID where the reservation should be created
            
        Returns:
            Result of the reservation creation
        """
        reservation = {
            "ip-address": ip_address,
            "hw-address": hw_address
        }
        
        if hostname:
            reservation["hostname"] = hostname
        
        if subnet_id is not None:
            reservation["subnet-id"] = subnet_id
        
        arguments = {
            "reservation": reservation
        }
        
        result = self._send_command("reservation-add", ["dhcp4"], arguments)
        
        logger.info(f"Created reservation: IP={ip_address}, MAC={hw_address}")
        
        return reservation
    
    def delete_reservation(self, ip_address: str, subnet_id: Optional[int] = None):
        """
        Delete a DHCPv4 reservation
        
        Args:
            ip_address: IP address of the reservation to delete
            subnet_id: Optional subnet ID
        """
        arguments = {
            "ip-address": ip_address
        }
        
        if subnet_id is not None:
            arguments["subnet-id"] = subnet_id
        
        self._send_command("reservation-del", ["dhcp4"], arguments)
        logger.info(f"Deleted reservation: IP={ip_address}")
    
    def get_subnets(self) -> List[Dict]:
        """
        Get configured DHCPv4 subnets
        
        Returns:
            List of subnet dictionaries
        """
        result = self._send_command("config-get", ["dhcp4"])
        config = result.get('arguments', {})
        
        dhcp4_config = config.get('Dhcp4', {})
        subnets = dhcp4_config.get('subnet4', [])
        
        subnet_list = []
        for subnet in subnets:
            subnet_list.append({
                'id': subnet.get('id'),
                'subnet': subnet.get('subnet'),
                'pools': subnet.get('pools', [])
            })
        
        return subnet_list
