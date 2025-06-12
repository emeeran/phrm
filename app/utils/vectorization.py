# Document vectorization utilities for RAG (Retrieval-Augmented Generation)
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from flask import current_app

from ..models import Document, db

# Configure logging
logger = logging.getLogger(__name__)

# Constants for configuration
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SEARCH_K = 5
VECTOR_STORE_DIR = "vector_stores"
PROCESSED_INDEX_FILE = "processed_files.json"

# Type imports for static analysis
if TYPE_CHECKING:
    from langchain.schema import Document as LangchainDocument
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

# Optional dependencies handling for vectorization
VECTORIZATION_AVAILABLE = False
try:
    from langchain.schema import Document as LangchainDocument
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

    VECTORIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning(
        f"LangChain dependencies not available. Vectorization disabled. Error: {e}"
    )
    # Only define when types are not available
    if not TYPE_CHECKING:
        # Create dummy classes for runtime to avoid AttributeError
        class _DummyClass:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, *args, **kwargs):
                return self

            def __getattr__(self, name):
                return _DummyClass()

        RecursiveCharacterTextSplitter = _DummyClass
        PyPDFLoader = _DummyClass
        TextLoader = _DummyClass
        Chroma = _DummyClass
        OpenAIEmbeddings = _DummyClass
        LangchainDocument = _DummyClass


class VectorizationError(Exception):
    """Custom exception for vectorization operations"""

    pass


class DocumentLoader:
    """Unified document loader for different file types"""

    @staticmethod
    def load_document(file_path: str) -> Optional[List[Any]]:
        """Load document based on file extension"""
        if not VECTORIZATION_AVAILABLE:
            raise VectorizationError("LangChain dependencies not available")

        if not os.path.exists(file_path):
            logger.warning(f"Document file not found: {file_path}")
            return None

        file_ext = Path(file_path).suffix.lower()

        try:
            loader: Union[Any, Any]  # Type hint for MyPy
            if file_ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_ext in [".txt", ".text"]:
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None

            return loader.load()

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None


class VectorStoreManager:
    """Manages vector store operations and persistence"""

    def __init__(self, embeddings: Any):
        self.embeddings = embeddings

    def get_vector_store_path(self, identifier: str) -> str:
        """Get vector store path for a given identifier"""
        base_path = Path(current_app.config["UPLOAD_FOLDER"]) / VECTOR_STORE_DIR
        base_path.mkdir(exist_ok=True)
        return str(base_path / identifier)

    def load_or_create_vectorstore(
        self, path: str, documents: Optional[List[Any]] = None
    ):
        """Load existing vectorstore or create new one"""
        if os.path.exists(path) and not documents:
            return Chroma(persist_directory=path, embedding_function=self.embeddings)

        if documents:
            if os.path.exists(path):
                vectorstore = Chroma(
                    persist_directory=path, embedding_function=self.embeddings
                )
                vectorstore.add_documents(documents)
                return vectorstore
            else:
                return Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=path,
                )

        return None


class DocumentVectorizer:
    """Optimized service for vectorizing documents and managing vector stores"""

    def __init__(
        self,
        embedding_model: str = "openai",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        if not VECTORIZATION_AVAILABLE:
            raise VectorizationError(
                "LangChain dependencies required for vectorization"
            )

        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Lazy initialization for expensive operations
        self._embeddings: Optional[Any] = None
        self._text_splitter: Optional[Any] = None
        self._vector_store_manager: Optional[VectorStoreManager] = None

    @property
    def embeddings(self) -> Any:
        """Get or create embeddings model (lazy initialization)"""
        if self._embeddings is None:
            from ..utils.ai_helpers import get_openai_api_key

            api_key = get_openai_api_key()
            if not api_key:
                raise VectorizationError("OpenAI API key required for embeddings")

            self._embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        return self._embeddings

    @property
    def text_splitter(self) -> Any:
        """Get or create text splitter (lazy initialization)"""
        if self._text_splitter is None:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""],
            )
        return self._text_splitter

    @property
    def vector_store_manager(self) -> VectorStoreManager:
        """Get or create vector store manager (lazy initialization)"""
        if self._vector_store_manager is None:
            self._vector_store_manager = VectorStoreManager(self.embeddings)
        return self._vector_store_manager

    def _create_document_metadata(self, document: Document) -> Dict[str, Any]:
        """Create metadata dictionary for a document"""
        return {
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "uploaded_at": document.uploaded_at.isoformat(),
            "health_record_id": document.health_record_id,
        }

    def extract_and_prepare_text(self, document: Document) -> Optional[List[Any]]:
        """Extract text and prepare LangChain documents"""
        # Use pre-extracted text if available
        if document.extracted_text and document.extracted_text.strip():
            logger.info(f"Using pre-extracted text for {document.filename}")
            content = document.extracted_text.strip()
            metadata = self._create_document_metadata(document)
            langchain_doc = LangchainDocument(page_content=content, metadata=metadata)
            return self.text_splitter.split_documents([langchain_doc])

        # Load and extract text from file
        docs = DocumentLoader.load_document(document.file_path)
        if not docs:
            return None

        # Update metadata for all loaded documents
        metadata = self._create_document_metadata(document)
        for doc in docs:
            doc.metadata.update(metadata)

        # Store extracted text in database for future use
        if not document.extracted_text:
            combined_text = "\n\n".join([doc.page_content for doc in docs])
            document.extracted_text = combined_text
            db.session.commit()

        return self.text_splitter.split_documents(docs)

    def vectorize_document(self, document: Document, user_id: int) -> bool:
        """Vectorize a single document efficiently"""
        try:
            chunks = self.extract_and_prepare_text(document)
            if not chunks:
                logger.warning(
                    f"No text content found in document: {document.filename}"
                )
                return False

            # Get vector store
            vector_db_path = self.vector_store_manager.get_vector_store_path(
                f"user_{user_id}"
            )
            vectorstore = self.vector_store_manager.load_or_create_vectorstore(
                vector_db_path, chunks
            )

            if not vectorstore:
                logger.error(f"Failed to create/load vector store for user {user_id}")
                return False

            # Update document status
            document.vectorized = True
            db.session.commit()

            logger.info(
                f"Successfully vectorized document: {document.filename} ({len(chunks)} chunks)"
            )
            return True

        except Exception as e:
            logger.error(f"Error vectorizing document {document.filename}: {e}")
            db.session.rollback()
            return False

    def vectorize_user_documents(
        self, user_id: int, force_refresh: bool = False
    ) -> Tuple[int, int]:
        """Vectorize all documents for a user efficiently"""
        try:
            # Query optimization: get documents based on refresh flag
            query = Document.query.join(Document.health_record).filter_by(
                user_id=user_id
            )
            if not force_refresh:
                query = query.filter_by(vectorized=False)

            documents = query.all()

            if not documents:
                logger.info(f"No documents to vectorize for user {user_id}")
                return 0, 0

            successful_count = sum(
                1
                for document in documents
                if self.vectorize_document(document, user_id)
            )

            logger.info(
                f"Vectorization complete for user {user_id}: {successful_count}/{len(documents)} successful"
            )
            return successful_count, len(documents)

        except Exception as e:
            logger.error(f"Error vectorizing documents for user {user_id}: {e}")
            return 0, 0

    def get_vectorstore_for_user(self, user_id: int):
        """Get the vector store for a user"""
        try:
            vector_db_path = self.vector_store_manager.get_vector_store_path(
                f"user_{user_id}"
            )
            return self.vector_store_manager.load_or_create_vectorstore(vector_db_path)
        except Exception as e:
            logger.error(f"Error loading vector store for user {user_id}: {e}")
            return None

    def search_documents(
        self, user_id: int, query: str, k: int = DEFAULT_SEARCH_K
    ) -> List[Dict[str, Any]]:
        """Search vectorized documents for a user"""
        try:
            vectorstore = self.get_vectorstore_for_user(user_id)
            if not vectorstore:
                return []

            results = vectorstore.similarity_search_with_score(query, k=k)

            return [
                {
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata,
                    "document_id": doc.metadata.get("document_id"),
                    "filename": doc.metadata.get("filename"),
                    "file_type": doc.metadata.get("file_type"),
                }
                for doc, score in results
            ]

        except Exception as e:
            logger.error(f"Error searching documents for user {user_id}: {e}")
            return []

    def get_vectorization_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive vectorization statistics for a user"""
        try:
            from sqlalchemy import func

            # Optimized query to get counts
            total_docs = (
                db.session.query(func.count(Document.id))
                .join(Document.health_record)
                .filter_by(user_id=user_id)
                .scalar()
                or 0
            )

            vectorized_docs = (
                db.session.query(func.count(Document.id))
                .join(Document.health_record)
                .filter_by(user_id=user_id)
                .filter(Document.vectorized)
                .scalar()
                or 0
            )

            vector_db_path = self.vector_store_manager.get_vector_store_path(
                f"user_{user_id}"
            )
            vector_store_exists = os.path.exists(vector_db_path)

            return {
                "total_documents": total_docs,
                "vectorized_documents": vectorized_docs,
                "pending_vectorization": total_docs - vectorized_docs,
                "vectorization_percentage": (
                    (vectorized_docs / total_docs * 100) if total_docs > 0 else 0
                ),
                "vector_store_exists": vector_store_exists,
                "vector_store_size": (
                    len(os.listdir(vector_db_path)) if vector_store_exists else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting vectorization stats for user {user_id}: {e}")
            return {
                "total_documents": 0,
                "vectorized_documents": 0,
                "pending_vectorization": 0,
                "vectorization_percentage": 0,
                "vector_store_exists": False,
                "vector_store_size": 0,
            }


# Utility Functions


def get_document_vectorizer() -> Optional[DocumentVectorizer]:
    """Get a DocumentVectorizer instance if available"""
    if not VECTORIZATION_AVAILABLE:
        logger.error("Vectorization not available - missing dependencies")
        return None

    try:
        return DocumentVectorizer()
    except Exception as e:
        logger.error(f"Error creating DocumentVectorizer: {e}")
        return None


class BatchVectorizer:
    """Optimized batch processing for large-scale vectorization"""

    def __init__(self, vectorizer: DocumentVectorizer):
        self.vectorizer = vectorizer

    def vectorize_all_unprocessed_documents(self) -> Dict[str, int]:
        """Vectorize all unprocessed documents in the system"""
        try:
            from sqlalchemy import distinct

            # Get all users with documents
            user_ids = (
                db.session.query(
                    distinct(Document.health_record.property.mapper.class_.user_id)
                )
                .join(Document.health_record)
                .all()
            )

            stats = {"total_processed": 0, "total_successful": 0, "users_processed": 0}

            for (user_id,) in user_ids:
                if user_id:  # Skip None values
                    successful, total = self.vectorizer.vectorize_user_documents(
                        user_id
                    )
                    stats["total_processed"] += total
                    stats["total_successful"] += successful
                    stats["users_processed"] += 1
                    logger.info(
                        f"User {user_id}: {successful}/{total} documents vectorized"
                    )

            logger.info(
                f"Batch vectorization complete: {stats['total_successful']}/{stats['total_processed']} documents processed"
            )
            return stats

        except Exception as e:
            logger.error(f"Error in batch vectorization: {e}")
            return {"total_processed": 0, "total_successful": 0, "users_processed": 0}

    def process_folder_documents(
        self, folder_path: str, identifier: str
    ) -> Dict[str, Any]:
        """Process documents from a specific folder"""
        folder_path_obj = Path(folder_path)

        if not folder_path_obj.exists():
            logger.error(f"Folder not found: {folder_path_obj}")
            return {"processed_files": [], "total_files": 0, "success": False}

        # Find supported files
        supported_files = list(folder_path_obj.glob("**/*.pdf")) + list(
            folder_path_obj.glob("**/*.txt")
        )

        if not supported_files:
            logger.info(f"No supported files found in {folder_path_obj}")
            return {"processed_files": [], "total_files": 0, "success": True}

        # Load processed files index
        processed_index_path = self._get_processed_index_path(
            folder_path_obj, identifier
        )
        already_processed = self._load_processed_index(processed_index_path)

        # Filter new files
        new_files = [f for f in supported_files if str(f) not in already_processed]

        if not new_files:
            logger.info(f"All files in {folder_path_obj} already processed")
            return {
                "processed_files": list(already_processed),
                "total_files": len(supported_files),
                "success": True,
            }

        # Process new files
        processed_files = self._vectorize_folder_files(
            new_files, folder_path_obj, identifier
        )

        # Update processed index
        already_processed.update(processed_files)
        self._save_processed_index(processed_index_path, already_processed)

        return {
            "processed_files": processed_files,
            "total_files": len(supported_files),
            "success": True,
        }

    def _get_processed_index_path(self, folder_path: Path, identifier: str) -> Path:
        """Get path for processed files index"""
        vector_stores_path = folder_path.parent / VECTOR_STORE_DIR
        vector_stores_path.mkdir(exist_ok=True)
        return vector_stores_path / f"{identifier}_{PROCESSED_INDEX_FILE}"

    def _load_processed_index(self, index_path: Path) -> set:
        """Load set of already processed files"""
        if not index_path.exists():
            return set()

        try:
            with open(index_path) as f:
                data = json.load(f)
                return set(data.get("processed_files", []))
        except Exception as e:
            logger.warning(f"Could not read processed index {index_path}: {e}")
            return set()

    def _save_processed_index(self, index_path: Path, processed_files: set):
        """Save processed files index"""
        try:
            index_data = {
                "processed_at": datetime.now().isoformat(),
                "processed_files": list(processed_files),
                "total_files": len(processed_files),
            }

            with open(index_path, "w") as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.error(f"Could not save processed index {index_path}: {e}")

    def _vectorize_folder_files(
        self, files: List[Path], base_path: Path, identifier: str
    ) -> List[str]:
        """Vectorize files from a folder"""
        vector_db_path = self.vectorizer.vector_store_manager.get_vector_store_path(
            identifier
        )
        processed_files = []

        for file_path in files:
            try:
                logger.info(f"Processing: {file_path}")

                # Load document
                docs = DocumentLoader.load_document(str(file_path))
                if not docs:
                    logger.warning(f"No content in file: {file_path}")
                    continue

                # Create metadata
                metadata = {
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower().replace(".", ""),
                    "file_size": file_path.stat().st_size,
                    "source": identifier,
                    "processed_at": datetime.now().isoformat(),
                }

                # Update metadata for all documents
                for doc in docs:
                    doc.metadata.update(metadata)

                # Split into chunks
                chunks = self.vectorizer.text_splitter.split_documents(docs)

                if chunks:
                    # Add to vector store
                    vectorstore = (
                        self.vectorizer.vector_store_manager.load_or_create_vectorstore(
                            vector_db_path, chunks
                        )
                    )

                    if vectorstore:
                        processed_files.append(str(file_path))
                        logger.info(
                            f"Successfully processed: {file_path} ({len(chunks)} chunks)"
                        )

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        logger.info(
            f"Folder processing complete: {len(processed_files)} files processed"
        )
        return processed_files


# Convenience functions for backward compatibility
def vectorize_all_unprocessed_documents():
    """Utility function to vectorize all unprocessed documents in the system"""
    vectorizer = get_document_vectorizer()
    if not vectorizer:
        return

    batch_vectorizer = BatchVectorizer(vectorizer)
    return batch_vectorizer.vectorize_all_unprocessed_documents()


def vectorize_uploads_folder():
    """Vectorize documents directly from uploads folder"""
    vectorizer = get_document_vectorizer()
    if not vectorizer:
        return

    uploads_path = Path(current_app.config.get("UPLOAD_FOLDER", "uploads"))
    batch_vectorizer = BatchVectorizer(vectorizer)
    return batch_vectorizer.process_folder_documents(str(uploads_path), "uploads")


def vectorize_and_status_reference_books():
    """Vectorize all reference books and return their status"""
    vectorizer = get_document_vectorizer()
    if not vectorizer:
        return []

    uploads_path = Path(current_app.config.get("UPLOAD_FOLDER", "uploads"))
    ref_folder = uploads_path / "reference_books"

    if not ref_folder.exists():
        logger.warning(f"Reference books folder not found: {ref_folder}")
        return []

    batch_vectorizer = BatchVectorizer(vectorizer)
    result = batch_vectorizer.process_folder_documents(
        str(ref_folder), "reference_books"
    )

    # Convert to expected format
    status_list = []
    for file_path in result.get("processed_files", []):
        path_obj = Path(file_path)
        status_list.append(
            {"filename": path_obj.name, "file_path": str(path_obj), "vectorized": True}
        )

    return status_list
