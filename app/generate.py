# Phase 5: GenAI (summaries, interview questions, pay bands)

from app.llm import chat
from app.rag import retrieve
from app.genschemas import Summary, InterviewKit, PayBand

SUMMARY_SYS = (
    "You write a concise recruiter-facing candidate summary. "
    "Use ONLY the profile and match features given. Never invent skills, employers, "
    "or credentials. Flag any inconsistencies you actually see (e.g. overlapping dates). "
    "Be balanced: real strengths AND real gaps."
)

def make_summary(profile: dict, features: dict) -> Summary:
    llm = chat("generate").with_structured_output(Summary)
    return llm.invoke([
        ("system", SUMMARY_SYS),
        ("human", f"PROFILE:\n{profile}\n\nMATCH FEATURES:\n{features}"),
    ])


QUESTIONS_SYS = (
    "Generate exactly 5 interview questions tailored to THIS candidate's gaps. "
    "Ground technical scope in the ROLE RUBRIC passages provided (do not go beyond them). "
    "Mix technical and behavioral; vary difficulty. Each question must target a specific "
    "skill or gap."
)

def make_questions(profile: dict, features: dict, job_title: str) -> InterviewKit:
    rubric_ctx = retrieve(f"interview focus and required skills for {job_title}")
    passages   = "\n".join(c["text"] for c in rubric_ctx) or "(no rubric found)"
    llm = chat("generate").with_structured_output(InterviewKit)
    return llm.invoke([
        ("system", QUESTIONS_SYS),
        ("human", f"GAPS: {features.get('missing_skills', [])}\n"
                  f"PROFILE: {profile}\n\nROLE RUBRIC:\n{passages}"),
    ])


def ask_about_candidate(profile: dict, raw_text: str, topic: str) -> InterviewKit:
    sys = ("You help an interviewer. Generate 3 interview questions about the requested TOPIC, "
           "grounded ONLY in THIS candidate's resume — reference specifics from their actual "
           "experience. Never invent facts not in the resume.")
    llm = chat("generate").with_structured_output(InterviewKit)
    return llm.invoke([("system", sys),
                       ("human", f"TOPIC: {topic}\n\nRESUME:\n{raw_text}\n\nPROFILE:\n{profile}")])


PAY_SYS = (
    "You are an HR compensation assistant. Using ONLY the candidate's skills and experience "
    "and the COMPENSATION POLICY passages provided, recommend a fair pay band. Give a "
    "suggested_range (min–max from the policy's bands) and 5-6 concise bullet points — each "
    "tied to a specific skill, the experience level, education, or a policy rule. Stay within "
    "the policy's bands; never invent numbers beyond the policy.")

def recommend_pay(profile: dict, features: dict, job_title: str) -> PayBand:
    ctx = retrieve(f"compensation salary pay band for {job_title}")
    passages = "\n".join(f'[{c["citation"]}] {c["text"]}' for c in ctx) or "(no policy found)"
    llm = chat("generate").with_structured_output(PayBand)
    return llm.invoke([("system", PAY_SYS),
        ("human", f"JOB: {job_title}\nSKILLS: {profile.get('skills')}\n"
                  f"EXPERIENCE_YEARS: {profile.get('total_experience')}\n"
                  f"EDUCATION: {profile.get('education_level')}\n"
                  f"MATCH_FEATURES: {features}\n\nCOMPENSATION POLICY:\n{passages}")])
