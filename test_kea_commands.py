"""
Test script to check which KEA commands are available
"""

import yaml
import json
from kea_client import KeaClient, CommandNotSupportedException

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize KEA client
kea_client = KeaClient(
    url=config['kea']['control_agent_url'],
    username=config['kea'].get('username'),
    password=config['kea'].get('password')
)

print("Testing KEA Control Agent Commands")
print("=" * 60)

# Test 1: Get version
print("\n1. Testing version-get...")
try:
    version = kea_client.get_version()
    print(f"   ✓ KEA Version: {version}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 2: Get subnets
print("\n2. Testing config-get (to fetch subnets)...")
try:
    subnets = kea_client.get_subnets()
    print(f"   ✓ Found {len(subnets)} subnets:")
    for subnet in subnets:
        print(f"     - Subnet {subnet['id']}: {subnet['subnet']}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 3: List all available commands
print("\n3. Testing list-commands...")
try:
    result = kea_client._send_command("list-commands", ["dhcp4"])
    commands = result.get('arguments', [])
    print(f"   ✓ Available commands ({len(commands)}):")
    for cmd in sorted(commands):
        print(f"     - {cmd}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 4: Test lease4-get-all
print("\n4. Testing lease4-get-all...")
try:
    result = kea_client._send_command("lease4-get-all", ["dhcp4"], arguments={})
    leases = result.get('arguments', {}).get('leases', [])
    print(f"   ✓ Retrieved {len(leases)} leases")
    if leases:
        print(f"   Sample lease: {json.dumps(leases[0], indent=2)}")
except CommandNotSupportedException as e:
    print(f"   ✗ Not supported: {e}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 5: Test lease4-get-page
print("\n5. Testing lease4-get-page...")
try:
    subnets = kea_client.get_subnets()
    if subnets:
        test_subnet = subnets[0]['id']
        arguments = {
            "subnets": [test_subnet],
            "from": "0.0.0.0",
            "limit": 10
        }
        result = kea_client._send_command("lease4-get-page", ["dhcp4"], arguments)
        leases = result.get('arguments', {}).get('leases', [])
        print(f"   ✓ Retrieved {len(leases)} leases from subnet {test_subnet}")
        if leases:
            print(f"   Sample lease: {json.dumps(leases[0], indent=2)}")
    else:
        print("   - No subnets found to test")
except CommandNotSupportedException as e:
    print(f"   ✗ Not supported: {e}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 6: Test stat-lease4-get
print("\n6. Testing stat-lease4-get (lease statistics)...")
try:
    result = kea_client._send_command("stat-lease4-get", ["dhcp4"])
    stats = result.get('arguments', {})
    print(f"   ✓ Lease statistics: {json.dumps(stats, indent=2)}")
except CommandNotSupportedException as e:
    print(f"   ✗ Not supported: {e}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "=" * 60)
print("Test complete!")
