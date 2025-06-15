#!/bin/bash
# Stop Redis for PHRM development

REDIS_PID="/tmp/redis-phrm.pid"

# Check if Redis is running
if [ -f "$REDIS_PID" ] && kill -0 $(cat "$REDIS_PID") 2>/dev/null; then
    echo "Stopping Redis (PID: $(cat $REDIS_PID))..."
    kill $(cat "$REDIS_PID")
    rm -f "$REDIS_PID"
    echo "✅ Redis stopped"
else
    echo "Redis is not running"
fi
