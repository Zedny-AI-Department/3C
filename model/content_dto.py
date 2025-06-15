from typing import Optional, List

from pydantic import BaseModel, Field


class VideoOutLines(BaseModel):
    video_name: str
    previous_video_name: Optional[str] = Field(default=None, title="The name of the previous video")
    video_keywords: List[str]
    video_description: str
    video_skill: str = Field(..., title="List of skills that the course covers")
    video_objective: str = Field(..., title="List of objectives that the course covers")
    video_duration: int = Field(..., title="Duration of the video in words")


class ChapterOutLines(BaseModel):
    chapter_name: str = Field(..., title="Name of the chapter")
    videos: List[VideoOutLines] = Field(..., title="List of video metadata that the chapter contains")


class CourseOutLines(BaseModel):
    country: Optional[str] = Field('US', title="Country of the course")
    course_name: str = Field(..., title="Name of the course")
    course_description: str = Field(..., title="description of the course")
    target_audience: str = Field(..., title="Target audience for the course")
    course_level: str = Field(..., title="Level of the course")
    course_slogan: str = Field(..., title="Slogan for the course")
    course_skills: List[str] = Field(None, title="List of skills that the course covers")
    course_objectives: List[str] = Field(None, title="List of objectives that the course covers")
    chapters: List[ChapterOutLines] = Field(..., title="List of chapters in the course")


class VideoScript(VideoOutLines):
    raw_content: Optional[str] = Field(None, description="The raw content retrieved from the web search")
    video_script: List[str] = Field(..., title="The script for the video")


class ChapterScript(ChapterOutLines):
    videos: List[VideoScript] = Field(..., title="List of video metadata that the chapter contains")


class CourseScript(CourseOutLines):
    chapters: List[ChapterScript] = Field(..., title="List of chapters in the course")
