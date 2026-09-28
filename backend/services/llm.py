import json, requests
from backend.config.settings import get_settings

LANGUAGE_NAMES = {
    "en":"English","hi":"Hindi","ta":"Tamil","bn":"Bengali","te":"Telugu",
    "mr":"Marathi","gu":"Gujarati","kn":"Kannada","ml":"Malayalam","pa":"Punjabi"
}

def reason_with_llm(claim, evidence, classification, language="en"):
    s = get_settings()
    lang_name = LANGUAGE_NAMES.get(language, "English")
    prompt = (
        "You are a careful fact-checking assistant. Return JSON only with keys "
        "verdict and reasoning. Verdict must be REAL, FAKE, or UNVERIFIED. "
        f"Write the reasoning in {lang_name}. Never invent evidence. "
        f"Claim: {claim}\nClassifier: {json.dumps(classification, ensure_ascii=False)}"
        f"\nEvidence: {json.dumps(evidence[:10], ensure_ascii=False)}"
    )
    try:
        resp = requests.post(
            s.ollama_url.rstrip('/') + '/api/generate',
            json={'model': s.ollama_model, 'prompt': prompt, 'stream': False},
            timeout=s.ollama_timeout_seconds
        )
        resp.raise_for_status()
        txt = resp.json().get('response','').strip()
        obj = json.loads(txt)
        if obj.get('verdict') in {'REAL','FAKE','UNVERIFIED'}:
            return {'verdict': obj['verdict'], 'reasoning': str(obj.get('reasoning') or '').strip(),
                    'provider': 'ollama', 'llm_status': 'OK'}
        return {'verdict': None, 'reasoning': '', 'provider': 'ollama', 'llm_status': 'INVALID'}
    except Exception as exc:
        return {'verdict': None, 'reasoning': '', 'provider': 'fallback',
                'llm_status': 'FALLBACK', 'error': str(exc)}

# Kept for compatibility with the previous timeout patch.
def _aletheia_ollama_call(fn, *args, **kwargs):
    return fn(*args, **kwargs)
