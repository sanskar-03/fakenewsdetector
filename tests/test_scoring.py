from backend.utils.scoring import aggregate

def test_contradictory_evidence_can_flag_fake():
    ev=[{"relation":"CONTRADICTS","weight":1.0},{"relation":"CONTRADICTS","weight":0.8}]
    verdict,conf=aggregate(.8,ev)
    assert verdict=="FAKE" and conf>.5
