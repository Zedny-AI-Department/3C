from typing import List

from pydantic import BaseModel, Field


class CourseKnowledge(BaseModel):
    context: List[str] = Field(..., title="Context")
    detailed_results: List = Field(..., title="Detailed Results")