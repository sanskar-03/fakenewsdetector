@echo off
cd /d "%~dp0"
python -m pip install -r backend\requirements.txt
python -m pytest -q
python deep_scan.py
python -m uvicorn backend.app:app --reload
