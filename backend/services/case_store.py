import json
import sqlite3
import threading
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA / "aletheia_cases.sqlite3"
LOCK = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with LOCK:
        conn = _connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                title TEXT,
                claim TEXT,
                verdict TEXT,
                confidence REAL,
                evidence_strength TEXT,
                language TEXT,
                payload TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cases_created "
            "ON cases(created_at DESC)"
        )
        conn.commit()
        conn.close()


def _extract_case_id(value):
    if not isinstance(value, dict):
        return None
    result = value.get("result")
    if isinstance(result, dict):
        return result.get("case_id") or value.get("case_id")
    return value.get("case_id")


def save_case(case_id, payload):
    if not case_id:
        return
    result = payload.get("result") if isinstance(payload, dict) else {}
    if not isinstance(result, dict):
        result = {}
    title = payload.get("title") or payload.get("article_title") or result.get("title") or ""
    claim = payload.get("article") or payload.get("claim") or payload.get("text") or ""
    verdict = result.get("verdict") or payload.get("verdict") or "UNVERIFIED"
    confidence = result.get("confidence", payload.get("confidence", 0)) or 0
    evidence_strength = result.get("evidence_strength") or payload.get("evidence_strength") or ""
    language = payload.get("language") or result.get("language") or "en"
    payload_json = json.dumps(payload, ensure_ascii=False)
    init_db()
    with LOCK:
        conn = _connect()
        conn.execute("""
            INSERT INTO cases (
                case_id, created_at, title, claim, verdict,
                confidence, evidence_strength, language, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                title=excluded.title,
                claim=excluded.claim,
                verdict=excluded.verdict,
                confidence=excluded.confidence,
                evidence_strength=excluded.evidence_strength,
                language=excluded.language,
                payload=excluded.payload
        """, (
            str(case_id),
            datetime.now(timezone.utc).isoformat(),
            str(title),
            str(claim)[:10000],
            str(verdict),
            float(confidence),
            str(evidence_strength),
            str(language),
            payload_json,
        ))
        conn.commit()
        conn.close()


def persist_case_result(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        case_id = _extract_case_id(result)
        if case_id:
            try:
                save_case(case_id, result)
            except Exception:
                pass
        return result

    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        case_id = _extract_case_id(result)
        if case_id:
            try:
                save_case(case_id, result)
            except Exception:
                pass
        return result

    import inspect
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper


def get_case(case_id):
    init_db()
    conn = _connect()
    row = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
    conn.close()
    if not row:
        return None
    data = json.loads(row["payload"])
    if isinstance(data, dict):
        data.setdefault("_history", {})
        data["_history"].update({
            "case_id": row["case_id"],
            "created_at": row["created_at"],
        })
    return data


def search_cases(limit=50, case_id=None):
    init_db()
    conn = _connect()
    if case_id:
        rows = conn.execute("""
            SELECT case_id, created_at, title, claim,
                   verdict, confidence, evidence_strength, language
            FROM cases
            WHERE case_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (case_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT case_id, created_at, title, claim,
                   verdict, confidence, evidence_strength, language
            FROM cases
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_case(case_id):
    init_db()
    with LOCK:
        conn = _connect()
        cur = conn.execute("DELETE FROM cases WHERE case_id=?", (case_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
    return deleted


init_db()
