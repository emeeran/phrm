#!/usr/bin/env python3
"""
PHRM Setup Tool - Convenient wrapper for system setup

This script provides easy access to the comprehensive setup system
from the root directory.
"""

import os
import sys

# Add the scripts directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))

try:
    from database.setup_system import main
    main()
except ImportError as e:
    print(f"Error: Could not import setup module: {e}")
    print("Make sure you have the setup module installed in scripts/database/")
    sys.exit(1)
except Exception as e:
    print(f"Error running setup: {e}")
    sys.exit(1)
