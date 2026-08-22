from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, func
from app.db import Base

class Candidate(Base):
    __tablename__ = "candidates"
    id            = Column(Integer, primary_key=True)
    raw_text      = Column(String(20000))          # extracted resume text
    profile       = Column(JSON)                    # structured profile (see schema)
    pii           = Column(JSON)                     # vaulted PII (name, etc.)
    created_at    = Column(DateTime, server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"
    id            = Column(Integer, primary_key=True)
    title         = Column(String(255))
    description   = Column(String(20000))            # JD text
    rubric        = Column(JSON)                      # required skills, min years...

class Application(Base):
    __tablename__ = "applications"
    id            = Column(Integer, primary_key=True)
    candidate_id  = Column(Integer, ForeignKey("candidates.id"))
    job_id        = Column(Integer, ForeignKey("jobs.id"))
    status        = Column(String(32), default="received")
    created_at    = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id            = Column(Integer, primary_key=True)
    application_id= Column(Integer)
    step          = Column(String(64))               # "parse", "score"...
    model         = Column(String(128))              # which LLM/version
    payload       = Column(JSON)                       # inputs + outputs
    created_at    = Column(DateTime, server_default=func.now())


###Phase 2 JD Matcher ####

class MatchResult(Base):
    __tablename__ = "match_results"
    id           = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id       = Column(Integer, ForeignKey("jobs.id"))
    features     = Column(JSON)
    created_at   = Column(DateTime, server_default=func.now())


#### Phase 4 RAG ###

class PolicyDoc(Base):
    __tablename__ = "policy_docs"
    id        = Column(Integer, primary_key=True)
    title     = Column(String(255))
    source    = Column(String(255))       # filename / URL for citation
    text      = Column(String(50000))



### Phase 5 GEN AI ####
class GenOutput(Base):
    __tablename__ = "gen_outputs"
    id            = Column(Integer, primary_key=True)
    candidate_id  = Column(Integer, ForeignKey("candidates.id"))
    job_id        = Column(Integer, ForeignKey("jobs.id"))
    summary       = Column(JSON)
    interview_kit = Column(JSON)
    panel         = Column(String(8000))          # panel recommendation text (Phase 6 agent)
    created_at    = Column(DateTime, server_default=func.now())

### Phase 6 Agent(LANGgraph)

class Interviewer(Base):
    __tablename__ = "interviewers"
    id        = Column(Integer, primary_key=True)
    name      = Column(String(255))
    seniority = Column(String(32))              # junior/mid/senior
    skills    = Column(JSON)                     # ["Python","AWS",...]




