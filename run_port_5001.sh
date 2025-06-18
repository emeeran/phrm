#!/bin/bash
cd "$(dirname "$0")" || exit 1
export FLASK_APP=run.py
export FLASK_ENV=development
python -m flask run --port=5001 --host=0.0.0.0
