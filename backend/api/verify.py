import asyncio, time, uuid
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
from backend.services.agent import verify_news
from backend.services.case_store import persist_case_result
from backend.rag.ingest import ingest_all_feeds

router = APIRouter(prefix='/api/v1')
_CACHE = {}

class VerifyRequest(BaseModel):
    article: str = Field(..., min_length=20, max_length=20000)
    article_url: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=2000)
    language: str = Field('en', max_length=10)

    @field_validator('article')
    @classmethod
    def article_clean(cls, v):
        v = v.strip()
        if len(v) < 20:
            raise ValueError('Article or claim must contain at least 20 characters.')
        return v

    @field_validator('image_url')
    @classmethod
    def image_valid(cls, v):
        if v and not v.strip().lower().startswith(('http://','https://')):
            raise ValueError('image_url must be an HTTP(S) URL')
        return v.strip() if v else None

def key(req):
    return (req.article.strip().lower(), req.article_url or '', req.image_url or '', req.language)

@router.post('/verify')
@persist_case_result
async def verify(req: VerifyRequest):
    k = key(req)
    now = time.time()
    if k in _CACHE and now - _CACHE[k][0] < 300:
        return _CACHE[k][1]
    result = await verify_news(req.article, req.image_url, req.language, req.article_url)
    result['article_url'] = req.article_url
    result['case_id'] = 'AF-' + uuid.uuid4().hex[:10].upper()
    result['cached'] = False
    _CACHE[k] = (now, result)
    return result

@router.get('/health')
async def health():
    return {'status':'ok','service':'aletheia-backend'}

@router.get('/metrics')
async def metrics():
    return {'cache_entries':len(_CACHE),'cache_ttl_seconds':300,'architecture':'async-parallel-evidence-verification'}

@router.post('/admin/ingest')
async def ingest():
    return {'results': await asyncio.to_thread(ingest_all_feeds)}
