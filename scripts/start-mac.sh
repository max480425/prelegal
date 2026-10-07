#!/usr/bin/env bash
# Start Prelegal (Mac) — thin wrapper around scripts/start.sh
exec "$(dirname "$0")/start.sh" "$@"
