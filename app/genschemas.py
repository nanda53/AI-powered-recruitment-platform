# Phase 5: GenAI structured-output schemas

from pydantic import BaseModel, Field

class Summary(BaseModel):
    strengths:      list[str] = Field(default_factory=list)
    gaps:           list[str] = Field(default_factory=list)
    flags:          list[str] = Field(default_factory=list)   # inconsistencies, risks
    recommendation: str = ""                                  # 1-2 sentence verdict

class Question(BaseModel):
    question:   str
    kind:       str      # "technical" | "behavioral"
    difficulty: str      # "easy" | "medium" | "hard"
    targets:    str      # which skill/gap it probes

class InterviewKit(BaseModel):
    questions: list[Question] = Field(default_factory=list)


class PayBand(BaseModel):
    suggested_range: str = ""                          # e.g. "$125,000–$155,000"
    points: list[str] = Field(default_factory=list)    # 5-6 justification bullets
