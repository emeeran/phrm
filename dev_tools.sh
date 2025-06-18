#!/bin/bash

# PHRM Linting and Code Quality Tools
# Script to run development tools with proper environment setup

echo "PHRM Code Quality Tools"
echo "======================="

# Set PYTHONPATH to current directory
export PYTHONPATH=.

case "$1" in
    "lint"|"check")
        echo "Running ruff linter..."
        uv run ruff check app/ "${@:2}"
        ;;
    "lint-fix"|"fix")
        echo "Running ruff linter with auto-fix..."
        uv run ruff check --fix app/ "${@:2}"
        ;;
    "format")
        echo "Running black formatter..."
        uv run black app/ "${@:2}"
        ;;
    "type-check"|"types")
        echo "Running mypy type checker..."
        uv run python -W ignore::DeprecationWarning -m mypy app/ "${@:2}"
        ;;
    "test")
        echo "Running tests..."
        ./run_tests.sh "${@:2}"
        ;;
    "all")
        echo "Running all code quality checks..."
        echo ""
        echo "1. Linting with ruff..."
        uv run ruff check app/
        echo ""
        echo "2. Type checking with mypy..."
        uv run python -W ignore::DeprecationWarning -m mypy app/ --ignore-missing-imports
        echo ""
        echo "3. Running tests..."
        ./run_tests.sh --tb=short
        ;;
    *)
        echo "Usage: $0 {lint|lint-fix|format|type-check|test|all}"
        echo ""
        echo "Commands:"
        echo "  lint       - Run ruff linter"
        echo "  lint-fix   - Run ruff linter with auto-fix"
        echo "  format     - Run black code formatter"
        echo "  type-check - Run mypy type checker"
        echo "  test       - Run tests"
        echo "  all        - Run all checks"
        exit 1
        ;;
esac
