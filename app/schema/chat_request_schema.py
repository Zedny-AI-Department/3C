from typing import Optional

from pydantic import BaseModel, Field


class ChatRequestSchema(BaseModel):
    query: str = Field(..., description="Query string")
    chat_id: Optional[str] = Field(None, description="Conversation ID")
    video_id: Optional[str] = Field(None, description="Video ID for context")
    chapter_id: Optional[str] = Field(None, description="Chapter ID for context")
    course_id: Optional[str] = Field(None, description="Course ID for context")
    temperature: Optional[float] = Field(0.3, description="Temperature for the response generation, default is 0.7")
