from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from difflib import SequenceMatcher
import re
import os
import requests

from backend.rag.ingest import query_trusted_sources
from backend.utils.scoring import reputation

# Source tier is deliberately separate from verdict authority.
# primary/fact_check -> can participate in verdict gate
# reputable_news -> corroborating context only
# general -> context only
TRUSTED_SOURCE_REGISTRY = {
    "pib.gov.in": ("PIB / Government of India", 1.00, "primary"),
    "factcheck.pib.gov.in": ("PIB Fact Check", 1.00, "fact_check"),
    "pmindia.gov.in": ("Prime Minister's Office", 1.00, "primary"),
    "eci.gov.in": ("Election Commission of India", 1.00, "primary"),
    "sci.gov.in": ("Supreme Court of India", 1.00, "primary"),
    "who.int": ("World Health Organization", 1.00, "primary"),
    "nasa.gov": ("NASA", 1.00, "primary"),
    "un.org": ("United Nations", 0.98, "primary"),
    "boomlive.in": ("BOOM", 0.96, "fact_check"),
    "altnews.in": ("Alt News", 0.96, "fact_check"),
    "vishvasnews.com": ("Vishvas News", 0.96, "fact_check"),
    "factly.in": ("Factly", 0.95, "fact_check"),
    "newschecker.in": ("Newschecker", 0.95, "fact_check"),
    "fullfact.org": ("Full Fact", 0.95, "fact_check"),
    "factcheck.org": ("FactCheck.org", 0.95, "fact_check"),
    "snopes.com": ("Snopes", 0.94, "fact_check"),
    "politifact.com": ("PolitiFact", 0.94, "fact_check"),
    "leadstories.com": ("Lead Stories", 0.93, "fact_check"),
    "afp.com": ("AFP", 0.93, "fact_check"),
    "reuters.com": ("Reuters", 0.94, "reputable_news"),
    "apnews.com": ("Associated Press", 0.94, "reputable_news"),
    "bbc.com": ("BBC", 0.90, "reputable_news"),
    "thehindu.com": ("The Hindu", 0.88, "reputable_news"),
    "indianexpress.com": ("The Indian Express", 0.88, "reputable_news"),
    "ndtv.com": ("NDTV", 0.84, "reputable_news"),
    "timesofindia.indiatimes.com": ("Times of India", 0.82, "reputable_news"),
    "indiatoday.in": ("India Today", 0.82, "reputable_news"),
    "hindustantimes.com": ("Hindustan Times", 0.84, "reputable_news"),
    "livehindustan.com": ("Live Hindustan", 0.78, "reputable_news"),
    "news18.com": ("News18", 0.78, "reputable_news"),
    "thequint.com": ("The Quint", 0.80, "reputable_news"),
}

TRUSTED_SEARCH_DOMAINS = [
    "factcheck.pib.gov.in", "pib.gov.in", "boomlive.in", "altnews.in",
    "vishvasnews.com", "factly.in", "newschecker.in", "afp.com",
    "reuters.com", "apnews.com", "bbc.com", "thehindu.com",
    "indianexpress.com", "fullfact.org", "factcheck.org", "snopes.com",
    "timesofindia.indiatimes.com", "indiatoday.in", "hindustantimes.com",
    "livehindustan.com", "news18.com", "thequint.com",
]

# Only phrases that normally express the source's verdict. Generic words such as
# "not", "false" or "said" are intentionally NOT enough by themselves.
_FALSE_PHRASES = [
    r"\bis false\b", r"\bwas false\b", r"\bare false\b", r"\bwere false\b",
    r"\bfalse claim\b", r"\bfalse news\b", r"\bfake news\b", r"\bhoax\b",
    r"\bdebunked\b", r"\bdebunk(ed|s|ing)?\b", r"\bnot true\b", r"\bnot authentic\b",
    r"\bfabricated\b", r"\bmisleading claim\b", r"\bno evidence (?:that|to show)\b",
    r"\bdid not happen\b", r"\bnever happened\b", r"\bdenied (?:that|the claim)\b",
    r"फर्जी दावा", r"झूठा दावा", r"दावा गलत", r"दावा भ्रामक", r"गलत दावा", r"नहीं हुआ",
    r"போலி கூற்று", r"தவறான கூற்று", r"கூற்று உண்மை அல்ல", r"நடக்கவில்லை",
    r"తప్పుడు दावा", r"తప్పుడు దావా", r"దావా తప్పు", r"జరగలేదు",
    r"ভুয়া দাবি", r"মিথ্যা দাবি", r"দাবিটি ভুল", r"ঘটেনি",
    r"ખોટો દાવો", r"દાવો ખોટો", r"બનાવટી દાવો",
    r"ತಪ್ಪು ದಾವೆ", r"ದಾವೆ ತಪ್ಪು", r"ನಡೆದಿಲ್ಲ",
    r"വ്യാജ അവകാശവാദം", r"അവകാശവാദം തെറ്റാണ്", r"നടന്നില്ല",
    r"ਝੂਠਾ ਦਾਅਵਾ", r"ਦਾਅਵਾ ਗਲਤ", r"ਨਹੀਂ ਹੋਇਆ",
]
_TRUE_PHRASES = [
    r"\bis true\b", r"\bwas true\b", r"\bconfirmed\b", r"\bverified\b",
    r"\bconfirmed by (?:evidence|officials|records)\b", r"\bevidence shows\b",
    r"\bcorrect claim\b", r"\bauthentic\b", r"\bthe event happened\b",
    r"सही दावा", r"दावा सही", r"सत्यापित", r"पुष्टि हुई", r"घटना हुई",
    r"உண்மை கூற்று", r"கூற்று உண்மை", r"சரிபார்க்கப்பட்டது", r"நிகழ்வு நடந்தது",
    r"నిజమైన దావా", r"దావా నిజం", r"ధృవీకరించబడింది", r"ఘటన జరిగింది",
    r"সত্য দাবি", r"দাবিটি সত্য", r"নিশ্চিত হয়েছে", r"ঘটনাটি ঘটেছে",
    r"સાચો દાવો", r"દાવો સાચો", r"પુષ્ટિ થઈ", r"ઘટના બની",
    r"ನಿಜವಾದ ದಾವೆ", r"ದಾವೆ ನಿಜ", r"ದೃಢೀಕರಿಸಲಾಗಿದೆ", r"ಘಟನೆ ನಡೆದಿದೆ",
    r"സത്യമായ അവകാശവാദം", r"അവകാശവാദം ശരിയാണ്", r"സ്ഥിരീകരിച്ചു", r"സംഭവിച്ചു",
    r"ਸੱਚਾ ਦਾਅਵਾ", r"ਦਾਅਵਾ ਸਹੀ", r"ਪੁਸ਼ਟੀ ਹੋਈ", r"ਘਟਨਾ ਹੋਈ",
]

_STOPWORDS = {
    "the","and","for","that","this","with","from","about","into","after","before","during",
    "what","when","where","which","will","would","could","should","has","have","been","are",
    "was","were","not","you","your","they","their","news","claim","video","viral","said",
    "article","report","reports","according","also","more","than","here","there","who","how",
    "एक","और","यह","इस","से","में","का","की","के","को","पर","है","था","थे","दावा","वीडियो",
    "செய்தி","இந்த","அந்த","ஒரு","கூற்று","வார்த்தை","వార్త","ఈ","ఆ","అని","దావా","খবর","এই","দাবি",
    "સમાચાર","આ","દાવો","ಮತ್ತು","ಈ","ಸುದ್ದಿ","ದಾವೆ","വാർത്ത","ഈ","അവകാശവാദം","ਅਤੇ","ਇਹ","ਦਾਅਵਾ",
}

def _tokens(s):
    return re.findall(
        r"[A-Za-z0-9]{2,}|[\u0900-\u097F]{2,}|[\u0B80-\u0BFF]{2,}|[\u0980-\u09FF]{2,}|"
        r"[\u0C00-\u0C7F]{2,}|[\u0A80-\u0AFF]{2,}|[\u0C80-\u0CFF]{2,}|[\u0D00-\u0D7F]{2,}|[\u0A00-\u0A7F]{2,}",
        str(s or "").lower())

def _terms(s):
    return [t for t in _tokens(s) if t not in _STOPWORDS and len(t) >= 2]

def _ngrams(tokens, n=2):
    return {" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)}

def relevance(q, text):
    a = set(_terms(q)); b = set(_terms(text))
    if not a or not b: return 0.0
    # Use the strongest 14 claim terms, rather than letting long prose dilute the match.
    aq = sorted(a, key=lambda x: (-len(x), x))[:14]
    overlap = len(set(aq) & b)
    coverage = overlap / max(1, len(aq))
    phrase_bonus = min(0.20, 0.10 * len(_ngrams(aq,2) & _ngrams(list(b),2)))
    return min(1.0, coverage + phrase_bonus)

def _match_score(q, text):
    qt = _terms(q); tt = _terms(text)
    if not qt or not tt: return 0.0
    qset = set(qt); tset = set(tt)
    top = sorted(qset, key=lambda x: (-len(x), x))[:14]
    overlap = len(set(top) & tset)
    coverage = overlap / max(1, len(top))
    # Character similarity is useful when a search snippet closely paraphrases a short claim.
    seq = SequenceMatcher(None, " ".join(qt[:18]), " ".join(tt[:30])).ratio()
    return min(1.0, 0.75 * coverage + 0.25 * seq)

def _domain(url):
    try: return (urlparse(str(url)).hostname or "").lower().strip(".")
    except Exception: return ""

def source_info(url):
    d = _domain(url)
    for domain, info in TRUSTED_SOURCE_REGISTRY.items():
        if d == domain or d.endswith("." + domain):
            name, score, tier = info
            return {"name":name,"score":score,"tier":tier,"trusted":tier in {"primary","fact_check"},"domain":domain}
    try: score = float(reputation(url))
    except Exception: score = 0.35
    return {"name":d or "Unknown source","score":max(0.0,min(1.0,score)),"tier":"general","trusted":False,"domain":d}

def _has_phrase(patterns, text):
    return sum(bool(re.search(p, text, re.I | re.U)) for p in patterns)

def relation(q, text, source_tier=None):
    text = str(text or "")
    score = _match_score(q, text)
    if score < 0.34:
        return "NEUTRAL"
    low = text.lower()
    false_hits = _has_phrase(_FALSE_PHRASES, low)
    true_hits = _has_phrase(_TRUE_PHRASES, low)
    # A source must first be about the same claim. This is the key regression fix:
    # unrelated fact-checks that merely contain words such as "false" remain neutral.
    if false_hits and false_hits >= true_hits and score >= 0.48:
        return "CONTRADICTS"
    if true_hits and true_hits > false_hits and score >= 0.42:
        return "SUPPORTS"
    # High lexical/phrase overlap is corroboration only. It never turns a loosely
    # related article into a contradiction.
    if score >= 0.62:
        return "SUPPORTS"
    return "NEUTRAL"

def _enrich(item, query):
    item=dict(item or {})
    url=item.get("url") or item.get("link") or item.get("href") or ""
    title=item.get("title") or item.get("name") or ""
    content=item.get("content") or item.get("body") or item.get("snippet") or ""
    info=source_info(url); text=f"{title} {content}"; rel=relation(query,text,info["tier"])
    item.update({"url":url,"title":title,"content":content,"source":info["domain"],"source_name":info["name"],
                 "trusted":info["trusted"],"tier":info["tier"],"credibility":info["score"],"source_domain":info["domain"],
                 "relation":rel,"relevance":round(_match_score(query,text),4),"weight":round(max(.05,_match_score(query,text))*info["score"],4),
                 "match_basis":"same-claim lexical/phrase match" if rel!="NEUTRAL" else "related text without sufficient same-claim stance"})
    return item

def _dedupe(rows):
    seen=set(); out=[]
    for row in rows:
        url=str(row.get("url") or "").split("#")[0].rstrip("/")
        key=url or (row.get("title"),row.get("source_domain"))
        if key in seen: continue
        seen.add(key); out.append(row)
    return out

def _search_domain(domain, query):
    try:
        from ddgs import DDGS
        rows=list(DDGS().text(f"site:{domain} {query[:260]}",max_results=4))
        return [_enrich(x,query) for x in rows]
    except Exception: return []

def _google_news(query, max_results=12):
    try:
        import feedparser
        url="https://news.google.com/rss/search?" + requests.compat.urlencode({"q":query[:220],"hl":"en-IN","gl":"IN","ceid":"IN:en"})
        feed=feedparser.parse(url)
        rows=[]
        for e in feed.entries[:max_results]:
            rows.append(_enrich({"title":e.get("title",""),"content":e.get("summary",""),"url":e.get("link","")},query))
        return rows
    except Exception: return []

def _claim_review_api(query):
    key=os.getenv("GOOGLE_FACTCHECK_API_KEY") or os.getenv("FACTCHECK_API_KEY")
    if not key: return []
    try:
        data=requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search",params={"query":query[:500],"pageSize":20,"key":key},timeout=10).json()
        rows=[]
        for claim in data.get("claims",[]):
            for review in claim.get("claimReview",[]):
                publisher=review.get("publisher") or {}; page=review.get("url") or ""; rating=str(review.get("textualRating") or "")
                rows.append(_enrich({"title":review.get("title") or claim.get("text") or "Claim review","content":f"{claim.get('text','')} {rating}","url":page},query))
        return rows
    except Exception: return []

def trusted_search(q):
    rows=[]
    try: rows.extend(_enrich(e,q) for e in (query_trusted_sources(q) or []))
    except Exception: pass
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures=[pool.submit(_search_domain,d,q) for d in TRUSTED_SEARCH_DOMAINS]
        for f in as_completed(futures):
            try: rows.extend(f.result())
            except Exception: pass
    rows.extend(_claim_review_api(q))
    rows=[x for x in _dedupe(rows) if x.get("relevance",0)>=0.34]
    # Domain diversity is mandatory. Repeated syndicated copies must not look like consensus.
    rows.sort(key=lambda x:(1 if x.get("trusted") else 0,x.get("relevance",0),x.get("credibility",0)),reverse=True)
    out=[]; counts={}
    for x in rows:
        d=x.get("source_domain") or x.get("source") or ""
        cap=2 if x.get("trusted") else 3
        if counts.get(d,0)>=cap: continue
        counts[d]=counts.get(d,0)+1; out.append(x)
        if len(out)>=60: break
    return out

def web_search(q,max_results=12):
    try:
        from ddgs import DDGS
        rows=list(DDGS().text(q[:300],max_results=max_results))
    except Exception: rows=[]
    if not rows: rows=_google_news(q,max_results)
    out=[_enrich(x,q) for x in rows]
    return sorted(_dedupe(out),key=lambda x:(x.get("relevance",0),x.get("credibility",0)),reverse=True)[:max_results]

def search_news(query,max_results=10): return web_search(query,max_results=max_results)
def search_official_sources(query,max_results=12): return [x for x in trusted_search(query) if x.get("tier") in {"primary","fact_check"}][:max_results]
