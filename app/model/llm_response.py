from typing import List

from pydantic import BaseModel

from app.model.content_dto import Question


class VideoContentLLMResponseList(BaseModel):
    video_content: List[str]


class QuestionResponse(BaseModel):
    question: List[Question]