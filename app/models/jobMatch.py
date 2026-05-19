from typing import List

from pydantic import BaseModel, Field


class JobMatchAnalysis(BaseModel):
    match_score: int = Field(..., ge=0, le=100, description="Overall match score between candidate and job")
    strong_matches: List[str] = Field(..., description="List of strong matches with citations from candidate's data")
    skill_gaps: List[str] = Field(default_factory=list, description="List of potential concerns or skill gaps")
    tailoring_recommendations: List[str] = Field(..., description="Key tailoring recommendations for the candidate")
    overall_verdict: str = Field(..., description="Overall verdict on the candidate's fit for the job")
    confidence_level: str = Field(..., description="Confidence level of the analysis (e.g., High, Medium, Low)")