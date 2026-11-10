#!/usr/bin/env bash
# Start both halves of the hybrid backend: Spring Boot (:8001) + Python AI (:8002).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/backend/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Missing $PY — create the virtualenv first (see README)." >&2
  exit 1
fi

if [[ -d /opt/homebrew/bin ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi
if [[ -d /opt/homebrew/opt/openjdk@21 ]]; then
  export JAVA_HOME=/opt/homebrew/opt/openjdk@21
  export PATH="$JAVA_HOME/bin:$PATH"
fi

if ! command -v java >/dev/null 2>&1 || ! command -v gradle >/dev/null 2>&1; then
  echo "Java 21 and Gradle are required to run the Spring backend." >&2
  exit 1
fi

cleanup() {
  kill "$AI_PID" "$SPRING_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting Python AI service on http://127.0.0.1:8002 ..."
"$PY" -m uvicorn app:app --app-dir "$ROOT/backend-ai" \
  --host 127.0.0.1 --port 8002 &
AI_PID=$!

echo "Starting Spring Boot on http://127.0.0.1:8001/api/v1 ..."
(cd "$ROOT/backend-spring" && gradle bootRun --no-daemon --console=plain) &
SPRING_PID=$!

wait -n "$AI_PID" "$SPRING_PID"
