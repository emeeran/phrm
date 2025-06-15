#!/bin/bash
# Simple script to run vectorization separately from the app

echo "=== PHRM Reference Books Vectorization ==="
echo "This script runs vectorization completely separate from the app startup."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo "Reference books: $PROJECT_ROOT/reference_books"
echo

# Check if reference_books directory exists
if [ ! -d "$PROJECT_ROOT/reference_books" ]; then
    echo "Error: reference_books directory not found at $PROJECT_ROOT/reference_books"
    echo "Please ensure the reference_books directory exists and contains PDF files."
    exit 1
fi

# Count PDF files
PDF_COUNT=$(find "$PROJECT_ROOT/reference_books" -name "*.pdf" | wc -l)
echo "Found $PDF_COUNT PDF files to process"

if [ $PDF_COUNT -eq 0 ]; then
    echo "Warning: No PDF files found in reference_books directory"
    echo "Please add PDF files to $PROJECT_ROOT/reference_books"
    exit 1
fi

echo
echo "Choose an option:"
echo "1) Check status"
echo "2) Run vectorization (new/changed files only)"
echo "3) Force refresh all files"
echo "4) Clean vector database"
echo "5) Test search"
echo

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Checking status..."
        python3 "$SCRIPT_DIR/rag_manager.py" status
        ;;
    2)
        echo "Running vectorization..."
        python3 "$SCRIPT_DIR/rag_manager.py" vectorize
        ;;
    3)
        echo "Force refreshing all files..."
        python3 "$SCRIPT_DIR/rag_manager.py" refresh
        ;;
    4)
        echo "Cleaning vector database..."
        python3 "$SCRIPT_DIR/rag_manager.py" clean
        ;;
    5)
        echo "Testing search functionality..."
        python3 "$SCRIPT_DIR/rag_manager.py" test
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo
echo "Done!"
