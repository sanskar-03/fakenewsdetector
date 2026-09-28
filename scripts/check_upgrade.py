from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parents[1]
required = [
    "frontend/index.html", "frontend/styles.css", "frontend/app.js",
    "backend/services/case_store.py", "backend/services/report_generator.py",
    "backend/services/trusted_sources.py", "backend/api/history.py", "backend/api/report.py",
    "data/trusted_sources.json", "Dockerfile", "docker-compose.yml",
]
missing=[p for p in required if not (ROOT/p).exists()]
if missing:
    print("UPGRADE CHECK FAILED")
    for p in missing: print(" -",p)
    raise SystemExit(1)
files=list(ROOT.glob("backend/**/*.py"))+[ROOT/"upgrade_aletheia_final.py"]
errors=[]
for p in files:
    try:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except SyntaxError as exc:
        errors.append((p,exc))
if errors:
    print("PYTHON SYNTAX CHECK FAILED")
    for p,e in errors: print(" -",p,":",e)
    raise SystemExit(1)
print("ALETHEIA UPGRADE CHECK: OK")
print(f"Python files checked: {len(files)}")
