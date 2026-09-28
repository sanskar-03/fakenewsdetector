from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

router = APIRouter(prefix="/api/v1", tags=["language"])


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    target: str = Field(default="en", min_length=2, max_length=5)


@router.post("/translate")
def translate(request: TranslationRequest):
    if request.target == "en" or GoogleTranslator is None:
        return {"text": request.text, "translated": False}
    try:
        value = GoogleTranslator(source="auto", target=request.target).translate(request.text)
        return {"text": value or request.text, "translated": bool(value)}
    except Exception:
        return {"text": request.text, "translated": False}
