#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
echo "a11y-audit-forge running on http://127.0.0.1:$PORT"
exec python3 app.py
