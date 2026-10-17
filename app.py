"""UniVerse AI — Streamlit Community Cloud entry point.
The deterministic workflows reuse the project's existing agent engine and SQLAlchemy models.
"""
from __future__ import annotations
import os, sys, json, hashlib, hmac, secrets
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Streamlit Community Cloud secrets are exposed through st.secrets; map supported settings
# before importing the database module (which creates its engine at import time).
for key in ("DATABASE_URL", "SECRET_KEY", "GEMINI_API_KEY", "DEMO_MODE"):
    try:
        value = st.secrets.get(key)
        if value:
            os.environ[key] = str(value)
    except Exception:
        pass

from sqlalchemy import select
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models.models import User, Project, WorkflowRun, AgentExecution
from app.agents.engine import execute_workflow
from app.ml.router import classify_task

st.set_page_config(page_title="UniVerse AI", page_icon="🌌", layout="wide", initial_sidebar_state="expanded")
Base.metadata.create_all(bind=engine)

st.markdown(r"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--ink:#e9ecf7;--muted:#a6b1c8;--line:#28334e;--panel:#11192b;--violet:#9c87ff;--teal:#56ddc3}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse at 80% 0%,#3b2c6b40,transparent 34%),radial-gradient(ellipse at 15% 20%,#1e657033,transparent 30%),#0b1020;color:var(--ink)}
[data-testid="stHeader"]{background:transparent} [data-testid="stSidebar"]{background:#0a0f1d;border-right:1px solid #202a40}
[data-testid="stSidebar"] *{color:#e9ecf7}
.block-container{padding-top:1.6rem;max-width:1450px}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.6px}
h1{font-size:2.35rem!important;font-weight:800!important} h2{font-weight:750!important}
.hero{padding:1.6rem 1.8rem;border:1px solid #474078;border-radius:20px;background:radial-gradient(ellipse at 80% 20%,#7353bf42,transparent 45%),linear-gradient(115deg,#17172e,#141b32 65%,#15303a);margin:.3rem 0 1.25rem}
.eyebrow{color:#b6a7ff;text-transform:uppercase;font-size:.72rem;font-weight:800;letter-spacing:1.7px}
.hero h1{font-size:2.7rem!important;line-height:1.12;margin:.55rem 0}.gradient{background:linear-gradient(100deg,#b49aff,#62e0cd);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:#bac5db;font-size:1rem;max-width:650px;line-height:1.7}
.panel{background:linear-gradient(145deg,#141d31,#101728);border:1px solid #2a3550;border-radius:15px;padding:1.1rem 1.2rem;height:100%}
.metric{background:#121b2e;border:1px solid #2b3650;border-radius:14px;padding:1rem 1.1rem}.metric .label{font-size:.8rem;color:#aab6ce}.metric .value{font:800 1.8rem Manrope,sans-serif;margin:.2rem 0}.metric .hint{font-size:.75rem;color:#8291ad}
div.stButton>button,div.stFormSubmitButton>button{border-radius:10px;border:1px solid #574b9b;background:linear-gradient(110deg,#7958e9,#5e72e9);color:white;font-weight:700;min-height:2.6rem}div.stButton>button:hover,div.stFormSubmitButton>button:hover{border-color:#9d8bff;color:white;filter:brightness(1.1)}
.stTextInput input,.stTextArea textarea,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div{background:#0e1525;color:#f0f2ff;border-color:#303b56;border-radius:9px}
[data-testid="stMetric"]{background:#121b2e;border:1px solid #2b3650;padding:1rem;border-radius:13px}
[data-testid="stExpander"]{border:1px solid #2b3650;border-radius:12px;background:#11192b}
div[data-testid="stAlert"]{border-radius:12px} .small-muted{color:#a6b1c8;font-size:.88rem}
hr{border-color:#28334e}.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{background:#121b2e;border-radius:8px;padding:.55rem 1rem}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

DISCIPLINES = {
    "Computer Science & IT": ["Build a project", "Debug / plan code", "Analyze requirements"],
    "Engineering": ["Engineering calculation", "Circuit / Ohm's law", "Unit conversion"],
    "Medical Education": ["Fictional case simulation", "Clinical reasoning practice", "Evidence review"],
    "Business & Economics": ["Analyze a business problem", "Research a topic", "Analyze a dataset"],
    "Agriculture & Environment": ["Agricultural analysis", "Research a topic", "Analyze a dataset"],
    "Natural Sciences": ["Scientific calculation", "Analyze a dataset", "Research a topic"],
    "Law & Social Sciences": ["Educational document analysis", "Structured research", "Analyze a case"],
}

# Database/session helpers
def db_session(): return SessionLocal()
def utcnow(): return datetime.now(timezone.utc)
def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 240_000)
    return 'pbkdf2_sha256$240000$' + salt.hex() + '$' + digest.hex()
def password_verify(password: str, stored: str) -> bool:
    try:
        if stored.startswith('pbkdf2_sha256$'):
            _, rounds, salt_hex, digest_hex = stored.split('$', 3)
            candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
            return hmac.compare_digest(candidate, digest_hex)
        # Compatibility with accounts created by the existing FastAPI API.
        from app.security.auth import verify_password
        return verify_password(password, stored)
    except Exception:
        return False

def authenticate(email, password):
    with db_session() as db:
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user and password_verify(password, user.password_hash):
            return {"id": user.id, "name": user.name, "email": user.email}
    return None

def register_user(name, email, password):
    with db_session() as db:
        normalized = email.strip().lower()
        if db.scalar(select(User).where(User.email == normalized)):
            return None, "An account with this email already exists."
        user = User(name=name.strip(), email=normalized, password_hash=password_hash(password))
        db.add(user); db.commit(); db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email}, None

def list_projects(user_id):
    with db_session() as db:
        rows = db.scalars(select(Project).where(Project.owner_id == user_id).order_by(Project.updated_at.desc())).all()
        return [{"id":p.id,"title":p.title,"discipline":p.discipline,"degree":p.degree,"semester":p.semester,"task_type":p.task_type,"description":p.description,"success_criteria":p.success_criteria,"status":p.status,"created_at":p.created_at.isoformat()} for p in rows]

def get_project(user_id, project_id):
    with db_session() as db:
        p = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
        if not p: return None
        runs=[]
        for r in sorted(p.runs, key=lambda x:x.started_at or utcnow(), reverse=True):
            agents=[{"agent_name":a.agent_name,"status":a.status,"summary":a.summary,"output":a.output,"duration_ms":a.duration_ms} for a in db.scalars(select(AgentExecution).where(AgentExecution.run_id==r.id)).all()]
            runs.append({"id":r.id,"status":r.status,"result":r.result,"error":r.error,"started_at":r.started_at.isoformat() if r.started_at else "","agents":agents})
        return {"id":p.id,"title":p.title,"discipline":p.discipline,"degree":p.degree,"semester":p.semester,"task_type":p.task_type,"description":p.description,"success_criteria":p.success_criteria,"status":p.status,"runs":runs}

def create_project(user_id, data):
    with db_session() as db:
        p=Project(owner_id=user_id, **data, status="draft")
        db.add(p); db.commit(); db.refresh(p); return p.id

def remove_project(user_id, project_id):
    with db_session() as db:
        p=db.scalar(select(Project).where(Project.id==project_id,Project.owner_id==user_id))
        if not p: return False
        db.delete(p); db.commit(); return True

def run_project(user_id, project_id):
    with db_session() as db:
        p=db.scalar(select(Project).where(Project.id==project_id,Project.owner_id==user_id))
        if not p: return None
        run=WorkflowRun(project_id=p.id,status="running",result={}); p.status="running"; db.add(run); db.commit(); db.refresh(run)
        try:
            output=execute_workflow(p)
            run.status=output.get('status','completed'); run.result=output; run.finished_at=utcnow(); p.status=run.status
            for a in output.get('agents',[]):
                db.add(AgentExecution(run_id=run.id,agent_name=a['agent_name'],status=a['status'],summary=a.get('summary',''),output=a.get('output',{}),duration_ms=a.get('duration_ms',0)))
            db.commit(); return {"run_id":run.id,**output}
        except Exception as exc:
            run.status='failed'; run.error='Workflow failed. Check the inputs and retry.'; run.finished_at=utcnow(); p.status='failed'; db.commit()
            return {"status":"failed","error":str(exc),"run_id":run.id}

def status_pill(status):
    colors={"completed":"#56ddc3","draft":"#b6a7ff","running":"#ffc56b","failed":"#ff899b"}
    color=colors.get((status or '').lower(),'#a6b1c8')
    st.markdown(f'<span style="display:inline-block;border:1px solid {color}66;background:{color}15;color:{color};padding:4px 9px;border-radius:7px;font-size:.72rem;font-weight:800">{(status or "unknown").upper()}</span>',unsafe_allow_html=True)

def show_auth():
    left,right=st.columns([1.15,1],gap="large")
    with left:
        st.markdown('<div class="hero" style="margin-top:3rem;padding:2rem"><div class="eyebrow">✦ ONE INTELLIGENCE · EVERY DISCIPLINE</div><h1>Your Degree Is<br><span class="gradient">Just the Beginning.</span></h1><p>Turn academic knowledge into practical outcomes with structured workflows, specialist steps, deterministic tools, and transparent verification.</p><p>✦ Project history &nbsp; · &nbsp; ✦ Agent execution trace &nbsp; · &nbsp; ✦ Discipline labs</p></div>',unsafe_allow_html=True)
        st.markdown("### Built for curious minds")
        st.write("Computer Science · Engineering · Medical Education · Business · Agriculture · Natural Sciences")
    with right:
        st.markdown("<div style='height:2rem'></div>",unsafe_allow_html=True)
        st.markdown("## Welcome to UniVerse AI")
        st.caption("Sign in to your workspace or create a new account.")
        mode=st.radio("Account",["Sign in","Create account"],horizontal=True,label_visibility="collapsed")
        with st.form("auth_form",clear_on_submit=False):
            name=st.text_input("Full name",placeholder="Your name") if mode=="Create account" else None
            email=st.text_input("Email",placeholder="you@example.com")
            password=st.text_input("Password",type="password",placeholder="At least 8 characters")
            if mode=="Create account": confirm=st.text_input("Confirm password",type="password")
            submit=st.form_submit_button("Create account" if mode=="Create account" else "Sign in",use_container_width=True)
        if submit:
            if not email.strip() or '@' not in email: st.error("Enter a valid email address.")
            elif mode=="Create account":
                if not name or len(name.strip())<2: st.error("Name must contain at least 2 characters.")
                elif len(password)<8: st.error("Use a password with at least 8 characters.")
                elif password!=confirm: st.error("Passwords do not match.")
                else:
                    user,error=register_user(name,email,password)
                    if error: st.error(error)
                    else: st.session_state.user=user; st.rerun()
            else:
                user=authenticate(email,password)
                if user: st.session_state.user=user; st.rerun()
                else: st.error("Incorrect email or password.")
        st.info("For a public deployment, configure a managed PostgreSQL database in Streamlit Secrets. Local SQLite is suitable for development, but hosted local files may not persist across restarts.")

if "user" not in st.session_state: st.session_state.user=None
if "page" not in st.session_state: st.session_state.page="Overview"
if "selected_project" not in st.session_state: st.session_state.selected_project=None
if "last_run" not in st.session_state: st.session_state.last_run=None

if not st.session_state.user:
    show_auth()
    st.stop()

user=st.session_state.user
with st.sidebar:
    st.markdown("<div style='display:flex;gap:10px;align-items:center;padding:.4rem 0 1.2rem'><div style='width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(135deg,#8b5cf6,#4d7cff);font-size:1.3rem'>✦</div><div><b style='font-size:1.1rem'>UniVerse <span style='color:#a997ff'>AI</span></b><div style='font-size:.72rem;color:#8f9db8'>Academic execution workspace</div></div></div>",unsafe_allow_html=True)
    st.caption("WORKSPACE")
    pages=[("◈","Overview"),("＋","New Project"),("▤","My Projects"),("⌘","Agent Workspace"),("◉","Discipline Labs"),("✧","Skills & Evidence"),("⚙","Settings")]
    for icon,label in pages:
        if st.button(f"{icon}   {label}",key="nav_"+label,use_container_width=True,type="primary" if st.session_state.page==label else "secondary"):
            st.session_state.page=label; st.rerun()
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.caption(user['email'])
    if st.button("Sign out",use_container_width=True):
        st.session_state.user=None; st.session_state.selected_project=None; st.rerun()

projects=list_projects(user['id'])
page=st.session_state.page
st.markdown(f'<div class="eyebrow">UNIverse AI / WORKSPACE</div>',unsafe_allow_html=True)
if page=="Overview":
    st.title(f"Welcome back, {user['name'].split()[0]} ✦")
    st.markdown("Turn your next academic challenge into a structured, reviewable workflow.")
    st.markdown('<div class="hero"><div class="eyebrow">YOUR IDEAS, PUT TO WORK</div><h1>One Intelligence.<br><span class="gradient">Every Discipline.</span></h1><p>Create a project, choose a discipline, and let a bounded workflow plan the task, perform a supported tool action, and verify what it can.</p></div>',unsafe_allow_html=True)
    completed=sum(p['status']=='completed' for p in projects); running=sum(p['status']=='running' for p in projects); failed=sum(p['status']=='failed' for p in projects)
    cols=st.columns(4)
    for col,label,value,hint in zip(cols,["Total projects","Completed","In progress","Needs attention"],[len(projects),completed,running,failed],["Saved to your workspace","Recorded successful workflows","Currently running status","Failed workflows"]):
        with col: st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div><div class="hint">{hint}</div></div>',unsafe_allow_html=True)
    st.markdown("## Recent projects")
    if not projects:
        st.markdown('<div class="panel"><h3>Your workspace starts here.</h3><p class="small-muted">No projects yet. Create your first project to generate a plan, run a supported workflow, and inspect its verification report.</p></div>',unsafe_allow_html=True)
        if st.button("＋  Create your first project",key="first_project"): st.session_state.page="New Project"; st.rerun()
    else:
        for p in projects[:5]:
            with st.container(border=True):
                a,b,c=st.columns([4,1,1])
                with a:
                    st.markdown(f"**{p['title']}**")
                    st.caption(f"{p['discipline']} · {p['task_type']}")
                with b: status_pill(p['status'])
                with c:
                    if st.button("Open →",key=f"open_home_{p['id']}"): st.session_state.selected_project=p['id']; st.session_state.page="My Projects"; st.rerun()
elif page=="New Project":
    st.title("Create a new project")
    st.caption("Define the challenge and review the workflow before it runs. Uploaded files are validated but are not stored or executed.")
    with st.form("new_project_form"):
        title=st.text_input("Project title",placeholder="e.g. Smart irrigation analysis")
        discipline=st.selectbox("Discipline",list(DISCIPLINES.keys()))
        c1,c2=st.columns(2)
        with c1: degree=st.text_input("Degree / programme",placeholder="e.g. BS Computer Science")
        with c2: semester=st.selectbox("Semester",["Not specified"]+[f"Semester {i}" for i in range(1,13)])
        task_type=st.selectbox("Task type",DISCIPLINES[discipline])
        description=st.text_area("Describe your task",height=150,placeholder="What are you trying to achieve? Include requirements, data, constraints, and context.")
        criteria=st.text_area("Success criteria (optional)",height=80,placeholder="How will you judge whether the result is useful?")
        submitted=st.form_submit_button("Create project",use_container_width=True)
    uploaded=st.file_uploader("Optional supporting file (not persisted)",type=["pdf","txt","csv","json","py","md","xlsx"])
    if uploaded:
        if uploaded.size>5*1024*1024: st.error("Maximum upload size is 5 MB.")
        else: st.info(f"{uploaded.name} ({uploaded.size:,} bytes) is available for this session only. It will not be saved or executed by this MVP.")
    if submitted:
        if len(title.strip())<3: st.error("Project title must contain at least 3 characters.")
        elif len(description.strip())<8: st.error("Describe the task in at least 8 characters.")
        else:
            data={"title":title.strip(),"discipline":discipline,"degree":degree.strip(),"semester":"" if semester=="Not specified" else semester,"task_type":task_type,"description":description.strip(),"success_criteria":criteria.strip()}
            pid=create_project(user['id'],data); st.session_state.selected_project=pid; st.session_state.page="My Projects"; st.success("Project saved."); st.rerun()
    with st.expander("Workflow preview"):
        st.write("1. Classify task using a transparent keyword baseline. 2. Run the discipline-specific deterministic workflow. 3. Verify supported constraints. 4. Save agent outputs and final report.")
elif page=="My Projects":
    st.title("My Projects"); st.caption("Your saved project history, linked to your account.")
    if not projects:
        st.info("No projects yet. Use New Project to create one.")
    else:
        search=st.text_input("Search projects",placeholder="Search title, discipline, or task")
        filtered=[p for p in projects if search.lower() in (p['title']+' '+p['discipline']+' '+p['task_type']).lower()]
        choices={f"{p['title']} · {p['discipline']} · #{p['id']}":p['id'] for p in filtered}
        if choices:
            labels=list(choices); default_index=next((i for i,x in enumerate(labels) if choices[x]==st.session_state.selected_project),0)
            selected_label=st.selectbox("Choose a project",labels,index=default_index)
            pid=choices[selected_label]; st.session_state.selected_project=pid
            p=get_project(user['id'],pid)
            if p:
                left,right=st.columns([3,1]);
                with left: st.subheader(p['title']); st.caption(f"{p['discipline']} · {p['degree'] or 'Degree not specified'} · {p['semester'] or 'Semester not specified'}")
                with right: status_pill(p['status'])
                st.markdown("**Task description**"); st.write(p['description'])
                if p['success_criteria']: st.markdown("**Success criteria**"); st.write(p['success_criteria'])
                a,b=st.columns([1,1])
                with a:
                    if st.button("▶ Run workflow",use_container_width=True):
                        with st.spinner("Running the supported workflow and recording actual outputs..."):
                            result=run_project(user['id'],pid)
                        st.session_state.last_run={"project_id":pid,"data":result}; st.session_state.page="Agent Workspace"; st.rerun()
                with b:
                    if st.button("Delete project",use_container_width=True): st.session_state.confirm_delete=pid
                if st.session_state.get('confirm_delete')==pid:
                    st.warning("Delete this project and its workflow history? This cannot be undone.")
                    x,y=st.columns(2)
                    with x:
                        if st.button("Confirm delete",key=f"confirmdel{pid}"):
                            remove_project(user['id'],pid); st.session_state.selected_project=None; st.session_state.confirm_delete=None; st.success("Project deleted."); st.rerun()
                    with y:
                        if st.button("Cancel",key=f"canceldel{pid}"): st.session_state.confirm_delete=None; st.rerun()
                st.markdown("### Workflow history")
                if not p['runs']: st.caption("No workflow runs yet.")
                for run in p['runs']:
                    with st.expander(f"Run #{run['id']} · {run['status']} · {run['started_at'][:19]}"):
                        st.json(run['result'] or {"error":run['error']})
                        st.download_button("Download run report (JSON)",json.dumps(run,indent=2,ensure_ascii=False),file_name=f"universe_project_{pid}_run_{run['id']}.json",mime="application/json",key=f"dlrun{run['id']}")
        else: st.info("No projects match your search.")
elif page=="Agent Workspace":
    st.title("Agent Workspace"); st.caption("Execution traces are recorded from the actual deterministic workflow; no fake live activity is shown.")
    current=st.session_state.get('last_run')
    if current and current.get('project_id')==st.session_state.get('selected_project'):
        out=current['data']; st.markdown(f"### Latest run · #{out.get('run_id','—')}"); status_pill(out.get('status','unknown'))
        if out.get('status')=='failed': st.error(out.get('error','Workflow failed.'))
        for i,a in enumerate(out.get('agents',[]),1):
            with st.expander(f"{i}. {a.get('agent_name','Agent')} · {a.get('status','unknown')} · {a.get('duration_ms',0)} ms",expanded=(i==1)):
                st.write(a.get('summary',''))
                st.json(a.get('output',{}))
        st.markdown("### Final report")
        st.json(out.get('result',{}))
        st.download_button("Download complete workflow report",json.dumps(out,indent=2,ensure_ascii=False),file_name=f"universe_run_{out.get('run_id','latest')}.json",mime="application/json")
    else:
        chosen=st.session_state.get('selected_project')
        p=get_project(user['id'],chosen) if chosen else None
        if p and p['runs']:
            run=p['runs'][0]; st.markdown(f"### Latest saved run · {p['title']}"); status_pill(run['status'])
            for i,a in enumerate(run.get('agents',[]),1):
                with st.expander(f"{i}. {a['agent_name']} · {a['status']}",expanded=i==1): st.write(a['summary']); st.json(a['output'])
            st.json(run['result'])
        else:
            st.info("Choose a saved project and run its workflow to see real agent outputs, timings, and verification details.")
            if st.button("Go to My Projects"): st.session_state.page="My Projects"; st.rerun()
elif page=="Discipline Labs":
    st.title("Discipline Labs"); st.caption("Three initial workflows are implemented. Other disciplines are templates, not yet full execution engines.")
    tabs=st.tabs(["Computer Science","Engineering","Medical Education","Extensions"])
    with tabs[0]:
        st.markdown("### CS & IT Lab"); st.write("Turn a programming problem into requirements, an implementation checklist, and test ideas. Arbitrary code is not executed by the hosted app.")
        code_task=st.text_area("Programming task",key="lab_cs",placeholder="Build a Python function that validates email addresses...")
        if st.button("Analyse programming task"):
            if len(code_task.strip())<8: st.error("Please describe a task of at least 8 characters.")
            else:
                st.json({"classification":classify_task(code_task),"requirements":[x.strip() for x in code_task.splitlines() if x.strip()][:12],"safe_plan":["Define expected inputs and outputs","Implement small pure functions","Add normal, boundary, and invalid-input tests","Run tests in an isolated local environment","Review errors and retest"],"execution_policy":"No arbitrary code execution on this hosted app."})
    with tabs[1]:
        st.markdown("### Engineering Analysis Lab — Ohm's law")
        st.warning("Educational calculation only. Not engineering certification or a substitute for professional review.")
        mode=st.selectbox("Calculate",["Voltage (V = I × R)","Current (I = V / R)","Resistance (R = V / I)"])
        x1,x2=st.columns(2)
        with x1: val_a=st.number_input("Current (A) or Voltage (V)",min_value=0.0,value=2.0,step=.5)
        with x2: val_b=st.number_input("Resistance (Ω) or other value",min_value=0.0,value=6.0,step=.5)
        if st.button("Calculate and verify"):
            if mode.startswith("Voltage"):
                answer=val_a*val_b; equation="V = I × R"; unit="V"; valid=val_a>=0 and val_b>=0
            elif mode.startswith("Current"):
                answer=val_a/val_b if val_b else None; equation="I = V / R"; unit="A"; valid=val_b>0
            else:
                answer=val_a/val_b if val_b else None; equation="R = V / I"; unit="Ω"; valid=val_b>0
            if not valid or answer is None: st.error("The divisor must be greater than zero.")
            else:
                st.success(f"Result: {answer:.6g} {unit}"); st.latex(equation); st.write({"equation":equation,"result":answer,"unit":unit,"independent_check":"Re-evaluate the selected equation using the same inputs","assumptions":["Ideal DC circuit","Units must be consistent"]})
    with tabs[2]:
        st.markdown("### Medical Education Simulation Lab"); st.warning("Fictional educational case only — not diagnosis or treatment advice.")
        if st.button("Generate fictional learning case"):
            st.json({"fictional":True,"patient":"Fictional adult, age 34","presentation":"Fatigue and intermittent headache for three days; no additional observations supplied.","student_tasks":["List relevant follow-up history","Identify observations to collect","Discuss broad possibilities and uncertainty","Explain when urgent professional assessment is warranted"],"rubric":["Acknowledges missing information","Avoids definitive diagnosis","Identifies uncertainty","Recognises need for professional assessment"]})
    with tabs[3]:
        st.markdown("### Extensible templates")
        for name,desc in [("Agriculture","Dataset-based crop and irrigation analysis"),("Business","Sales, inventory, and financial-data analysis"),("Law","Source-grounded educational document analysis"),("Natural Sciences","Dataset analysis and controlled experiments")]:
            st.markdown(f"**{name}** · {desc} — <span style='color:#ffc56b'>Template only</span>",unsafe_allow_html=True)
elif page=="Skills & Evidence":
    st.title("Skills & Evidence"); st.caption("Evidence is derived from saved workflow records, not fabricated achievements.")
    runs=[]
    for p in projects:
        detail=get_project(user['id'],p['id'])
        if detail:
            for r in detail['runs']: runs.append((p,r))
    st.metric("Recorded workflow runs",len(runs)); st.metric("Completed runs",sum(r['status']=='completed' for _,r in runs))
    if not runs: st.info("Run a project workflow to build an evidence trail.")
    else:
        for p,r in runs:
            with st.expander(f"{p['title']} · Run #{r['id']} · {r['status']}"):
                st.write(f"Discipline: {p['discipline']} · Task: {p['task_type']}")
                st.write(f"Agent steps recorded: {len(r['agents'])}")
                st.json(r['result'])
elif page=="Settings":
    st.title("Settings"); st.caption("Workspace configuration and deployment health.")
    st.markdown('<div class="panel"><h3>Account</h3><p class="small-muted">Name and email are associated with your signed-in account.</p></div>',unsafe_allow_html=True)
    st.write("**Name:**",user['name']); st.write("**Email:**",user['email'])
    st.markdown("### Runtime status")
    st.success("Database connection initialized")
    st.write("**Execution mode:** Deterministic baseline (no live LLM call)")
    st.write("**Database dialect:**",engine.dialect.name)
    st.write("**External API key:**", "Configured" if settings.gemini_api_key else "Not configured; no Gemini calls are made by this MVP")
    st.markdown("### Data & safety")
    st.info("Uploaded files are not persisted. User code is never executed. Medical cases are fictional and educational. Use PostgreSQL through Streamlit Secrets for durable hosted data.")

st.markdown("---")
st.caption("UniVerse AI · One Intelligence. Every Discipline. Real-World Impact. · Deterministic MVP — review outputs before relying on them.")
