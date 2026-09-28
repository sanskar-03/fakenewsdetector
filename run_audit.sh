#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q backend tests
pytest -q
