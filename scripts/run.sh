#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

source venv/bin/activate
export PYTHONPATH="$PROJECT_DIR"

echo "Starting SMS-Engine API on http://0.0.0.0:8000"
exec uvicorn aviation.api.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning
