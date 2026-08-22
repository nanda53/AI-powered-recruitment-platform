# pipeline_debug.py
# Open in your IDE, set breakpoints on the marked lines, and STEP THROUGH the
# whole recruitment pipeline for ONE candidate against ONE job.
#
# Run under a debugger:
#   VS Code  : open this file, press F5 (Python: Current File)
#   PyCharm  : right-click -> Debug 'pipeline_debug'
#   terminal : python -m pdb pipeline_debug.py     (n = next line, p var = print, c = continue)
#
# No try/except anywhere on purpose — if a stage breaks, the debugger stops
# right on it so you can inspect the real error.

from app.db import SessionLocal
from app.models import Candidate, Job
from app.matching import build_features
from app.scoring import score
from app.generate import make_summary, make_questions, recommend_pay
from app.agents import recommend_panel
from app.rag import retrieve

# ---- pick who to trace (edit these) ------------------------------------
CANDIDATE_ID = 1
JOB_ID = 1
THRESHOLD = 0.6

db = SessionLocal()

cand = db.get(Candidate, CANDIDATE_ID)     # <-- BREAKPOINT: inspect `cand`, `cand.profile`
job = db.get(Job, JOB_ID)                  # <-- BREAKPOINT: inspect `job`, `job.title`, `job.rubric`

# ---- STAGE 1: ingestion (Phase 1) — the parsed resume ------------------
profile = cand.profile                     # <-- BREAKPOINT: inspect `profile`

# ---- STAGE 2: JD match (Phase 2) ---------------------------------------
features = build_features(profile, job)    # <-- BREAKPOINT: step INTO to see matching logic; inspect `features`

# ---- STAGE 3: rubric score (Phase 3A) ----------------------------------
result = score(features)                   # <-- BREAKPOINT: step INTO scoring; inspect `result` (score/breakdown/explanation)

# ---- STAGE 4: shortlist gate (orchestrator route) ----------------------
shortlisted = result["score"] >= THRESHOLD  # <-- BREAKPOINT: inspect `shortlisted`

# ---- STAGE 5: GenAI summary (Phase 5) ----------------------------------
summary = make_summary(profile, features).model_dump()          # <-- BREAKPOINT: inspect `summary`

# ---- STAGE 6: interview kit (Phase 5) ----------------------------------
kit = make_questions(profile, features, job.title).model_dump()  # <-- BREAKPOINT: inspect `kit`

# ---- STAGE 7: panel recommendation (Phase 6 agent) ---------------------
gaps = features.get("missing_skills", [])
search_skills = gaps or features.get("matched_skills", [])
panel = recommend_panel(search_skills)     # <-- BREAKPOINT: step INTO the agent; inspect `panel`

# ---- STAGE 8: RAG HR-policy retrieval (Phase 4) ------------------------
policy_hits = retrieve("interview panel policy for " + job.title)  # <-- BREAKPOINT: inspect `policy_hits` (citations)

# ---- STAGE 9: pay-band recommendation ----------------------------------
pay = recommend_pay(profile, features, job.title).model_dump()   # <-- BREAKPOINT: inspect `pay`

print("done | shortlisted:", shortlisted, "| score:", result["score"])
print("summary keys:", list(summary))
print("kit questions:", len(kit.get("questions", [])))
print("policy hits:", len(policy_hits))
