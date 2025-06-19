# PHRM Project Structure

## Core Files
- `setup.py` - Database setup and sample data generation
- `start_phrm.py` - Main application server
- `pyproject.toml` - Project dependencies and configuration
- `README.md` - Main project documentation

## Directories
- `app/` - Main application code
  - `models/` - Database models
  - `templates/` - HTML templates
  - `static/` - CSS, JS, images
  - `api/` - API endpoints
  - `utils/` - Utility functions
- `docs/` - Project documentation
- `scripts/` - Utility scripts
- `tests/` - Test files
- `migrations/` - Database migrations
- `instance/` - Database files (created at runtime)

## Key Scripts
- `setup.py` - Initialize database and create sample data
- `start_phrm.py` - Start the web application
- `scripts/quick_start.py` - Auto-setup and run
- `scripts/run_tests.py` - Run test suite

## Documentation
- `README.md` - Main project documentation
- `docs/` - Additional documentation files
  - `ENHANCED_DEPLOYMENT_GUIDE.md` - Deployment instructions
  - `API_TOKEN_MANAGEMENT.md` - API configuration
  - `PROJECT_SUMMARY.md` - Detailed project overview
