#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

source venv/bin/activate
export PYTHONPATH="$PROJECT_DIR"

echo "Starting SMS-Engine API (dev mode) on http://0.0.0.0:8000"
echo "API docs at http://localhost:8000/docs"
exec uvicorn aviation.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
