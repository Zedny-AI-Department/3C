from typing import Optional, List

from pydantic import BaseModel, Field


class CourseOutlineRequest(BaseModel):
    country: Optional[str] = Field('US', title="Country of the course")
    course_name: str = Field(..., title="Name of the course")
    target_audience: str = Field(..., title="Target audience for the course")
    course_level: str = Field(..., title="Level of the course (e.g., beginner, intermediate, advanced)")
    brief: Optional[str] = Field(
        None,
        title="Brief description of the course",
        description="A brief description to help in generating the course outline"
    )
    chapter_count: int = Field(
        ...,
        title="Number of chapters in the course",
        description="The number of chapters to be included in the course outline"
    )
    video_count: int = Field(
        ...,
        title="Number of videos per chapter",
        description="The number of videos to be included in each chapter of the course outline"
    )
    min_words_per_video: int = Field(
        ...,
        title="Minimum words per video",
        description="The minimum number of words that should be included in each video script"
    )
    max_words_per_video: int = Field(
        ...,
        title="Maximum words per video",
        description="The maximum number of words that should be included in each video script"
    )
    language: Optional[str] = Field(
        default="English",
        title="Language of the course",
        description="The language in which the course will be delivered"
    )
    limitations: Optional[str] = Field(
        default=None,
        title="Limitations of the course",
        description="Any limitations or constraints that should be considered while generating the course outline"
    )
    skills: List[str] = Field(
        ...,
        title="Skills to be acquired",
        description="Skills that the course aims to impart to the learners"
    )
