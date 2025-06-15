"""
Local RAG (Retrieval-Augmented Generation) Service

This module handles vectorization of reference books and provides
retrieval functionality for AI-powered medical reference queries.
"""

import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Optional

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from flask import current_app

logger = logging.getLogger(__name__)


class LocalRAGService:
    """Service for managing local RAG functionality with reference books"""

    def __init__(self, reference_books_path: Optional[str] = None):
        if reference_books_path:
            self.reference_books_path = reference_books_path
        else:
            # Path to reference_books in project root
            app_dir = os.path.dirname(os.path.dirname(__file__))  # app directory
            project_root = os.path.dirname(app_dir)  # project root
            self.reference_books_path = os.path.join(project_root, "reference_books")
        self.vector_store_path = os.path.join(
            self.reference_books_path, ".vector_store"
        )
        self.metadata_file = os.path.join(self.reference_books_path, ".metadata.json")

        # Process isolation flag - when True, prevents app interference
        self._isolated_mode = os.getenv("RAG_ISOLATED_MODE", "false").lower() == "true"

        # Initialize ChromaDB lazily - only when first accessed
        self.chroma_client = None
        self.collection = None
        self._chroma_initialized = False

    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        if self._chroma_initialized and self.chroma_client:
            return  # Already initialized

        try:
            # Use different persistence directories for isolated mode
            persist_directory = self.vector_store_path
            if self._isolated_mode:
                persist_directory = f"{self.vector_store_path}_isolated"
                logger.info(f"Using isolated vector store: {persist_directory}")

            os.makedirs(persist_directory, exist_ok=True)

            # Enhanced settings for stability
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
                persist_directory=persist_directory,
            )

            logger.info(
                f"Initializing ChromaDB persistent client at: {persist_directory}"
            )

            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory, settings=settings
            )

            # Create or get collection for medical references
            self.collection = self.chroma_client.get_or_create_collection(
                name="medical_references",
                metadata={"description": "Medical reference books and documents"},
            )

            self._chroma_initialized = True
            logger.info(
                f"ChromaDB initialized successfully with collection: {self.collection.name} ({'isolated' if self._isolated_mode else 'normal'} mode)"
            )

            logger.info(
                f"ChromaDB initialized with collection: {self.collection.name} ({'isolated' if self._isolated_mode else 'normal'} mode)"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None

    def _extract_text_from_pdf(self, pdf_path: str) -> list[dict[str, Any]]:
        """Extract text from PDF in chunks"""
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, cannot extract PDF text")
            return []

        chunks = []
        try:
            doc = fitz.open(pdf_path)
            filename = os.path.basename(pdf_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()

                if text.strip():
                    # Split page into smaller chunks (approximately 1000 characters)
                    text_chunks = self._split_text(text, max_length=1000)

                    for i, chunk in enumerate(text_chunks):
                        if chunk.strip():
                            chunks.append(
                                {
                                    "text": chunk.strip(),
                                    "source": filename,
                                    "page": page_num + 1,
                                    "chunk_id": f"{filename}_p{page_num + 1}_c{i + 1}",
                                    "metadata": {
                                        "file_path": pdf_path,
                                        "page_number": page_num + 1,
                                        "chunk_index": i + 1,
                                        "extraction_date": datetime.now().isoformat(),
                                    },
                                }
                            )

            doc.close()
            logger.info(f"Extracted {len(chunks)} chunks from {filename}")

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")

        return chunks

    def _split_text(self, text: str, max_length: int = 1000) -> list[str]:
        """Split text into chunks of approximately max_length characters"""
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""
        sentences = text.split(". ")

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _get_file_hash(self, file_path: str) -> str:
        """Get MD5 hash of file for change detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
        return hash_md5.hexdigest()

    def _load_metadata(self) -> dict[str, Any]:
        """Load processing metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {"processed_files": {}, "last_updated": None}

    def _save_metadata(self, metadata: dict[str, Any]):
        """Save processing metadata to file"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def vectorize_reference_books(self, background: bool = False) -> bool:
        """Vectorize all PDF files in the reference_books directory"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, cannot vectorize files")
            return False

        if not self._ensure_chroma_initialized():
            logger.error("ChromaDB collection not initialized")
            return False

        if not os.path.exists(self.reference_books_path):
            logger.warning(
                f"Reference books directory not found: {self.reference_books_path}"
            )
            return False

        if background:
            # Run vectorization in background thread
            def background_vectorization():
                self._vectorize_files()

            thread = threading.Thread(target=background_vectorization, daemon=True)
            thread.start()
            logger.info("Started background vectorization process")
            return True
        else:
            return self._vectorize_files()

    def _vectorize_files(self) -> bool:
        """Internal method to perform actual vectorization"""
        metadata = self._load_metadata()
        processed_count = 0

        try:
            # Find all PDF files
            pdf_files = []
            for file in os.listdir(self.reference_books_path):
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(self.reference_books_path, file))

            logger.info(f"Found {len(pdf_files)} PDF files to process")

            for pdf_path in pdf_files:
                filename = os.path.basename(pdf_path)
                current_hash = self._get_file_hash(pdf_path)

                # Check if file has already been processed
                if (
                    filename in metadata["processed_files"]
                    and metadata["processed_files"][filename].get("hash")
                    == current_hash
                ):
                    logger.info(f"Skipping {filename} - already processed")
                    continue

                logger.info(f"Processing {filename}...")

                # Extract text chunks
                chunks = self._extract_text_from_pdf(pdf_path)

                if chunks:
                    # Process in batches to avoid memory issues
                    batch_size = 100
                    for i in range(0, len(chunks), batch_size):
                        batch = chunks[i : i + batch_size]

                        # Prepare data for ChromaDB
                        documents = [chunk["text"] for chunk in batch]
                        metadatas = [chunk["metadata"] for chunk in batch]
                        ids = [chunk["chunk_id"] for chunk in batch]

                        # Add to ChromaDB collection
                        self.collection.add(
                            documents=documents, metadatas=metadatas, ids=ids
                        )

                        logger.info(
                            f"Processed batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size} for {filename}"
                        )

                    # Update metadata
                    metadata["processed_files"][filename] = {
                        "hash": current_hash,
                        "chunks_count": len(chunks),
                        "processed_date": datetime.now().isoformat(),
                        "file_path": pdf_path,
                    }

                    # Save metadata after each file
                    self._save_metadata(metadata)

                    processed_count += 1
                    logger.info(
                        f"Successfully processed {filename} with {len(chunks)} chunks"
                    )

                else:
                    logger.warning(f"No text extracted from {filename}")

            # Update final metadata
            metadata["last_updated"] = datetime.now().isoformat()
            self._save_metadata(metadata)

            logger.info(f"Vectorization complete. Processed {processed_count} files.")
            return True

        except Exception as e:
            logger.error(f"Error during vectorization: {e}")
            return False

    def search_references(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search vectorized reference books for relevant information"""
        if not CHROMADB_AVAILABLE or not self._ensure_chroma_initialized():
            logger.warning("ChromaDB not available for search")
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = (
                        results["metadatas"][0][i] if results["metadatas"][0] else {}
                    )
                    distance = (
                        results["distances"][0][i] if results["distances"][0] else 1.0
                    )

                    formatted_results.append(
                        {
                            "text": doc,
                            "source": metadata.get("file_path", "unknown"),
                            "page": metadata.get("page_number", 0),
                            "relevance_score": 1.0
                            - distance,  # Convert distance to relevance
                            "metadata": metadata,
                        }
                    )

            logger.info(
                f"Found {len(formatted_results)} relevant references for query: {query[:50]}..."
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching references: {e}")
            return []

    def get_status(self) -> dict[str, Any]:
        """Get status information about the RAG service"""
        metadata = self._load_metadata()

        # Check if vectorization is in progress
        is_processing = self._is_vectorization_in_progress()

        status = {
            "available": CHROMADB_AVAILABLE and PYMUPDF_AVAILABLE,
            "reason": self._get_availability_reason(),
            "chromadb_available": CHROMADB_AVAILABLE,
            "pymupdf_available": PYMUPDF_AVAILABLE,
            "collection_initialized": self._chroma_initialized
            and self.collection is not None,
            "reference_books_path": self.reference_books_path,
            "processed_files_count": len(metadata.get("processed_files", {})),
            "last_updated": metadata.get("last_updated"),
            "processed_files": list(metadata.get("processed_files", {}).keys()),
            "is_processing": is_processing,
        }

        # Only get collection count if ChromaDB is already initialized
        if self._chroma_initialized and self.collection:
            try:
                collection_count = self.collection.count()
                status["total_chunks"] = collection_count
            except Exception as e:
                logger.error(f"Error getting collection count: {e}")
                status["total_chunks"] = 0
        else:
            status["total_chunks"] = 0

        # Add processing status
        if is_processing:
            status["status_message"] = "Vectorization in progress..."
        elif status["processed_files_count"] == 0:
            status["status_message"] = "No files processed yet"
        else:
            status["status_message"] = (
                f"Ready with {status['processed_files_count']} reference books"
            )

        return status

    def _is_vectorization_in_progress(self) -> bool:
        """Check if vectorization is currently in progress"""
        # Simple check - could be enhanced with a proper status file
        return threading.active_count() > 1  # Main thread + background thread(s)

    def refresh_all(self) -> bool:
        """Force refresh of all reference books (re-process everything)"""
        if not CHROMADB_AVAILABLE or not self._ensure_chroma_initialized():
            return False

        try:
            # Clear existing collection
            self.collection.delete()

            # Recreate collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="medical_references",
                metadata={"description": "Medical reference books and documents"},
            )

            # Clear metadata
            metadata = {"processed_files": {}, "last_updated": None}
            self._save_metadata(metadata)

            # Re-vectorize all files
            return self.vectorize_reference_books()

        except Exception as e:
            logger.error(f"Error during refresh: {e}")
            return False

    def _ensure_chroma_initialized(self):
        """Ensure ChromaDB is initialized before use"""
        if not self._chroma_initialized and CHROMADB_AVAILABLE:
            self._initialize_chroma()
            self._chroma_initialized = True
        return self.chroma_client is not None

    def _get_availability_reason(self) -> str:
        """Get reason why RAG might not be available"""
        if not CHROMADB_AVAILABLE:
            return "ChromaDB not installed"
        if not PYMUPDF_AVAILABLE:
            return "PyMuPDF not installed"
        if not os.path.exists(self.reference_books_path):
            return "Reference books directory not found"
        if not self._chroma_initialized:
            return "Not initialized yet"
        if self.collection is None:
            return "No collection available"
        return "Available"


# Global RAG service instance (initialized lazily)
rag_service = None


def _get_rag_service():
    """Get or create the global RAG service instance"""
    global rag_service
    if rag_service is None:
        try:
            rag_service = LocalRAGService()
        except Exception as e:
            logger.error(f"Failed to create RAG service: {e}")
            rag_service = None
    return rag_service


def initialize_rag():
    """Initialize RAG service with no automatic vectorization"""
    global rag_service

    if not CHROMADB_AVAILABLE:
        if hasattr(current_app, "logger"):
            current_app.logger.warning(
                "ChromaDB not available - RAG functionality disabled"
            )
        else:
            logger.warning("ChromaDB not available - RAG functionality disabled")
        return False

    if not PYMUPDF_AVAILABLE:
        if hasattr(current_app, "logger"):
            current_app.logger.warning(
                "PyMuPDF not available - cannot process PDF files"
            )
        else:
            logger.warning("PyMuPDF not available - cannot process PDF files")
        return False

    try:
        # Initialize the global service
        rag_service = LocalRAGService()
        # Just log that the service is ready - don't trigger ChromaDB initialization
        if hasattr(current_app, "logger"):
            current_app.logger.info("RAG service initialized (lazy loading mode)")
            current_app.logger.info(
                "RAG ready - vectorization must be triggered manually via API or script"
            )
        else:
            logger.info("RAG service initialized (lazy loading mode)")
            logger.info(
                "RAG ready - vectorization must be triggered manually via API or script"
            )

        return True

    except Exception as e:
        if hasattr(current_app, "logger"):
            current_app.logger.error(f"Error initializing RAG service: {e}")
        else:
            logger.error(f"Error initializing RAG service: {e}")
        return False


def start_background_vectorization():
    """Start background vectorization process"""
    service = _get_rag_service()
    if service:
        return service.vectorize_reference_books(background=True)
    return False


def search_medical_references(query: str, n_results: int = 5) -> list[dict[str, Any]]:
    """Search medical reference books for relevant information"""
    service = _get_rag_service()
    if service:
        try:
            return service.search_references(query, n_results)
        except Exception as e:
            logger.error(f"Error searching medical references: {e}")
            return []
    return []


def get_rag_status() -> dict[str, Any]:
    """Get current status of the RAG service"""
    service = _get_rag_service()
    if service:
        try:
            return service.get_status()
        except Exception as e:
            logger.error(f"Error getting RAG status: {e}")
            return {"chromadb_available": False, "error": str(e)}
    return {"chromadb_available": False, "error": "RAG service not available"}


def refresh_reference_books() -> bool:
    """Refresh/re-process all reference books"""
    service = _get_rag_service()
    if service:
        try:
            return service.refresh_all()
        except Exception as e:
            logger.error(f"Error refreshing reference books: {e}")
            return False
    return False
