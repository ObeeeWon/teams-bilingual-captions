#!/usr/bin/env bash
# Recommended entry point: bootstrap + run the app.
# Usage:
#   ./run.sh --audio mic          # microphone test
#   ./run.sh --audio blackhole    # Teams system audio
#   ./run.sh --simulate --fast    # demo without keys
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Prefer project venv if present
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python3 -m src.bootstrap
exec python3 -m src.main "$@"
