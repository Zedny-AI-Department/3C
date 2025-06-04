from typing import List

from pydantic import BaseModel, Field


class VideoContentLLMResponseList(BaseModel):
    video_content: List[str]