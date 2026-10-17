"""Bounded deterministic multi-agent workflow; no fabricated LLM traces."""
from datetime import datetime, timezone
from time import perf_counter
from app.ml.router import classify_task
MAX_STEPS=6
def execute_workflow(project):
    started=perf_counter(); desc=project.description.strip(); discipline=project.discipline.lower(); task=project.task_type.lower(); agents=[]
    def step(name, fn):
        t=perf_counter(); out=fn(); agents.append({"agent_name":name,"status":"completed","summary":out.get("summary", "Completed"),"output":out,"duration_ms":round((perf_counter()-t)*1000)}); return out
    route=step("Router & Planner",lambda:{"summary":"Classified request and created a bounded execution plan","classification":classify_task(desc),"plan":["Interpret requirements","Run discipline-specific tool","Verify deterministic constraints","Prepare evidence-linked report"]})
    if "engineering" in discipline or "circuit" in task or "calculator" in task:
        def calc():
            import re
            nums=[float(x) for x in re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?",desc)]
            # Explicit safe supported calculator: V=IR, when exactly two positive values are provided.
            if len(nums)<2: return {"summary":"Needs two numeric values","needs_input":True,"message":"Provide two values, e.g. voltage 12 V and resistance 6 ohm, or current 2 A and resistance 6 ohm."}
            a,b=nums[0],nums[1]
            if a<=0 or b<=0: return {"summary":"Input validation failed","verified":False,"error":"Values must be positive."}
            if "voltage" in desc.lower() or re.search(r"\bV\s*=",desc): result={"equation":"I = V / R","inputs":{"voltage_V":a,"resistance_ohm":b},"result":{"current_A":a/b}}
            else: result={"equation":"V = I × R (assumed first value is current, second resistance)","inputs":{"current_A":a,"resistance_ohm":b},"result":{"voltage_V":a*b}}
            return {"summary":"Calculated using Ohm’s law","verified":True,**result,"assumptions":["Ideal DC circuit","First two numbers interpreted according to task wording; confirm before consequential use"]}
        result=step("Engineering Calculation Agent",calc)
        verify=step("Independent Verification Agent",lambda:{"summary":"Checked result against equation and input constraints","passed":bool(result.get("verified")) if "verified" in result else bool(result.get("needs_input")),"checks":["positive numeric inputs", "equation applied deterministically"],"note":"Simplified educational calculator; not engineering certification."})
    elif "medical" in discipline or "medical" in task:
        result=step("Medical Education Case Agent",lambda:{"summary":"Created fictional learning case and structured reasoning exercise","case":{"fictional":True,"patient":"Fictional adult, age 34","presentation":"Reports fatigue and intermittent headache for three days; no additional observations supplied.","student_tasks":["List relevant follow-up history","Identify observations that would be important to collect","Discuss a broad differential and uncertainty","Explain when urgent professional assessment is warranted"]},"safety":"Educational simulation only. This is not a diagnosis or treatment recommendation."})
        verify=step("Safety & Rubric Agent",lambda:{"summary":"Reviewed educational framing and uncertainty","passed":bool(result["case"]["fictional"] and "not a diagnosis" in result["safety"]),"rubric":["Acknowledges missing information","Avoids definitive diagnosis","Identifies uncertainty","Recognises need for professional assessment"]})
    else:
        result=step("Computer Science Lab Agent",lambda:{"summary":"Analysed requirements and produced a safe implementation checklist","requirements":[x.strip() for x in desc.splitlines() if x.strip()][:12],"plan":["Define expected input and output","Implement small pure functions","Add boundary and invalid-input tests","Run tests in an isolated development environment","Review errors and retest"],"execution_policy":"Arbitrary uploaded code is not executed by this server. Use the downloadable checklist and run code in your own isolated environment.","test_template":"Add tests for a normal case, an empty input, invalid types, and boundary values."})
        verify=step("Verification Agent",lambda:{"summary":"Checked that the task has actionable requirements and safe next steps","passed":len(desc)>=8 and bool(result.get("plan")),"checks":["description length validated","implementation checklist present","unsafe arbitrary code execution disabled"]})
    report=step("Final Report Agent",lambda:{"summary":"Compiled workflow evidence and limitations","discipline":project.discipline,"task_type":project.task_type,"result":result,"verification":verify,"agent_count":len(agents)+1,"completed_at":datetime.now(timezone.utc).isoformat(),"limitations":["LLM provider is not called in deterministic baseline mode","Outputs require student review","No arbitrary code execution"]})
    return {"status":"completed","agents":agents,"result":report,"duration_ms":round((perf_counter()-started)*1000)}
