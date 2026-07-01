#!/usr/bin/env bash
# Convenience script: start backend (:8000) and frontend (:3000) together.
# Requires backend/.env and frontend/.env.local to exist (copy from the examples).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "▶ Starting FastAPI backend on :8000"
(
  cd "$ROOT/backend"
  [ -d .venv ] || python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r requirements.txt
  uvicorn app.main:app --reload --port 8000
) &
BACKEND_PID=$!

echo "▶ Starting Next.js frontend on :3000"
(
  cd "$ROOT/frontend"
  [ -d node_modules ] || npm install
  npm run dev
) &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT
wait
