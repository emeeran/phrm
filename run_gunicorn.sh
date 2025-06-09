#!/bin/zsh
# Production WSGI server launcher for PHRM
cd "$(dirname "$0")"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
source .venv/bin/activate || source venv/bin/activate || true
export FLASK_ENV=production
export FLASK_DEBUG=0
export FLASK_APP=run:app
exec gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 run:app
