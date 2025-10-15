#!/usr/bin/env bash
# Copyright (c) [2025] NirrussVn0

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENTRYPOINT="${SCRIPT_DIR}/main.py"
export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

if command -v uv >/dev/null 2>&1; then
  exec uv run python "$ENTRYPOINT" "$@"
elif [ -d "${SCRIPT_DIR}/.venv" ] && [ -x "${SCRIPT_DIR}/.venv/bin/python" ]; then
  exec "${SCRIPT_DIR}/.venv/bin/python" "$ENTRYPOINT" "$@"
else
  exec python "$ENTRYPOINT" "$@"
fi
