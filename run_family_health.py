#!/usr/bin/env python3
"""
Start the Family Health Record Manager application.

This script initializes and runs the Flask application.
"""

import os
import sys
from pathlib import Path

# Ensure the application directory is in the path
app_path = str(Path(__file__).resolve().parent)
if app_path not in sys.path:
    sys.path.insert(0, app_path)

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")

    app.run(host=host, port=port, debug=debug)
