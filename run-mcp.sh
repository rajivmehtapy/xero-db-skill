#!/bin/bash
# Xero MCP Server — macOS/Linux launcher
# Reads credentials from scripts/.env

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SKILL_DIR/scripts/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found. Copy scripts/.env.example to scripts/.env and fill in your credentials." >&2
  exit 1
fi

# Load .env
set -a
source "$ENV_FILE"
set +a

exec uv run --project "$SKILL_DIR" python "$SKILL_DIR/mcp_server.py"
