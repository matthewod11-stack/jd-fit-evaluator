from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Stint(BaseModel):
    org: str = Field(..., description="Employer or client")
    title: str = Field(...)
    industry: Optional[str] = None
    start: date
    end: Optional[date] = None
    employment_type: Optional[str] = None  # full-time, contract, freelance
    projects: List[Project] = Field(default_factory=list)

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v, info):
        if v is None:
            return v
        start = info.data.get("start") if info and hasattr(info, "data") else None
        if start and v < start:
            raise ValueError("end must be greater than or equal to start")
        return v
