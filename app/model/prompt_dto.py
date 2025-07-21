from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from pyobjectID import PyObjectId, MongoObjectId


class PromptDTO(BaseModel):
    prompt_name: str = Field(..., description="Name of the prompt")
    system_prompt: str = Field(..., description="Content of the prompt")
    user_id: Optional[PyObjectId] = Field(None, description="Creation timestamp of the prompt")


class GetPromptDTO(PromptDTO):
    id: MongoObjectId = Field(..., description="Unique identifier for the prompt", alias="_id")
    created_at: datetime = Field(..., description="Creation timestamp of the prompt")
    updated_at: datetime = Field(..., description="Last update timestamp of the prompt")
