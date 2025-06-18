#!/bin/bash

# PHRM Test Runner
# Simple script to run tests with proper environment setup

echo "Setting up Python environment for testing..."

# Set PYTHONPATH to current directory so 'app' module can be imported
export PYTHONPATH=.

# Suppress SWIG deprecation warnings
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Run tests with uv
if [ $# -eq 0 ]; then
    echo "Running all tests..."
    uv run python -W ignore::DeprecationWarning -m pytest "$@"
else
    echo "Running specific tests: $@"
    uv run python -W ignore::DeprecationWarning -m pytest "$@"
fi
