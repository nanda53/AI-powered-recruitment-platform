

from app.db import SessionLocal, Base, engine
from app.models import Job
Base.metadata.create_all(engine)
db = SessionLocal()

JOBS = [
    {"title":"Backend Engineer","description":"Build scalable Python APIs. Python, FastAPI, SQL, REST, AWS. 3+ yrs.",
     "required_skills":["Python","FastAPI","SQL","AWS"],"min_years":3,"min_education":"Bachelors"},
    {"title":"Frontend Engineer","description":"Build modern web UIs. React, TypeScript, CSS, REST. 2+ yrs.",
     "required_skills":["React","TypeScript","CSS","REST"],"min_years":2,"min_education":"Bachelors"},
    {"title":"Data Scientist","description":"ML models + analysis. Python, pandas, scikit-learn, SQL. 3+ yrs.",
     "required_skills":["Python","Machine Learning","pandas","SQL"],"min_years":3,"min_education":"Masters"},
    {"title":"DevOps Engineer","description":"CI/CD + infra. Docker, Kubernetes, AWS, Terraform. 4+ yrs.",
     "required_skills":["Docker","Kubernetes","AWS","CI/CD"],"min_years":4,"min_education":"Bachelors"},
]
added = 0
for j in JOBS:
    if db.query(Job).filter_by(title=j["title"]).first():
        continue
    db.add(Job(title=j["title"], description=j["description"],
               rubric={"required_skills":j["required_skills"],
                       "min_years":j["min_years"],"min_education":j["min_education"]}))
    added += 1
db.commit()
print(f"seeded {added} jobs; total = {db.query(Job).count()}")
