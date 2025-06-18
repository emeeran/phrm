#!/bin/bash

# PHRM Development Environment Runner
# Script to run Python commands with proper environment setup and warning suppression

# Set PYTHONPATH to current directory so 'app' module can be imported
export PYTHONPATH=.

# Suppress SWIG deprecation warnings
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Run the command with uv and warning suppression
echo "Running: $@"
uv run python -W ignore::DeprecationWarning "$@"
