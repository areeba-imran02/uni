import os
os.environ["DATABASE_URL"]="sqlite:///./test_universe.db"
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def account():
    import uuid
    r=client.post('/api/auth/register',json={"name":"Test User","email":f"{uuid.uuid4().hex}@example.com","password":"safe-password-123"}); assert r.status_code==200; return {"Authorization":"Bearer "+r.json()["access_token"]}
def test_health(): assert client.get('/health').json()['status']=='ok'
def test_create_and_run_project():
    h=account(); r=client.post('/api/projects',headers=h,json={"title":"Ohm law practice","discipline":"Engineering","degree":"Electrical Engineering","semester":"2","task_type":"Engineering calculation","description":"Calculate voltage for current 2 A and resistance 6 ohm","success_criteria":"Show equation"}); assert r.status_code==200; pid=r.json()['id']
    run=client.post(f'/api/projects/{pid}/run',headers=h); assert run.status_code==200; assert run.json()['status']=='completed'; assert len(run.json()['agents'])>=3
def test_project_ownership():
    h1=account(); h2=account(); r=client.post('/api/projects',headers=h1,json={"title":"Private project","discipline":"Computer Science","task_type":"Build a project","description":"Create a simple parser with validation"}); pid=r.json()['id']; assert client.get(f'/api/projects/{pid}',headers=h2).status_code==404
