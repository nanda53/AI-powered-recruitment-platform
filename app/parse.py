from app.llm import chat
from app.schemas import CandidateProfile

SYSTEM = (
    "You extract structured data from a resume. "
    "Return ONLY the fields requested. Do not invent skills or credentials. "
    "If a field is missing, leave it empty/null."
)

def parse_resume(raw_text: str) -> CandidateProfile:
    llm = chat("parse").with_structured_output(CandidateProfile)   # forces the schema
    return llm.invoke([("system", SYSTEM), ("human", raw_text)])
