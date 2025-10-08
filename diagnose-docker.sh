#!/bin/bash
# KEA GUI Container Diagnostics Script
# Run this to diagnose configuration issues

CONTAINER_NAME="${1:-kea-gui}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         KEA GUI Container Diagnostics                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Container: $CONTAINER_NAME"
echo ""

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' not found!"
    echo ""
    echo "Available containers:"
    docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Container Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps -a --filter "name=^${CONTAINER_NAME}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Config File on Host"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "config.yaml" ]; then
    echo "✅ config.yaml exists in current directory"
    ls -lh config.yaml
    echo ""
    echo "KEA URL configured:"
    grep "control_agent_url" config.yaml || echo "⚠️  control_agent_url not found"
else
    echo "❌ config.yaml NOT FOUND in current directory!"
    echo "   Create one or cd to the directory containing config.yaml"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Container Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec "$CONTAINER_NAME" env | grep -E "CONFIG|PYTHON" 2>&1 || echo "❌ Cannot access container environment"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Config Directory in Container"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec "$CONTAINER_NAME" ls -la /app/config/ 2>&1 || echo "❌ /app/config/ directory not found or not accessible"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Config File Content in Container"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker exec "$CONTAINER_NAME" test -f /app/config/config.yaml 2>/dev/null; then
    echo "✅ Config file exists in container"
    echo ""
    docker exec "$CONTAINER_NAME" cat /app/config/config.yaml 2>&1 | head -20
else
    echo "❌ Config file NOT FOUND at /app/config/config.yaml"
    echo "   This means the volume mount is missing or incorrect!"
    echo ""
    echo "   Fix: Stop container and run with:"
    echo "   docker run -d --name $CONTAINER_NAME -p 5000:5000 \\"
    echo "     -v \$(pwd)/config.yaml:/app/config/config.yaml:ro \\"
    echo "     awkto/kea-gui-reservations:latest"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. API Config Endpoint Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
RESPONSE=$(curl -s http://localhost:5000/api/config 2>&1)
if echo "$RESPONSE" | grep -q "control_agent_url"; then
    KEA_URL=$(echo "$RESPONSE" | grep -o '"control_agent_url":"[^"]*"' | cut -d'"' -f4)
    echo "✅ API is responding"
    echo "   Configured KEA URL: $KEA_URL"
    
    if [[ "$KEA_URL" == *"localhost"* ]] || [[ "$KEA_URL" == *"127.0.0.1"* ]]; then
        echo "   ⚠️  WARNING: Using localhost - config file may not be mounted!"
    fi
else
    echo "❌ Cannot reach API or invalid response"
    echo "Response: $RESPONSE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s http://localhost:5000/api/health 2>&1 | python3 -m json.tool 2>/dev/null || echo "❌ Health check failed or invalid JSON"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. Recent Container Logs (last 30 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs --tail 30 "$CONTAINER_NAME" 2>&1
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. Volume Mounts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker inspect "$CONTAINER_NAME" --format='{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Mode}}){{"\n"}}{{end}}' 2>&1
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        Summary                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Determine issues
HAS_ISSUES=false

# Check if config file is mounted
if ! docker exec "$CONTAINER_NAME" test -f /app/config/config.yaml 2>/dev/null; then
    echo "❌ ISSUE: Config file not mounted in container"
    HAS_ISSUES=true
fi

# Check if using localhost
KEA_URL=$(curl -s http://localhost:5000/api/config 2>/dev/null | grep -o '"control_agent_url":"[^"]*"' | cut -d'"' -f4)
if [[ "$KEA_URL" == *"localhost"* ]] || [[ "$KEA_URL" == *"127.0.0.1"* ]]; then
    echo "⚠️  WARNING: Application is configured to use localhost"
    echo "   This usually means the config file is not properly mounted"
    HAS_ISSUES=true
fi

if [ "$HAS_ISSUES" = false ]; then
    echo "✅ No obvious issues detected!"
    echo ""
    echo "If you're still having problems, check:"
    echo "  - KEA server is reachable from this container"
    echo "  - KEA Control Agent is running on the configured port"
    echo "  - Required hook libraries (lease_cmds, host_cmds) are loaded"
else
    echo ""
    echo "📋 Recommended Actions:"
    echo ""
    echo "1. Stop the container:"
    echo "   docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
    echo ""
    echo "2. Ensure config.yaml exists in current directory"
    echo ""
    echo "3. Run with proper volume mount:"
    echo "   docker run -d --name $CONTAINER_NAME \\"
    echo "     -p 5000:5000 \\"
    echo "     -v \$(pwd)/config.yaml:/app/config/config.yaml:ro \\"
    echo "     awkto/kea-gui-reservations:latest"
    echo ""
    echo "   OR use docker-compose:"
    echo "   docker-compose up -d"
fi

echo ""
echo "For more help, see: DOCKER_CONFIG_TROUBLESHOOTING.md"
