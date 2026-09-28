from fastapi.testclient import TestClient
from backend.app import app

def test_health():
    c=TestClient(app); r=c.get('/api/v1/health'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_validation():
    c=TestClient(app); r=c.post('/api/v1/verify',json={'article':'too short'}); assert r.status_code==422
