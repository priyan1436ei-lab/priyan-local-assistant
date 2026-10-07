#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --only-binary=llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt
.venv/bin/python -m pip install -r requirements-documents.txt
.venv/bin/python setup.py --model
.venv/bin/python -m pip freeze > installed-versions.txt
printf '\nReady. Run: sh start.sh\n'
