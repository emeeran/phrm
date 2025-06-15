#!/bin/bash
# Start Redis for PHRM development

REDIS_CONF="redis-dev.conf"
REDIS_PID="/tmp/redis-phrm.pid"

# Check if Redis is already running
if [ -f "$REDIS_PID" ] && kill -0 $(cat "$REDIS_PID") 2>/dev/null; then
    echo "Redis is already running (PID: $(cat $REDIS_PID))"
    exit 0
fi

# Start Redis with our configuration
echo "Starting Redis for PHRM development..."
redis-server "$REDIS_CONF" --daemonize yes --pidfile "$REDIS_PID"

# Verify it started
sleep 1
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis started successfully"
    echo "   PID: $(cat $REDIS_PID)"
    echo "   Use 'redis-cli' to connect"
    echo "   Use './scripts/stop-redis.sh' to stop"
else
    echo "❌ Failed to start Redis"
    exit 1
fi
