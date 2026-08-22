# Phase 2: JD matcher — turns a profile + job into scoring features

import numpy as np
from pydantic import BaseModel

from app.llm import embedder, chat

_emb = embedder()


def cosine(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

def semantic_similarity(profile_text: str, jd_text: str) -> float:
    va, vb = _emb.embed_documents([profile_text, jd_text])
    return cosine(va, vb)          # 0..1


class SkillMatch(BaseModel):
    matched: list[str]     # required skills the candidate has (incl. synonyms)
    missing: list[str]     # required skills not evidenced

SKILL_SYS = ("Given REQUIRED skills and a candidate's skills, decide which required "
             "skills are satisfied (treat synonyms/abbreviations as matches). "
             "Return matched and missing lists. Do not invent candidate skills.")

def match_skills(required: list[str], candidate: list[str]) -> SkillMatch:
    llm = chat("match").with_structured_output(SkillMatch)
    return llm.invoke([("system", SKILL_SYS),
                       ("human", f"REQUIRED: {required}\nCANDIDATE: {candidate}")])


EDU_RANK = {"Bachelors": 1, "Masters": 2, "PhD": 3}

def _norm_edu(level: str | None) -> str | None:
    """Map free-text education ("B.S. Computer Science") to Bachelors/Masters/PhD.
    The parser returns raw text, so normalize before ranking (real bug hit in build)."""
    if not level:
        return None
    l = level.lower()
    if "phd" in l or "doctor" in l:                                  return "PhD"
    if "master" in l or "m.s" in l or "msc" in l or "mtech" in l:    return "Masters"
    if "bachelor" in l or "b.s" in l or "b.e" in l or "btech" in l:  return "Bachelors"
    return None

def build_features(profile: dict, job) -> dict:
    rub = job.rubric
    sm  = match_skills(rub["required_skills"], profile.get("skills", []))
    req = max(len(rub["required_skills"]), 1)

    skills_coverage = len(sm.matched) / req                      # 0..1
    exp_fit = min(profile.get("total_experience", 0) /
                  max(rub.get("min_years", 1), 1), 1.0)          # capped 0..1
    cand_edu = _norm_edu(profile.get("education_level"))         # normalize first
    edu_ok = 1.0 if (not rub.get("min_education") or
                     EDU_RANK.get(cand_edu, 0)
                     >= EDU_RANK.get(rub["min_education"], 0)) else 0.0
    sem = semantic_similarity(" ".join(profile.get("skills", [])),
                              job.description)

    return {
        "skills_coverage": round(skills_coverage, 3),
        "experience_fit":  round(exp_fit, 3),
        "education_match": edu_ok,
        "semantic_similarity": round(sem, 3),
        "matched_skills": sm.matched,
        "missing_skills": sm.missing,       # <-- Panel Rec agent (Phase 6) uses this
    }
