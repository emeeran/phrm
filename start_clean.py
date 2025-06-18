#!/usr/bin/env python3
"""
Script to free port 5000 and start the PHRM application
"""

import os
import signal
import subprocess
import sys

try:
    # Find processes using port 5000
    result = subprocess.run(
        ["lsof", "-i", ":5000", "-t"], capture_output=True, text=True, check=False
    )

    if result.stdout:
        pids = result.stdout.strip().split("\n")
        print(f"Found {len(pids)} process(es) using port 5000:")

        for pid in pids:
            try:
                # Get process name
                cmd_result = subprocess.run(
                    ["ps", "-p", pid, "-o", "comm="],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                process_name = cmd_result.stdout.strip()
                print(f"Stopping process {pid} ({process_name})...")

                # Kill the process
                os.kill(int(pid), signal.SIGTERM)
                print(f"✅ Successfully stopped process {pid}")
            except Exception as e:
                print(f"⚠️  Failed to stop process {pid}: {e}")

        print("\n✅ Port 5000 has been freed")
    else:
        print("No processes found using port 5000")

    # Start the PHRM application
    print("\n🚀 Starting PHRM application...")
    os.execv(sys.executable, [sys.executable, "run.py"])

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
