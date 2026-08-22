from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.db import SessionLocal
from app.models import Candidate, Job, MatchResult, GenOutput
from app.matching import build_features
from app.scoring import score
from app.generate import make_summary, make_questions
from app.agents import recommend_panel

SHORTLIST_THRESHOLD = 0.6

class AppState(TypedDict, total=False):
    candidate_id: int
    job_id:       int
    features:     dict
    score:        dict
    shortlisted:  bool
    summary:      dict
    interview_kit:dict
    panel:        str

def match_node(s: AppState) -> AppState:
    db = SessionLocal()
    cand, job = db.get(Candidate, s["candidate_id"]), db.get(Job, s["job_id"])
    s["features"] = build_features(cand.profile, job)
    return s

def score_node(s: AppState) -> AppState:
    s["score"] = score(s["features"])
    s["shortlisted"] = s["score"]["score"] >= SHORTLIST_THRESHOLD
    return s

def route(s: AppState) -> str:
    return "generate" if s["shortlisted"] else "reject"

def generate_node(s: AppState) -> AppState:
    db = SessionLocal()
    cand, job = db.get(Candidate, s["candidate_id"]), db.get(Job, s["job_id"])
    s["summary"]       = make_summary(cand.profile, s["features"]).model_dump()
    s["interview_kit"] = make_questions(cand.profile, s["features"], job.title).model_dump()
    return s

def panel_node(s: AppState) -> AppState:
    gaps = s["features"].get("missing_skills", [])
    search_skills = gaps or s["features"].get("matched_skills", [])   # fallback to matched
    s["panel"] = recommend_panel(search_skills)
    _persist(s)
    return s

def reject_node(s: AppState) -> AppState:
    _persist(s)
    return s

def _persist(s: AppState):
    db = SessionLocal()
    # write the MatchResult so the interviewer dashboard (reads MatchResult) sees this candidate
    db.query(MatchResult).filter_by(candidate_id=s["candidate_id"], job_id=s["job_id"]).delete(synchronize_session=False)
    db.add(MatchResult(candidate_id=s["candidate_id"], job_id=s["job_id"], features=s.get("features")))
    db.add(GenOutput(candidate_id=s["candidate_id"], job_id=s["job_id"],
                     summary=s.get("summary"), interview_kit=s.get("interview_kit"),
                     panel=s.get("panel")))
    db.commit()

# build the graph
g = StateGraph(AppState)
g.add_node("match", match_node)
g.add_node("score", score_node)
g.add_node("generate", generate_node)
g.add_node("panel", panel_node)
g.add_node("reject", reject_node)
g.add_edge(START, "match")
g.add_edge("match", "score")
g.add_conditional_edges("score", route, {"generate": "generate", "reject": "reject"})
g.add_edge("generate", "panel")
g.add_edge("panel", END)
g.add_edge("reject", END)

pipeline = g.compile()
