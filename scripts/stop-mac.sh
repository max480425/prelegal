#!/usr/bin/env bash
# Stop Prelegal (Mac) — thin wrapper around scripts/stop.sh
exec "$(dirname "$0")/stop.sh" "$@"
