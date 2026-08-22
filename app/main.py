import app.config  # loads .env once, before anything else
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.db import engine, Base, SessionLocal
from app.llm import chat, embedder, MODELS
from app import models
from app.models import Candidate, AuditLog, Job, MatchResult, GenOutput
from app.extract import extract_text
from app.parse import parse_resume
from app.pii import extract_pii
from app.matching import build_features
from app.scoring import score
from app.rag import ingest_policy, retrieve
from app.generate import make_summary, make_questions, ask_about_candidate, recommend_pay
from app.orchestrator import pipeline

app = FastAPI(title="AI Recruitment Platform")

Base.metadata.create_all(engine)


@app.get("/health")
def health():
    out = {}
    # DB
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        out["db"] = "ok"
    except Exception as e:
        out["db"] = f"error: {e}"
    # chat
    try:
        r = chat("parse").invoke("Reply with exactly: OK")
        out["chat"] = "ok" if "OK" in r.content else r.content[:40]
    except Exception as e:
        out["chat"] = f"error: {e}"
    # embeddings
    try:
        v = embedder().embed_query("hello")
        out["embeddings"] = f"ok dim={len(v)}"
    except Exception as e:
        out["embeddings"] = f"error: {e}"
    return out


# ---- Phase 1: resume ingestion -------------------------------------------

@app.post("/resumes")
async def upload_resume(file: UploadFile = File(...)):
    # save temp file
    suffix = "." + file.filename.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp); path = tmp.name

    raw     = extract_text(path)
    profile = parse_resume(raw)
    pii     = extract_pii(raw)

    db = SessionLocal()
    cand = Candidate(raw_text=raw[:20000], profile=profile.model_dump(), pii=pii)
    db.add(cand); db.commit(); db.refresh(cand)
    db.add(AuditLog(application_id=cand.id, step="parse",
                    model=MODELS["parse"],
                    payload={"profile": profile.model_dump()}))
    db.commit()
    return {"candidate_id": cand.id, "profile": profile.model_dump(), "pii_captured": bool(pii)}


# ---- Phase 2: JD matcher -------------------------------------------------

class JobIn(BaseModel):
    title: str
    description: str
    required_skills: list[str]
    min_years: float = 0
    min_education: str | None = None      # Bachelors/Masters/PhD

@app.post("/jobs")
def create_job(job: JobIn):
    db = SessionLocal()
    row = Job(title=job.title, description=job.description,
              rubric={"required_skills": job.required_skills,
                      "min_years": job.min_years,
                      "min_education": job.min_education})
    db.add(row); db.commit(); db.refresh(row)
    return {"job_id": row.id}

@app.post("/match")
def match(candidate_id: int, job_id: int):
    db = SessionLocal()
    cand = db.get(Candidate, candidate_id)
    job  = db.get(Job, job_id)
    feats = build_features(cand.profile, job)
    row = MatchResult(candidate_id=candidate_id, job_id=job_id, features=feats)
    db.add(row); db.commit()
    return {"match_id": row.id, "features": feats}


# ---- Phase 3: scoring ----------------------------------------------------

@app.post("/score")
def score_candidate(match_id: int):
    db = SessionLocal()
    m = db.get(MatchResult, match_id)
    result = score(m.features)
    db.add(AuditLog(application_id=m.candidate_id, step="score",
                    model="rubric-v1", payload=result))
    db.commit()
    return result


# ---- Phase 4: RAG (HR policy) --------------------------------------------

class PolicyIn(BaseModel):
    title: str
    source: str
    text: str

@app.post("/policies")
def add_policy(p: PolicyIn):
    ingest_policy(p.title, p.source, p.text)
    return {"status": "ingested", "title": p.title}

@app.get("/policies/search")
def search_policy(q: str):
    return {"results": retrieve(q)}


# ---- Phase 5: GenAI ------------------------------------------------------

@app.post("/generate")
def generate(candidate_id: int, job_id: int):
    db = SessionLocal()
    cand = db.get(Candidate, candidate_id)
    job  = db.get(Job, job_id)
    m = (db.query(MatchResult)
           .filter_by(candidate_id=candidate_id, job_id=job_id)
           .order_by(MatchResult.id.desc()).first())

    summary = make_summary(cand.profile, m.features)
    kit     = make_questions(cand.profile, m.features, job.title)

    row = GenOutput(candidate_id=candidate_id, job_id=job_id,
                    summary=summary.model_dump(), interview_kit=kit.model_dump())
    db.add(row); db.commit()
    return {"summary": summary.model_dump(), "interview_kit": kit.model_dump()}


# ---- Phase 6: agents (LangGraph pipeline) --------------------------------

@app.post("/process")
def process(candidate_id: int, job_id: int):
    final = pipeline.invoke({"candidate_id": candidate_id, "job_id": job_id})
    return {
        "score": final["score"],
        "shortlisted": final["shortlisted"],
        "summary": final.get("summary"),
        "interview_kit": final.get("interview_kit"),
        "panel": final.get("panel"),
    }


# ---- Phase 7: interviewer dashboard --------------------------------------

@app.get("/jobs")
def list_jobs():
    db = SessionLocal()
    return [{"job_id": j.id, "title": j.title, "description": j.description,
             "required_skills": (j.rubric or {}).get("required_skills", [])}
            for j in db.query(Job).all()]

@app.get("/candidates")               # ranked list for a job (interviewer picks from this)
def list_candidates(job_id: int):
    db = SessionLocal()
    out = []
    for m in db.query(MatchResult).filter_by(job_id=job_id).all():
        s = score(m.features)
        out.append({"candidate_id": m.candidate_id, "score": s["score"],
                    "explanation": s["explanation"],
                    "missing_skills": m.features.get("missing_skills", [])})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out

@app.get("/interview/{candidate_id}")  # full saved output for one candidate
def interview_view(candidate_id: int, job_id: int):
    db = SessionLocal()
    gen = (db.query(GenOutput).filter_by(candidate_id=candidate_id, job_id=job_id)
             .order_by(GenOutput.id.desc()).first())
    if not gen:
        raise HTTPException(404, "candidate not processed for this job yet")
    return {"summary": gen.summary, "interview_kit": gen.interview_kit, "panel": gen.panel}

@app.post("/interview/{candidate_id}/ask")  # interviewer asks a resume-grounded question
def ask_candidate(candidate_id: int, topic: str):
    db = SessionLocal()
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "candidate not found")
    return ask_about_candidate(cand.profile, cand.raw_text or "", topic).model_dump()


# ---- Recruiter decision (immutable audit trail) --------------------------

class Decision(BaseModel):
    candidate_id: int
    job_id: int
    action: str          # "accept" | "reject"
    recruiter: str
    reason: str = ""

@app.post("/decision")
def record_decision(d: Decision):
    db = SessionLocal()
    db.add(AuditLog(application_id=d.candidate_id, step="recruiter_decision",
                    model=f"human:{d.recruiter}",
                    payload=d.model_dump()))              # immutable trail
    db.commit()
    return {"status": "logged", "action": d.action}


# ---- Phase 8: PII erasure ------------------------------------------------

@app.delete("/candidates/{cid}/pii")
def erase_pii(cid: int):
    db = SessionLocal()
    c = db.get(Candidate, cid)
    c.pii = None                      # erase PII, keep anonymized profile + audit trail
    db.commit()
    return {"status": "pii_erased", "candidate_id": cid}


# ---- Phase 9: pay-band recommendation ------------------------------------

@app.post("/interview/{candidate_id}/pay")
def pay_reco(candidate_id: int, job_id: int):
    db = SessionLocal()
    cand = db.get(Candidate, candidate_id)
    job  = db.get(Job, job_id)
    if not cand or not job:
        raise HTTPException(404, "candidate or job not found")
    m = (db.query(MatchResult).filter_by(candidate_id=candidate_id, job_id=job_id)
           .order_by(MatchResult.id.desc()).first())
    return recommend_pay(cand.profile, m.features if m else {}, job.title).model_dump()
