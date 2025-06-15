#!/usr/bin/env python3
"""
RAG Management Script

Provides various management commands for the Local RAG system.
Can be run completely independently from the Flask application.

Commands:
    status     - Show current vectorization status
    vectorize  - Run vectorization process
    refresh    - Force refresh all files
    clean      - Clean vector database
    test       - Test search functionality
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []

    try:
        import chromadb  # noqa: F401
    except ImportError:
        missing.append("chromadb")

    try:
        import fitz  # noqa: F401
    except ImportError:
        missing.append("PyMuPDF")

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False

    return True


def get_rag_service(reference_books_path=None):
    """Get RAG service instance"""
    # Set isolated mode for standalone processing
    os.environ["RAG_ISOLATED_MODE"] = "true"

    from app.utils.local_rag import LocalRAGService

    if not reference_books_path:
        reference_books_path = str(project_root / "reference_books")

    return LocalRAGService(reference_books_path)


def cmd_status(args):
    """Show current vectorization status"""
    if not check_dependencies():
        return False

    try:
        rag_service = get_rag_service(args.path)
        status = rag_service.get_status()

        print("=== RAG Service Status ===")
        print(f"ChromaDB Available: {status['chromadb_available']}")
        print(f"PyMuPDF Available: {status['pymupdf_available']}")
        print(f"Collection Initialized: {status['collection_initialized']}")
        print(f"Reference Books Path: {status['reference_books_path']}")
        print(f"Processed Files: {status['processed_files_count']}")
        print(f"Total Chunks: {status.get('total_chunks', 'unknown')}")
        print(f"Last Updated: {status.get('last_updated', 'never')}")
        print(f"Status: {status.get('status_message', 'unknown')}")

        if status["processed_files"]:
            print("\nProcessed Files:")
            for filename in status["processed_files"]:
                print(f"  ✓ {filename}")

        return True

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return False


def cmd_vectorize(args):
    """Run vectorization process"""
    if not check_dependencies():
        return False

    try:
        rag_service = get_rag_service(args.path)

        logger.info("Starting vectorization process...")
        success = rag_service.vectorize_reference_books(background=False)

        if success:
            logger.info("Vectorization completed successfully!")
            return True
        else:
            logger.error("Vectorization failed")
            return False

    except Exception as e:
        logger.error(f"Error during vectorization: {e}")
        return False


def cmd_refresh(args):
    """Force refresh all files"""
    if not check_dependencies():
        return False

    try:
        rag_service = get_rag_service(args.path)

        logger.info("Refreshing all files (force re-processing)...")
        success = rag_service.refresh_all()

        if success:
            logger.info("Refresh completed successfully!")
            return True
        else:
            logger.error("Refresh failed")
            return False

    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        return False


def cmd_clean(args):
    """Clean vector database"""
    if not check_dependencies():
        return False

    try:
        rag_service = get_rag_service(args.path)

        # Confirm action
        if not args.force:
            response = input("This will delete all vectorized data. Continue? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                logger.info("Clean operation cancelled")
                return True

        # Remove vector store and metadata
        import shutil

        vector_store_path = Path(rag_service.vector_store_path)
        metadata_file = Path(rag_service.metadata_file)

        if vector_store_path.exists():
            shutil.rmtree(vector_store_path)
            logger.info(f"Removed vector store: {vector_store_path}")

        if metadata_file.exists():
            metadata_file.unlink()
            logger.info(f"Removed metadata file: {metadata_file}")

        logger.info("Vector database cleaned successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during clean: {e}")
        return False


def cmd_test(args):
    """Test search functionality"""
    if not check_dependencies():
        return False

    try:
        rag_service = get_rag_service(args.path)

        # Check if any files are processed
        status = rag_service.get_status()
        if status["processed_files_count"] == 0:
            logger.error("No files processed yet. Run 'vectorize' command first.")
            return False

        # Test search
        test_query = args.query or "diabetes treatment guidelines"
        logger.info(f"Testing search with query: '{test_query}'")

        results = rag_service.search_references(test_query, n_results=3)

        if results:
            print(f"\n=== Search Results for '{test_query}' ===")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Source: {result['source']} (Page {result['page']})")
                print(f"   Relevance: {result['relevance_score']:.3f}")
                print(f"   Text: {result['text'][:200]}...")
        else:
            print("No results found")

        return True

    except Exception as e:
        logger.error(f"Error during test: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="RAG Management Tool")
    parser.add_argument("--path", type=str, help="Path to reference_books directory")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show vectorization status")

    # Vectorize command
    subparsers.add_parser("vectorize", help="Run vectorization")

    # Refresh command
    subparsers.add_parser("refresh", help="Force refresh all files")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean vector database")
    clean_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test search functionality")
    test_parser.add_argument("--query", type=str, help="Search query to test")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    commands = {
        "status": cmd_status,
        "vectorize": cmd_vectorize,
        "refresh": cmd_refresh,
        "clean": cmd_clean,
        "test": cmd_test,
    }

    success = commands[args.command](args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
