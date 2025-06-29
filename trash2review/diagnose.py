#!/usr/bin/env python3
"""
PHRM Diagnostics Tool - System-wide diagnostics for PHRM

This is a convenient wrapper script that runs the comprehensive
system diagnostics. It's placed in the root directory for easy access.
"""

import os
import sys

# Add the scripts directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))

# Import and run diagnostics
try:
    from diagnostics.system_diagnostics import run_diagnostics
    run_diagnostics()
except ImportError:
    print("Error: Could not import diagnostics module.")
    print("Make sure you have the diagnostics module installed in scripts/diagnostics/")
    sys.exit(1)
except Exception as e:
    print(f"Error running diagnostics: {e}")
    sys.exit(1)
