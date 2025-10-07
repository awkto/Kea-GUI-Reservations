#!/bin/bash
# Quick test script to verify KEA lease commands are working

echo "==================================="
echo "KEA Lease Commands Test"
echo "==================================="
echo ""

# Configuration
KEA_URL="http://localhost:8001"  # Change this to match your config.yaml
USERNAME=""
PASSWORD=""

# Build auth param if needed
AUTH_PARAM=""
if [ -n "$USERNAME" ]; then
    AUTH_PARAM="-u $USERNAME:$PASSWORD"
fi

echo "Testing KEA at: $KEA_URL"
echo ""

# Test 1: Check if KEA is reachable
echo "1. Testing KEA connectivity..."
if curl -s -f $AUTH_PARAM -X POST -H "Content-Type: application/json" \
    -d '{"command": "version-get", "service": ["dhcp4"]}' \
    $KEA_URL > /dev/null; then
    echo "   ✓ KEA is reachable"
else
    echo "   ✗ Cannot reach KEA at $KEA_URL"
    exit 1
fi

echo ""

# Test 2: List available commands
echo "2. Checking available commands..."
COMMANDS=$(curl -s $AUTH_PARAM -X POST -H "Content-Type: application/json" \
    -d '{"command": "list-commands", "service": ["dhcp4"]}' \
    $KEA_URL | grep -o '"lease4-get[^"]*"' | tr '\n' ' ')

if echo "$COMMANDS" | grep -q "lease4-get-all"; then
    echo "   ✓ lease4-get-all is available"
    LEASE_CMD_AVAILABLE=true
else
    echo "   ✗ lease4-get-all is NOT available"
    LEASE_CMD_AVAILABLE=false
fi

if echo "$COMMANDS" | grep -q "lease4-get-page"; then
    echo "   ✓ lease4-get-page is available"
else
    echo "   ✗ lease4-get-page is NOT available"
fi

echo ""

# Test 3: Try to fetch leases
if [ "$LEASE_CMD_AVAILABLE" = true ]; then
    echo "3. Fetching leases..."
    RESPONSE=$(curl -s $AUTH_PARAM -X POST -H "Content-Type: application/json" \
        -d '{"command": "lease4-get-all", "service": ["dhcp4"]}' \
        $KEA_URL)
    
    if echo "$RESPONSE" | grep -q '"result": 0'; then
        LEASE_COUNT=$(echo "$RESPONSE" | grep -o '"ip-address"' | wc -l)
        echo "   ✓ Successfully fetched $LEASE_COUNT lease(s)"
        
        # Show first lease as example
        if [ $LEASE_COUNT -gt 0 ]; then
            echo ""
            echo "   Example lease:"
            echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -30
        fi
    else
        echo "   ✗ Failed to fetch leases"
        echo "   Response: $RESPONSE"
    fi
else
    echo "3. Skipping lease fetch (command not available)"
    echo ""
    echo "==================================="
    echo "ACTION REQUIRED"
    echo "==================================="
    echo ""
    echo "The lease_cmds hook library is NOT loaded!"
    echo ""
    echo "To fix this:"
    echo "1. Edit /etc/kea/kea-dhcp4.conf"
    echo "2. Add the hooks-libraries section:"
    echo ""
    echo '   "hooks-libraries": ['
    echo '     {'
    echo '       "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"'
    echo '     }'
    echo '   ],'
    echo ""
    echo "3. Restart KEA:"
    echo "   sudo systemctl restart kea-dhcp4-server kea-ctrl-agent"
    echo ""
    echo "4. Run this script again to verify"
    echo ""
fi

echo ""
echo "==================================="
echo "Test complete!"
echo "==================================="
