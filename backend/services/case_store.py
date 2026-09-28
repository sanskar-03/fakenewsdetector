import json
import threading
from datetime import datetime, timezone
from functools import wraps
import os
import psycopg2
from psycopg2.extras import DictCursor

NEON_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_pnt48eLiKMBW@ep-spring-frost-b59xw6nh-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
LOCK = threading.Lock()

def _connect():
    return psycopg2.connect(NEON_URL, cursor_factory=DictCursor)

def init_db():
    with LOCK:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("""
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
            cur.execute(
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
    
    with LOCK:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cases (
                    case_id, created_at, title, claim, verdict,
                    confidence, evidence_strength, language, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_id,))
        row = cur.fetchone()
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
    conn = _connect()
    with conn.cursor() as cur:
        if case_id:
            cur.execute("""
                SELECT case_id, created_at, title, claim,
                       verdict, confidence, evidence_strength, language
                FROM cases
                WHERE case_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (case_id, limit))
        else:
            cur.execute("""
                SELECT case_id, created_at, title, claim,
                       verdict, confidence, evidence_strength, language
                FROM cases
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
        rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_case(case_id):
    with LOCK:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM cases WHERE case_id=%s", (case_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        conn.close()
    return deleted

try:
    init_db()
except Exception as e:
    print(f"Warning: Could not initialize Neon Postgres DB: {e}")
