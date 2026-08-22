from app.db import SessionLocal, Base, engine
from app.models import Interviewer

Base.metadata.create_all(engine)
db = SessionLocal()

if db.query(Interviewer).count() == 0:
    db.add_all([
        Interviewer(name="Alice Chen",   seniority="senior", skills=["Python","FastAPI","AWS","System Design"]),
        Interviewer(name="Bob Martinez", seniority="senior", skills=["SQL","PostgreSQL","Docker","Cloud"]),
        Interviewer(name="Priya Nair",   seniority="mid",    skills=["Python","LangChain","ML","scikit-learn"]),
        Interviewer(name="Sam Okoye",    seniority="mid",    skills=["REST","Git","AWS","Testing"]),
    ])
    db.commit()
    print("seeded 4 interviewers")
else:
    print("interviewers already present")