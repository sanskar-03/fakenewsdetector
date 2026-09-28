import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "trusted_sources.json"

try:
    DATA = json.loads(REGISTRY.read_text(encoding="utf-8"))
    TRUSTED_SOURCES = DATA.get("all", [])
except Exception:
    TRUSTED_SOURCES = []

TRUSTED_DOMAINS = {item["domain"] for item in TRUSTED_SOURCES}
SOURCE_SCORES = {item["domain"]: float(item.get("score", 0.75)) for item in TRUSTED_SOURCES}


def source_score(value: str, default: float = 0.40) -> float:
    value = (value or "").lower()
    for domain, score in SOURCE_SCORES.items():
        if domain in value:
            return score
    return default


def is_trusted(value: str) -> bool:
    value = (value or "").lower()
    return any(domain in value for domain in TRUSTED_DOMAINS)
