#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

source venv/bin/activate
export PYTHONPATH="$PROJECT_DIR"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-sk-placeholder}"

echo "Running tests..."
exec python -m pytest tests/ -v "$@"
