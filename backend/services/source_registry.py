SOURCE_REGISTRY = {'trusted_india': [{'name': 'PIB Fact Check', 'domain': 'factcheck.pib.gov.in', 'score': 0.98}, {'name': 'Alt News', 'domain': 'altnews.in', 'score': 0.92}, {'name': 'BOOM', 'domain': 'boomlive.in', 'score': 0.92}, {'name': 'The Quint WebQoof', 'domain': 'thequint.com', 'score': 0.89}, {'name': 'FACTLY', 'domain': 'factly.in', 'score': 0.89}, {'name': 'Newschecker', 'domain': 'newschecker.in', 'score': 0.88}], 'trusted_international': [{'name': 'Reuters Fact Check / Reuters', 'domain': 'reuters.com', 'score': 0.97}, {'name': 'Associated Press', 'domain': 'apnews.com', 'score': 0.96}, {'name': 'FactCheck.org', 'domain': 'factcheck.org', 'score': 0.96}, {'name': 'Full Fact', 'domain': 'fullfact.org', 'score': 0.95}, {'name': 'BBC Verify / BBC', 'domain': 'bbc.com', 'score': 0.94}, {'name': 'Lead Stories', 'domain': 'leadstories.com', 'score': 0.91}, {'name': 'Snopes', 'domain': 'snopes.com', 'score': 0.9}], 'reputable_india': [{'name': 'The Hindu', 'domain': 'thehindu.com', 'score': 0.86}, {'name': 'Hindustan Times', 'domain': 'hindustantimes.com', 'score': 0.84}, {'name': 'The Indian Express', 'domain': 'indianexpress.com', 'score': 0.86}, {'name': 'Times of India', 'domain': 'timesofindia.indiatimes.com', 'score': 0.8}, {'name': 'India Today', 'domain': 'indiatoday.in', 'score': 0.82}, {'name': 'News18', 'domain': 'news18.com', 'score': 0.78}, {'name': 'NDTV', 'domain': 'ndtv.com', 'score': 0.82}, {'name': 'Deccan Herald', 'domain': 'deccanherald.com', 'score': 0.84}, {'name': 'The New Indian Express', 'domain': 'newindianexpress.com', 'score': 0.82}, {'name': 'Hindustan', 'domain': 'livehindustan.com', 'score': 0.78}, {'name': 'Lalluram', 'domain': 'lalluram.com', 'score': 0.72}, {'name': 'LiveLaw', 'domain': 'livelaw.in', 'score': 0.78}, {'name': 'News24', 'domain': 'news24online.com', 'score': 0.72}, {'name': 'NewsBytes', 'domain': 'newsbytesapp.com', 'score': 0.68}], 'reputable_international': [{'name': 'The Guardian', 'domain': 'theguardian.com', 'score': 0.84}, {'name': 'The New York Times', 'domain': 'nytimes.com', 'score': 0.86}, {'name': 'The Washington Post', 'domain': 'washingtonpost.com', 'score': 0.84}, {'name': 'Al Jazeera', 'domain': 'aljazeera.com', 'score': 0.8}, {'name': 'CNN', 'domain': 'cnn.com', 'score': 0.8}, {'name': 'The Wall Street Journal', 'domain': 'wsj.com', 'score': 0.84}, {'name': 'The Telegraph', 'domain': 'telegraph.co.uk', 'score': 0.78}], 'primary_official': ['pib.gov.in', 'pmindia.gov.in', 'pm.gov.in', 'pmo.gov.in', 'presidentofindia.nic.in', 'parliamentofindia.nic.in', 'sansad.in', 'sci.gov.in', 'supremecourt.gov.in', 'eci.gov.in', 'rbi.org.in', 'sebi.gov.in', 'isro.gov.in', 'drdo.gov.in', 'uidai.gov.in', 'niti.gov.in', 'mea.gov.in', 'mha.gov.in', 'moes.gov.in', 'mohfw.gov.in', 'education.gov.in', 'morth.nic.in', 'grse.in', 'aiims.edu', 'aiims.edu.in', 'aiimsrishikesh.edu.in', 'who.int', 'un.org', 'unicef.org', 'unesco.org', 'worldbank.org', 'imf.org'], 'low_credibility': ['facebook.com', 'instagram.com', 'youtube.com', 'm.youtube.com', 'tiktok.com', 'x.com', 'twitter.com', 'telegram.me', 't.me']}

def source_info(url):
    from urllib.parse import urlparse
    host = (urlparse(str(url or '')).hostname or '').lower().strip('.')
    if not host:
        return {'category': 'UNVERIFIED', 'quality': 'LOW', 'score': 0.20, 'name': ''}
    if host.endswith('.gov.in') or host.endswith('.nic.in') or any(host == d or host.endswith('.' + d) for d in SOURCE_REGISTRY['primary_official']):
        return {'category': 'PRIMARY OFFICIAL', 'quality': 'HIGH', 'score': 0.97, 'name': host}
    for group in ('trusted_india', 'trusted_international'):
        for item in SOURCE_REGISTRY[group]:
            if host == item['domain'] or host.endswith('.' + item['domain']):
                return {'category': 'TRUSTED / FACT-CHECK', 'quality': 'HIGH', 'score': float(item['score']), 'name': item['name']}
    for group in ('reputable_india', 'reputable_international'):
        for item in SOURCE_REGISTRY[group]:
            if host == item['domain'] or host.endswith('.' + item['domain']):
                return {'category': 'REPUTABLE NEWS', 'quality': 'MEDIUM-HIGH', 'score': float(item['score']), 'name': item['name']}
    if any(host == d or host.endswith('.' + d) for d in SOURCE_REGISTRY['low_credibility']):
        return {'category': 'UNVERIFIED', 'quality': 'LOW', 'score': 0.20, 'name': ''}
    return {'category': 'GENERAL', 'quality': 'MEDIUM', 'score': 0.50, 'name': ''}
# ---------------------------------------------------------------------------
# Backward-compatible exports
# ---------------------------------------------------------------------------
TRUSTED_SOURCES = SOURCE_REGISTRY
REPUTABLE_SOURCES = {
    "india": SOURCE_REGISTRY.get("reputable_india", []),
    "international": SOURCE_REGISTRY.get("reputable_international", []),
}
LOW_CREDIBILITY_DOMAINS = set(
    SOURCE_REGISTRY.get("low_credibility", [])
)
