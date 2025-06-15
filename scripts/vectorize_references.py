#!/usr/bin/env python3
"""
Standalone vectorization script for reference books.

This script runs completely independently from the Flask application
and handles vectorization of PDF files in the reference_books directory.

Usage:
    python scripts/vectorize_references.py [--force] [--path=/path/to/reference_books]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "vectorization.log"),
    ],
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import chromadb  # noqa: F401

        logger.info("✓ ChromaDB available")
    except ImportError:
        logger.error("✗ ChromaDB not available - install with: pip install chromadb")
        return False

    try:
        import fitz  # noqa: F401 # PyMuPDF

        logger.info("✓ PyMuPDF available")
    except ImportError:
        logger.error("✗ PyMuPDF not available - install with: pip install PyMuPDF")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Vectorize reference books for RAG")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-processing of all files, even if already processed",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to reference_books directory (default: ./reference_books)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting standalone vectorization process...")

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies - aborting")
        sys.exit(1)

    # Determine reference books path
    if args.path:
        reference_books_path = Path(args.path)
    else:
        reference_books_path = project_root / "reference_books"

    if not reference_books_path.exists():
        logger.error(f"Reference books directory not found: {reference_books_path}")
        sys.exit(1)

    logger.info(f"Using reference books path: {reference_books_path}")

    # Import and initialize RAG service
    try:
        # Set isolated mode for standalone processing
        os.environ["RAG_ISOLATED_MODE"] = "true"

        from app.utils.local_rag import LocalRAGService

        # Create service instance with specific path
        rag_service = LocalRAGService(str(reference_books_path))

        logger.info("RAG service initialized successfully")

        # Get initial status
        status = rag_service.get_status()
        logger.info(
            f"Current status: {status['processed_files_count']} files processed"
        )

        if status["processed_files_count"] > 0 and not args.force:
            logger.info("Files already processed. Use --force to re-process all files.")

            # List processed files
            for filename in status["processed_files"]:
                logger.info(f"  - {filename}")

            response = input("\nContinue with processing new/changed files? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                logger.info("Vectorization cancelled by user")
                sys.exit(0)

        # Perform vectorization
        if args.force:
            logger.info("Force flag enabled - refreshing all files...")
            success = rag_service.refresh_all()
        else:
            logger.info("Processing new/changed files...")
            success = rag_service.vectorize_reference_books(background=False)

        if success:
            # Get final status
            final_status = rag_service.get_status()
            logger.info("Vectorization completed successfully!")
            logger.info(
                f"Final status: {final_status['processed_files_count']} files processed"
            )
            logger.info(f"Total chunks: {final_status.get('total_chunks', 'unknown')}")

            # List all processed files
            logger.info("Processed files:")
            for filename in final_status["processed_files"]:
                logger.info(f"  ✓ {filename}")
        else:
            logger.error("Vectorization failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during vectorization: {e}")
        import traceback

        logger.debug(traceback.format_exc())
        sys.exit(1)

    logger.info("Vectorization process completed successfully!")


if __name__ == "__main__":
    main()
