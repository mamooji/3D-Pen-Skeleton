#comment from my mac
#!/usr/bin/env bash
# Build the frontend (if needed) and serve the whole app at http://127.0.0.1:8000
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$root/backend/.venv" ]; then
    # Needs Python 3.10+ (macOS ships 3.9; `brew install python@3.12`).
    python="$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)"
    "$python" -m venv "$root/backend/.venv"
    "$root/backend/.venv/bin/python" -m pip install -r "$root/backend/requirements.txt"
fi
if [ ! -d "$root/frontend/node_modules" ]; then
    (cd "$root/frontend" && npm ci)
fi
(cd "$root/frontend" && npm run build)

cd "$root/backend"
echo "Open http://127.0.0.1:8000"
exec .venv/bin/python -m uvicorn app.main:app --port 8000
