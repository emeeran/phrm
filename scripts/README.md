# PHRM Vectorization Scripts

This directory contains standalone scripts for managing the Local RAG (Retrieval-Augmented Generation) system. These scripts run completely independently from the Flask application to ensure optimal performance.

## Why Separate Vectorization?

Vectorizing large PDF documents can take significant time and resources. To ensure the web application starts quickly and remains responsive, the vectorization process is intentionally separated from app startup.

## Available Scripts

### 1. Quick Start Script
```bash
./scripts/run_vectorization.sh
```
Interactive menu-driven script for common operations:
- Check status
- Run vectorization
- Force refresh all files
- Clean vector database
- Test search functionality

### 2. RAG Manager (Advanced)
```bash
python scripts/rag_manager.py <command>
```

Available commands:
- `status` - Show current vectorization status
- `vectorize` - Process new/changed files only
- `refresh` - Force re-process all files
- `clean [--force]` - Clean vector database
- `test [--query "search terms"]` - Test search functionality

Options:
- `--path /custom/path` - Use custom reference books directory
- `--verbose` - Enable verbose logging

### 3. Standalone Vectorizer
```bash
python scripts/vectorize_references.py [options]
```

Options:
- `--force` - Force re-processing of all files
- `--path /custom/path` - Custom reference books directory
- `--verbose` - Enable verbose logging

## Process Isolation

The scripts use isolated ChromaDB databases to prevent interference with the running application. This ensures:

- No file locks or conflicts
- No impact on app performance
- Safe concurrent operation
- Independent error handling

## Typical Workflow

1. **Initial Setup**: Place PDF files in the `reference_books/` directory
2. **First Run**: Execute `./scripts/run_vectorization.sh` and choose option 2 (vectorize)
3. **Check Status**: Use option 1 to verify processing completed successfully
4. **Add New Files**: Simply add PDFs to `reference_books/` and run vectorization again
5. **Maintenance**: Use option 4 (clean) if you need to reset the vector database

## File Locations

- **Reference Books**: `reference_books/` (project root)
- **Vector Database**: `reference_books/.vector_store/`
- **Metadata**: `reference_books/.metadata.json`
- **Logs**: `vectorization.log` (project root)

## Integration with App

Once vectorization is complete, the web application will automatically detect and use the processed reference books for AI-enhanced medical insights. No app restart required.

## Troubleshooting

### No PDF files found
Ensure PDF files are placed directly in the `reference_books/` directory (not subdirectories).

### Permission errors
Make sure the scripts are executable:
```bash
chmod +x scripts/run_vectorization.sh
```

### Missing dependencies
Install required packages:
```bash
pip install chromadb PyMuPDF
```

### Database locked errors
If you see file lock errors, ensure the Flask app is not running vectorization simultaneously. The isolation mode should prevent this, but stopping the app during manual vectorization is safest.

## Performance Notes

- Vectorization time depends on PDF size and content
- Large medical textbooks may take 10-30 minutes
- Process runs in batches to manage memory usage
- Progress is logged to both console and log file
