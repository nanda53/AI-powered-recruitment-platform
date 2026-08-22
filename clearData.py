from app.db import SessionLocal
from app.models import Candidate, MatchResult, GenOutput

d = SessionLocal()

# delete children first (FK-safe), keep Job / Interviewer / policies
print("gen_outputs deleted:", d.query(GenOutput).delete())
print("matches deleted    :", d.query(MatchResult).delete())

for name in ("Application", "AuditLog"):
    try:
        mod = __import__("app.models", fromlist=[name])
        M = getattr(mod, name)
        print(name, "deleted     :", d.query(M).delete())
    except Exception:
        pass

print("candidates deleted :", d.query(Candidate).delete())

d.commit()
print("DONE. Jobs, interviewers, and policies were kept.")
