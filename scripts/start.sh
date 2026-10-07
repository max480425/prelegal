#!/usr/bin/env bash
# Start Prelegal: build the Docker image and run the container.
# App available at http://localhost:8000
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not on PATH." >&2
  exit 1
fi

echo "Building and starting Prelegal..."
docker compose up -d --build

echo ""
echo "Prelegal is starting at http://localhost:8000"
echo "API docs:            http://localhost:8000/docs"
echo "Stop with:           scripts/stop.sh (or the OS-specific wrapper)"
