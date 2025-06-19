# PHRM Makefile for common tasks

.PHONY: setup run clean test help

help:
	@echo "Available commands:"
	@echo "  setup  - Initialize database and create sample data"
	@echo "  run    - Start the application server"
	@echo "  clean  - Clean up cache and temporary files"
	@echo "  test   - Run the test suite"
	@echo "  help   - Show this help message"

setup:
	@echo "Setting up PHRM database and sample data..."
	python setup.py

run:
	@echo "Starting PHRM application..."
	python start_phrm.py

clean:
	@echo "Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
	rm -f .cache_ggshield dump.rdb

test:
	@echo "Running test suite..."
	python scripts/run_tests.py

install:
	@echo "Installing dependencies..."
	uv sync

dev:
	@echo "Starting development server with auto-reload..."
	FLASK_DEBUG=true python start_phrm.py
