#!/bin/bash
cd /home/em/code/wip/phrm

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Ensure instance directory exists
mkdir -p instance

# Check database
if [ ! -f "instance/phrm.db" ]; then
    echo "Creating database..."
    python setup_database.py
fi

# Start the application
echo "Starting PHRM with environment variables loaded..."
python start_phrm.py
