# Personal Health Record Manager (PHRM)

## Overview
PHRM is a Flask-based web application for managing personal health records, featuring AI-powered chat, symptom checker, and document summarization. The default AI provider is MedGemma (via Hugging Face or local), with GROQ and DEEPSEEK as fallbacks.

## AI Provider Fallback Logic
- **Primary:** MedGemma (Hugging Face Inference API or local transformers)
- **Fallbacks:** GROQ, DEEPSEEK

## Setup
1. Clone the repo and install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Configure `.env` with your API keys (see example in repo).
3. Run the app:
   ```sh
   python run.py
   ```

## Testing
- Run `python test_ai_providers.py` to check AI provider status.

## Production Cleanup
- All test, debug, and temporary scripts are removed or ignored via `.gitignore` for production deployments.
- For best performance, ensure no `__pycache__` or `.pyc` files remain in the codebase.

## Maintenance
- Keep dependencies up to date in `requirements.txt`.
- Review `.env` for only necessary secrets and keys.
- For further optimization, review and refactor utility modules in `app/utils/` as needed.

## Notes
- MedGemma models require gated access on Hugging Face.
- Remove or ignore test scripts (`test_*.py`) in production deployments.

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

1. **Install dependencies and create a virtual environment:**
   ```zsh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
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
