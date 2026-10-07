#!/usr/bin/env bash
# Stop Prelegal: remove the container (the SQLite DB is ephemeral).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Stopping Prelegal..."
docker compose down

echo "Prelegal stopped."
