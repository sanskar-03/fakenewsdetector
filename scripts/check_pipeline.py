from pathlib import Path
import ast
root = Path(__file__).resolve().parents[1]
files = [
    root / "backend/services/source_registry.py",
    root / "backend/services/retriever.py",
    root / "backend/services/llm.py",
    root / "backend/services/graph.py",
    root / "backend/services/agents.py",
    root / "backend/api/verify.py",
]
for path in files:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("ALETHEIA PIPELINE CHECK: PASS")
