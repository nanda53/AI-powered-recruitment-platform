### Phase3 Scoring###

WEIGHTS = {                       # tune these; must sum to 1.0
    "skills_coverage":     0.45,
    "experience_fit":      0.25,
    "semantic_similarity": 0.20,
    "education_match":     0.10,
}

def score(features: dict) -> dict:
    contribs = {k: round(w * features.get(k, 0), 3) for k, w in WEIGHTS.items()}
    total = round(sum(contribs.values()), 3)          # 0..1
    return {
        "score": total,
        "breakdown": contribs,                        # explainability, per feature
        "explanation": (
            f"{int(features.get('skills_coverage',0)*100)}% skills, "
            f"exp fit {features.get('experience_fit',0)}, "
            f"missing: {features.get('missing_skills', [])}"
        ),
    }
