# Personal Health Record Manager (PHRM)

## Overview
PHRM is a Flask-based web application for managing personal health records, featuring AI-powered chat, symptom checker, document summarization, and Local RAG (Retrieval-Augmented Generation) with medical reference books. The default AI provider is MedGemma (via Hugging Face Inference API only), with GROQ and DEEPSEEK as fallbacks.

## Key Features
- **Personal Health Records**: Secure storage and management of medical data
- **AI-Powered Chat**: Medical question answering with MedGemma
- **Local RAG**: Vectorized medical reference books for enhanced AI responses
- **Document Processing**: PDF upload and AI summarization
- **Family Records**: Multi-user health record management

## AI Provider Fallback Logic
- **Primary:** MedGemma 27B (Hugging Face Inference API - remote only, no local models)
- **Fallbacks:** GROQ, DEEPSEEK
- **Enhanced with:** Local RAG from medical reference books

## Setup
1. Clone the repo and install dependencies:
   ```sh
   uv sync
   ```
2. Configure `.env` with your API keys (see example in repo).
3. (Optional) Start Redis for improved performance:
   ```sh
   ./scripts/start-redis.sh
   ```
   > **Note**: Redis is optional. The app will work without it but will use in-memory caching.
4. Run the app:
   ```sh
   python run.py
   ```

## Redis Setup (Optional)
Redis improves performance by providing:
- **Rate limiting storage**: Better than in-memory for production
- **Session caching**: Faster user session management
- **General caching**: Improved response times

### Installation & Usage
- **Start Redis**: `./scripts/start-redis.sh`
- **Stop Redis**: `./scripts/stop-redis.sh`
- **Check Status**: `redis-cli ping` (should return "PONG")

The application automatically detects Redis availability and falls back to in-memory storage if Redis is not running.

## Local RAG Setup (Optional)
To enable enhanced AI responses with medical reference books:

1. Place PDF medical reference books in the `reference_books/` directory
2. Process the reference books using the standalone vectorization script:
   ```sh
   ./scripts/run_vectorization.sh
   ```
3. Choose option 2 to vectorize the books
4. The AI will now use these references for enhanced medical insights

### RAG Management
- **Check Status**: `./scripts/run_vectorization.sh` → option 1
- **Add New Books**: Place PDFs in `reference_books/` and re-run vectorization
- **Advanced Management**: Use `python scripts/rag_manager.py --help`

## Testing
- Use the built-in health check endpoint: `curl http://localhost:5000/health`
- Run `python scripts/rag_manager.py test` to test RAG search functionality.
- View system status in the application dashboard after login.

## Production Cleanup
- All test, debug, and temporary scripts are removed or ignored via `.gitignore` for production deployments.
- For best performance, ensure no `__pycache__` or `.pyc` files remain in the codebase.
- Vector databases are automatically excluded from version control.

## Maintenance
- Keep dependencies up to date with `uv sync`.
- Review `.env` for only necessary secrets and keys.
- For reference book updates, use the standalone vectorization scripts in `scripts/`.
- Project has been streamlined: temporary/test files removed, code quality improved with ruff.

## Notes
- MedGemma models require gated access on Hugging Face.
- Project uses modern Python packaging with `pyproject.toml` and `uv` for dependency management.
- All temporary test files and redundant documentation have been removed for production readiness.

## Environment Variables

Your `.env` file should look like:

```
HUGGINGFACE_ACCESS_TOKEN=hf_...
HUGGINGFACE_MODEL=google/medgemma-4b-it
GROQ_API_KEY=...
GROQ_MODEL=deepseek-r1-distill-llama-70b
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat
```

- Ensure your Hugging Face token has access to MedGemma models (gated repo).
- Only production keys should be present in `.env`.

## Production Deployment

1. **Install dependencies using uv:**
   ```zsh
   uv sync
   ```
2. **Copy and edit the production .env:**
   ```zsh
   cp .env.production.example .env
   # Edit .env with your production secrets and keys
   ```
3. **Run with Gunicorn (recommended for production):**
   ```zsh
   ./run_gunicorn.sh
   # App will be available at http://localhost:8000
   ```

- For systemd or advanced deployment, create a service file pointing to `run_gunicorn.sh`.
- Use a real database (e.g., PostgreSQL) for production, not SQLite.
- Set up HTTPS and a reverse proxy (e.g., Nginx) for secure public access.

## System Status & Features

### ✅ AI Summary System
- **Comprehensive Analysis**: Extracts all health record fields + document content via OCR
- **Smart Caching**: 1-hour cache for instant summary retrieval (0.00s vs 4-5s)
- **Multi-Provider Fallback**: GROQ → DeepSeek → HuggingFace with intelligent error handling
- **Professional Formatting**: HTML output with medical styling and content richness scoring
- **RAG Integration**: Enhanced responses using vectorized medical reference books

### ✅ Performance Optimizations
- **Rate Limiting**: 10 requests/minute with cache-aware processing
- **Error Handling**: Graceful degradation with user-friendly messages
- **Document Processing**: Optimized OCR extraction with smart content limits
- **Database Caching**: Intelligent summary storage and retrieval

### ✅ Production Ready Features
- **Redis Integration**: Optional Redis for enhanced performance and rate limiting
- **Security**: Comprehensive audit logging and access controls
- **Family Records**: Multi-user health record management with proper relationship handling
- **File Management**: Secure upload, OCR processing, and document serving
