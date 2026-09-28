import re, html
from urllib.parse import urlparse


def clean_text(text: str) -> str:
    text=html.unescape(str(text or ''))
    text=re.sub(r'https?://\S+',' ',text)
    text=re.sub(r'<script\b[^>]*>.*?</script>',' ',text,flags=re.I|re.S)
    text=re.sub(r'<style\b[^>]*>.*?</style>',' ',text,flags=re.I|re.S)
    text=re.sub(r'<[^>]+>',' ',text)
    text=re.sub(r'\s+',' ',text).strip()
    return text


def extract_claim(article: str) -> str:
    raw=str(article or '').replace('\r','')
    lines=[clean_text(x) for x in raw.split('\n') if clean_text(x)]
    metadata=re.compile(r'^(published|publication|date|by|author|source|url|entry|दिनांक|लेखक|स्रोत|प्रकाशित|தேதி|ஆசிரியர்|సమయం|తేదీ|লেখক|তারিখ)\b',re.I)
    candidates=[]
    for line in lines[:20]:
        if metadata.search(line) or re.match(r'^https?://',line,re.I): continue
        if 20<=len(line)<=600: candidates.append(line)
    if candidates:
        # Prefer headline-like first line, but avoid generic site labels.
        bad_prefix=('latest news','breaking news','home','news','entertainment','fact check','वायरल न्यूज़','समाचार')
        for c in candidates[:8]:
            if c.lower() not in bad_prefix: return c[:600]
        return candidates[0][:600]
    sentences=re.split(r'(?<=[.!?।॥])\s+',' '.join(lines))
    return next((s.strip() for s in sentences if 20<=len(s.strip())<=600),' '.join(lines)[:600])


def extract_title_and_body(html_text: str):
    """Best-effort article extraction without making the URL mandatory."""
    try:
        from bs4 import BeautifulSoup
        soup=BeautifulSoup(html_text,'html.parser')
        for tag in soup(['script','style','noscript','svg','nav','footer','header','form']): tag.decompose()
        title=(soup.find('meta',attrs={'property':'og:title'}) or {}).get('content') if soup.find('meta',attrs={'property':'og:title'}) else None
        if not title and soup.title: title=soup.title.get_text(' ',strip=True)
        blocks=[]
        for node in soup.select('article p, main p, [itemprop="articleBody"] p, p'):
            t=node.get_text(' ',strip=True)
            if len(t)>=30: blocks.append(t)
        body=' '.join(blocks)
        return clean_text(title or ''), clean_text(body[:30000])
    except Exception:
        text=clean_text(html_text)
        return text[:300], text[:30000]
