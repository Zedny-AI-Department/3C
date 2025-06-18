from typing import List

from pydantic import BaseModel, Field

from model.content_dto import Question


class VideoContentLLMResponseList(BaseModel):
    video_content: List[str]


class QuestionResponse(BaseModel):
    question: List[Question]