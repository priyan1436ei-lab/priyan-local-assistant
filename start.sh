#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python app.py "$@"
else
  exec python3 app.py "$@"
fi
