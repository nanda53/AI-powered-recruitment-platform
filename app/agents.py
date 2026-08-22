from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from app.llm import chat
from app.db import SessionLocal
from app.models import Interviewer
from app.rag import retrieve

@tool
def find_interviewers(skills: list[str]) -> list[dict]:
    """Return interviewers whose skills overlap the given skills (the candidate's gaps)."""
    db = SessionLocal()
    out = []
    for iv in db.query(Interviewer).all():
        overlap = set(map(str.lower, iv.skills)) & set(map(str.lower, skills))
        if overlap:
            out.append({"name": iv.name, "seniority": iv.seniority,
                        "covers": sorted(overlap)})
    return out

@tool
def panel_policy(query: str) -> str:
    """Retrieve HR panel-composition policy passages (cited)."""
    return "\n".join(f'[{c["citation"]}] {c["text"]}' for c in retrieve(query))

PANEL_SYS = (
    "  You recommend a final 2-person interview panel. Steps: (1) call panel_policy to get the "
    "composition rules; (2) call find_interviewers for the candidate's missing skills. "
    "If there are NO missing skills, call find_interviewers with the role's core skills "
    "instead, and compose a policy-compliant panel (e.g. at least one senior, diverse "
    "backgrounds). "
    "OUTPUT the final panel only: name the 2 interviewers, what each covers, and a one-line "
    "policy justification with the citation. Do NOT ask the user any questions. Do NOT ask to "
    "proceed. Never invent interviewers not returned by the tool."
)

panel_agent = create_react_agent(chat("agent"),
                                 tools=[find_interviewers, panel_policy],
                                 prompt=PANEL_SYS)

def recommend_panel(missing_skills: list[str]) -> str:
    r = panel_agent.invoke({"messages": [("human",
            f"Recommend a panel for gaps: {missing_skills}")]})
    return r["messages"][-1].content
