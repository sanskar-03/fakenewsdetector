from backend.services.agent import _decision

def row(rel, relevance=.6, weight=.5, domain='a', tier='fact_check'):
    return {"relation":rel,"relevance":relevance,"weight":weight,"source_domain":domain,"tier":tier}

def test_unrelated_neutral_does_not_make_fake():
    v,*_= _decision([row("NEUTRAL",.3,.2,"a"),row("NEUTRAL",.3,.2,"b")])
    assert v=="UNVERIFIED"

def test_strong_factcheck_contradiction_can_flag_fake():
    v,*_= _decision([row("CONTRADICTS",.8,.8,"a")])
    assert v=="FAKE"

def test_conflicting_high_trust_is_unverified():
    v,*_= _decision([row("SUPPORTS",.8,.8,"a"),row("CONTRADICTS",.8,.8,"b")])
    assert v=="UNVERIFIED"
