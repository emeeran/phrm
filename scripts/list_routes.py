#!/usr/bin/env python3
"""
List all routes in the PHRM application.
"""

import sys
from pathlib import Path

from app import create_app

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def list_routes():
    """List all routes in the application."""
    app = create_app()

    print("PHRM Application Routes:")
    print("=" * 50)

    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(
            {
                "endpoint": rule.endpoint,
                "methods": ", ".join(sorted(rule.methods - {"HEAD", "OPTIONS"})),
                "path": rule.rule,
            }
        )

    # Sort by endpoint
    routes.sort(key=lambda x: x["endpoint"])

    for route in routes:
        print(f"{route['methods']:<10} {route['path']:<40} -> {route['endpoint']}")


if __name__ == "__main__":
    list_routes()
