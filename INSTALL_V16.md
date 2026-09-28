# Aletheia V16 — Deep Fix

1. Replace the old Aletheia project folder with this package, or copy these files over the existing project after making a backup.
2. Create/activate the Python environment.
3. Install dependencies:
   `pip install -r backend/requirements.txt`
4. Start the backend from the project root:
   `python -m uvicorn backend.app:app --reload`
5. Open `http://127.0.0.1:8000`.
6. Run the deep regression scan:
   `python deep_scan.py`

The package intentionally does not include the old SQLite case history or old repair/back-up folders.
