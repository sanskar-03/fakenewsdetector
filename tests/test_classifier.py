from backend.utils.preprocess import clean_text, extract_claim
from backend.utils.scoring import reputation, aggregate

def test_clean_and_claim():
    assert 'http' not in clean_text('Hello https://example.com world')
    assert extract_claim('Headline: A verified event happened in Chennai today.')

def test_reputation_and_fallback():
    assert reputation('https://www.reuters.com/story') > .9
    verdict, conf = aggregate(.9, [])
    assert verdict in {'FAKE','UNVERIFIED','REAL'} and 0 <= conf <= 1
