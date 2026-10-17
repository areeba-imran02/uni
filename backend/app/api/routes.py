from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from pathlib import Path
from app.core.database import get_db
from app.models.models import User, Project, WorkflowRun, AgentExecution
from app.schemas.schemas import RegisterIn, LoginIn, ProjectIn
from app.security.auth import hash_password, verify_password, create_token, current_user
from app.agents.engine import execute_workflow
router=APIRouter(prefix="/api")
@router.post('/auth/register')
def register(body:RegisterIn,db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==body.email.lower())): raise HTTPException(409,"Email already registered")
    u=User(name=body.name.strip(),email=body.email.lower(),password_hash=hash_password(body.password)); db.add(u); db.commit(); db.refresh(u)
    return {"access_token":create_token(u.id),"token_type":"bearer","user":{"id":u.id,"name":u.name,"email":u.email}}
@router.post('/auth/login')
def login(body:LoginIn,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==body.email.lower()))
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":create_token(u.id),"token_type":"bearer","user":{"id":u.id,"name":u.name,"email":u.email}}
@router.get('/auth/me')
def me(u:User=Depends(current_user)): return {"id":u.id,"name":u.name,"email":u.email}
def own_project(pid:int,u:User,db:Session):
    p=db.scalar(select(Project).where(Project.id==pid,Project.owner_id==u.id))
    if not p: raise HTTPException(404,"Project not found")
    return p
@router.get('/projects')
def projects(u:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":p.id,"title":p.title,"discipline":p.discipline,"degree":p.degree,"semester":p.semester,"task_type":p.task_type,"description":p.description,"success_criteria":p.success_criteria,"status":p.status,"created_at":p.created_at.isoformat()} for p in db.scalars(select(Project).where(Project.owner_id==u.id).order_by(Project.updated_at.desc())).all()]
@router.post('/projects')
def create_project(body:ProjectIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=Project(owner_id=u.id,**body.model_dump(),status="draft"); db.add(p); db.commit(); db.refresh(p); return {"id":p.id,"title":p.title,"status":p.status}
@router.get('/projects/{pid}')
def get_project(pid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=own_project(pid,u,db); return {"id":p.id,"title":p.title,"discipline":p.discipline,"degree":p.degree,"semester":p.semester,"task_type":p.task_type,"description":p.description,"success_criteria":p.success_criteria,"status":p.status,"runs":[{"id":r.id,"status":r.status,"result":r.result,"error":r.error,"started_at":r.started_at.isoformat()} for r in p.runs]}
@router.patch('/projects/{pid}')
def update_project(pid:int,body:ProjectIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=own_project(pid,u,db); [setattr(p,k,v) for k,v in body.model_dump().items()]; p.updated_at=datetime.now(timezone.utc); db.commit(); return {"id":p.id,"status":p.status,"message":"Project updated"}
@router.delete('/projects/{pid}')
def delete_project(pid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=own_project(pid,u,db); db.delete(p); db.commit(); return {"deleted":True}
@router.post('/projects/{pid}/run')
def run_project(pid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=own_project(pid,u,db); run=WorkflowRun(project_id=p.id,status="running",result={}); db.add(run); p.status="running"; db.commit(); db.refresh(run)
    try:
        output=execute_workflow(p); run.status=output["status"]; run.result=output; run.finished_at=datetime.now(timezone.utc); p.status=run.status
        for a in output["agents"]: db.add(AgentExecution(run_id=run.id,agent_name=a["agent_name"],status=a["status"],summary=a["summary"],output=a["output"],duration_ms=a["duration_ms"]))
        db.commit(); return {"run_id":run.id,**output}
    except Exception as e:
        run.status="failed"; run.error="Workflow failed. Review inputs and retry."; run.finished_at=datetime.now(timezone.utc); p.status="failed"; db.commit(); raise HTTPException(500,run.error) from e
@router.get('/runs/{rid}')
def get_run(rid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(WorkflowRun,rid)
    if not r or not db.scalar(select(Project).where(Project.id==r.project_id,Project.owner_id==u.id)): raise HTTPException(404,"Run not found")
    return {"id":r.id,"status":r.status,"result":r.result,"error":r.error,"agents":[{"agent_name":a.agent_name,"status":a.status,"summary":a.summary,"output":a.output,"duration_ms":a.duration_ms} for a in db.scalars(select(AgentExecution).where(AgentExecution.run_id==rid)).all()]}
@router.post('/uploads')
async def upload(file:UploadFile=File(...),u:User=Depends(current_user)):
    allowed={'.pdf','.txt','.csv','.json','.py','.md','.xlsx'}; suffix=Path(file.filename or '').suffix.lower()
    if suffix not in allowed: raise HTTPException(415,"File type not supported")
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,"Maximum file size is 5 MB")
    # Safe MVP: upload is acknowledged, never executed. Persistence can be added with private object storage.
    return {"filename":Path(file.filename).name,"size":len(data),"status":"received_for_this_request","note":"File contents are not persisted in this MVP; code uploads are never executed."}
