from pydantic import BaseModel, Field

class WorkItem(BaseModel):
    company: str
    role: str
    years: float

class CandidateProfile(BaseModel):
    skills:            list[str]           = Field(default_factory=list)
    total_experience:  float               = 0            # years
    education_level:   str | None = None                  # Bachelors/Masters/PhD
    cgpa:              float | None = None
    work_history:      list[WorkItem]      = Field(default_factory=list)
    certifications:    list[str]           = Field(default_factory=list)
