import hashlib, re
from backend.rag.vector_store import collection
TRUSTED_FEEDS={'FactCheck.org':'https://www.factcheck.org/feed/','Lead Stories':'https://leadstories.com/atom.xml','Full Fact':'https://fullfact.org/feed/all/','TruthOrFiction':'https://www.truthorfiction.com/feed/'}
def ingest_document(title,content,url,source):
    c=collection()
    if c is None:return None
    i=hashlib.sha256(url.encode()).hexdigest()[:24]; c.upsert(ids=[i],documents=[content[:50000]],metadatas=[{'title':title,'url':url,'source':source}]); return i
def ingest_all_feeds(limit=20):
    import feedparser
    out=[]
    for name,url in TRUSTED_FEEDS.items():
        try:
            f=feedparser.parse(url); n=0
            for e in f.entries[:limit]:
                if e.get('link'): ingest_document(e.get('title',''),f"{e.get('title','')}\n\n{e.get('summary','')}",e['link'],name); n+=1
            out.append({'feed':name,'ingested':n})
        except Exception as exc: out.append({'feed':name,'error':str(exc)})
    return out
def query_trusted_sources(query,n_results=8):
    c=collection()
    if c is None:return []
    try:
        r=c.query(query_texts=[query],n_results=min(n_results,20)); docs=r.get('documents',[[]])[0]; metas=r.get('metadatas',[[]])[0]; ds=r.get('distances',[[]])[0]
        return [{'title':m.get('title',''),'content':d,'url':m.get('url',''),'source':m.get('source',''),'similarity':round(1/(1+float(dist)),4)} for d,m,dist in zip(docs,metas,ds)]
    except Exception:return []
