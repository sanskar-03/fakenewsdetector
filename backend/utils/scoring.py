from urllib.parse import urlparse
TRUSTED={'reuters.com':.96,'apnews.com':.96,'bbc.com':.94,'theguardian.com':.90,'factcheck.org':.95,'fullfact.org':.95,'leadstories.com':.92,'snopes.com':.93,'pib.gov.in':.99,'gov.in':.98,'nic.in':.98,'pmindia.gov.in':.99,'who.int':.98,'un.org':.98}
def domain(url): return urlparse(url).netloc.lower().removeprefix('www.') if url else ''
def reputation(url):
    d=domain(url)
    if not d:return .30
    if d in TRUSTED:return TRUSTED[d]
    for k,v in TRUSTED.items():
        if d.endswith('.'+k):return v
    if d.endswith('.gov.in') or d.endswith('.nic.in'): return .97
    return .40

def aggregate(class_prob_fake, evidence, llm_verdict=None):
    # Conservative evidence-first fallback; no LLM means no fabricated reasoning.
    support=sum((e.get('relation')=='SUPPORTS')*e.get('weight',0) for e in evidence)
    contradict=sum((e.get('relation')=='CONTRADICTS')*e.get('weight',0) for e in evidence)
    total=support+contradict
    ev_fake=contradict/total if total else .5
    score=.45*class_prob_fake+.55*ev_fake if total else class_prob_fake
    if llm_verdict in {'REAL','FAKE','UNVERIFIED'}:
        return llm_verdict, round(max(.05,min(.99,.55+abs(score-.5)*.8)),3)
    if total<.8 or abs(score-.5)<.12:return 'UNVERIFIED',round(.50+abs(score-.5)*.35,3)
    return ('FAKE' if score>.5 else 'REAL'),round(.55+abs(score-.5)*.8,3)
