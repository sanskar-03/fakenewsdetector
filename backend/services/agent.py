import asyncio
import requests
from backend.services.classifier import classify
from backend.services.retriever import trusted_search, web_search
from backend.services.image_search import verify_image
from backend.services.llm import reason_with_llm
from backend.utils.preprocess import extract_claim, clean_text, extract_title_and_body
from backend.config.settings import get_settings
from backend.services.report_helpers import method_text

LANG={"en":"English","hi":"Hindi","ta":"Tamil","bn":"Bengali","te":"Telugu","mr":"Marathi","gu":"Gujarati","kn":"Kannada","ml":"Malayalam","pa":"Punjabi"}


def _fetch_article(url, timeout=10):
    if not url: return {"title":"","body":"","image_url":"","status":"NOT_REQUESTED"}
    try:
        r=requests.get(url,timeout=timeout,headers={"User-Agent":"Mozilla/5.0 Aletheia/4.0"},allow_redirects=True)
        r.raise_for_status()
        title,body=extract_title_and_body(r.text)
        image_url=''
        try:
            from bs4 import BeautifulSoup
            soup=BeautifulSoup(r.text,'html.parser')
            meta=soup.find('meta',attrs={'property':'og:image'}) or soup.find('meta',attrs={'name':'twitter:image'})
            image_url=(meta.get('content') or '').strip() if meta else ''
        except Exception: pass
        return {"title":title,"body":body,"image_url":image_url,"status":"FETCHED","final_url":r.url}
    except Exception as exc:
        return {"title":"","body":"","image_url":"","status":"ERROR","error":str(exc)}


def _fallback_reasoning(language, trusted, live, verdict):
    total=len(trusted)+len(live)
    if total == 0:
        return "Fake because no any sources found"
    if verdict == 'FAKE':
        return "Fake because sources"
    if verdict == 'REAL':
        return "Real because sources"
    if verdict == 'UNVERIFIED':
        return "Unverified"
    return "Unverified"


def _decision(trusted, total_sources=0):
    gate=[e for e in trusted if e.get('tier') in {'primary','fact_check'} and e.get('relevance',0)>=0.34 and e.get('relation') in {'SUPPORTS','CONTRADICTS','NEUTRAL'}]
    support=[e for e in gate if e.get('relation')=='SUPPORTS']; contra=[e for e in gate if e.get('relation')=='CONTRADICTS']; neutral=[e for e in gate if e.get('relation')=='NEUTRAL']
    support_domains={e.get('source_domain') for e in support if e.get('source_domain')}
    contra_domains={e.get('source_domain') for e in contra if e.get('source_domain')}
    
    if total_sources == 0:
        return 'FAKE', 95.0, 'fake_no_sources_found', 0, 0, 0

    # Independent domains, not repeated pages, are required for REAL consensus.
    if support and contra:
        return 'UNVERIFIED', 55.0, 'trusted_conflict', len(support), len(contra), len(neutral)
    if contra and not support:
        conf=min(96.0,80.0+4.0*min(4,max(0,len(contra_domains)-1)))
        return 'FAKE', round(conf,1), 'fake_because_sources', len(support), len(contra), len(neutral)
    if support:
        conf=min(96.0,84.0+3.0*min(4,max(0,len(support_domains)-1)))
        return 'REAL', round(conf,1), 'real_because_sources', len(support), len(contra), len(neutral)
        
    return 'UNVERIFIED', 25.0 if gate else 20.0, 'insufficient_trusted_evidence', len(support), len(contra), len(neutral)


def _image_status(image):
    if not image: return {'status':'NOT_PROVIDED','verified':False,'message':'No image was supplied.'}
    if not isinstance(image,dict): return {'status':'UNAVAILABLE','verified':False,'message':'Image verification returned no structured result.'}
    image=dict(image); status=str(image.get('status') or 'UNAVAILABLE').upper(); total=int(image.get('total_matches') or 0)
    if status in {'NO_MATCH','NO_REFERENCE_MATCH'} and total==0:
        image['status']='NO_REFERENCE_MATCH'; image['verified']=False; image['message']='No reference match was found. This does not prove authenticity.'
    elif status in {'MATCH','MATCHED'} or total>0:
        image['status']='MATCH'; image['verified']=True
    else: image['verified']=False
    return image


async def verify_news(article, image_url=None, language='en', article_url=None):
    s=get_settings(); language=language if language in LANG else 'en'
    raw=clean_text(article)
    page=await asyncio.to_thread(_fetch_article,article_url,s.image_timeout_seconds) if article_url else {'status':'NOT_REQUESTED','title':'','body':'','image_url':''}
    # User-entered text remains authoritative for the claim. A URL is used to enrich it,
    # not to silently replace the user's statement.
    claim=extract_claim(raw)
    if (not claim or claim==raw[:600]) and page.get('title'):
        claim=extract_claim(page.get('title')+'\n'+page.get('body',''))
    search_text=' '.join(x for x in [claim,page.get('title','')] if x).strip()
    tasks=[asyncio.to_thread(classify,raw),asyncio.to_thread(trusted_search,search_text),asyncio.to_thread(web_search,search_text,max(16,int(s.max_web_results or 16)))]
    effective_image=image_url or page.get('image_url')
    if effective_image: tasks.append(asyncio.to_thread(verify_image,effective_image,[],s.image_hash_threshold,s.image_timeout_seconds,claim))
    else: tasks.append(asyncio.to_thread(lambda:None))
    classification,trusted,live,image=await asyncio.gather(*tasks,return_exceptions=True)
    if isinstance(classification,Exception): classification={'label':'UNAVAILABLE','confidence':0.0,'fake_probability':0.5}
    trusted=[] if isinstance(trusted,Exception) else trusted
    live=[] if isinstance(live,Exception) else live
    image=None if isinstance(image,Exception) else image
    # Trusted gate is ONLY primary/fact-check. Reputable news is retained as corroboration.
    trusted=[dict(x) for x in trusted if x.get('tier') in {'primary','fact_check'} and x.get('relevance',0)>=0.34]
    live=[dict(x) for x in live if x.get('relevance',0)>=0.34]
    # Avoid duplicate evidence across search paths.
    seen=set(); merged=[]
    for x in trusted+live:
        key=(str(x.get('url') or '').split('#')[0].rstrip('/'),x.get('source_domain'),x.get('title'))
        if key in seen: continue
        seen.add(key); merged.append(x)
    evidence=merged
    verdict,confidence,basis,support_n,contra_n,neutral_n=_decision(trusted, len(evidence))
    llm=await asyncio.to_thread(reason_with_llm,claim,evidence,classification,language)
    reasoning=llm.get('reasoning') or _fallback_reasoning(language,trusted,live,verdict)
    image=_image_status(image)
    method=method_text({'llm_status':llm.get('llm_status'),'provider':llm.get('provider'),'article_fetched':page.get('status')=='FETCHED'},language)
    return {'case_id':None,'claim':claim,'language':language,'verdict':verdict,'confidence':confidence,'decision_basis':basis,
            'trusted_supporting_count':support_n,'trusted_contradicting_count':contra_n,'trusted_neutral_count':neutral_n,
            'trusted_source_count':len(trusted),'related_source_count':len(evidence),'classification':classification,
            'reasoning':reasoning,'verification_method':method,'llm_provider':llm.get('provider','fallback'),'llm_status':llm.get('llm_status','FALLBACK'),
            'article_url':article_url,'article_fetch_status':page.get('status'),'article_title':page.get('title',''),'article_image_url':page.get('image_url',''),
            'evidence':evidence,'trusted_evidence':trusted,'live_evidence':live,'image':image,'image_verification':image,
            'evidence_strength':('STRONG' if (support_n>=2 or contra_n>=1) else 'MODERATE' if (support_n>=1 or len(live)>=2) else 'WEAK'),
            'decision_summary':{'verdict':verdict,'confidence':confidence,'trusted_total':len(trusted),'trusted_supporting':support_n,'trusted_contradicting':contra_n,'trusted_neutral':neutral_n,'related_total':len(evidence),'basis':basis}}
