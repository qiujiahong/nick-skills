#!/usr/bin/env bash
set -euo pipefail

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to install the remotion skill." >&2
  exit 1
fi

exec npx skills add https://github.com/google-labs-code/stitch-skills --skill remotion
