from functools import lru_cache
from backend.config.settings import get_settings

@lru_cache
def get_classifier():
    from transformers import pipeline
    s=get_settings()
    return pipeline("zero-shot-classification", model=s.model_name)

def classify(text):
    try:
        result=get_classifier()(text, candidate_labels=["fake news", "real news"], multi_label=False)
        scores=dict(zip(result["labels"], result["scores"]))
        fake=float(scores.get("fake news",0.0)); real=float(scores.get("real news",0.0))
        label="FAKE" if fake>=real else "REAL"
        return {"label":label,"confidence":round(max(fake,real),4),"fake_probability":round(fake,4),"real_probability":round(real,4),"model":get_settings().model_name,"mode":"zero-shot"}
    except Exception as exc:
        return {"label":"UNAVAILABLE","confidence":0.0,"fake_probability":0.0,"real_probability":0.0,"model":get_settings().model_name,"error":str(exc)}
