#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"

if [[ -x "$project_dir/.venv/bin/python" ]]; then
    python="$project_dir/.venv/bin/python"
else
    python="python3"
fi

"$python" -m unittest discover -s tests -p 'test*.py' -v
