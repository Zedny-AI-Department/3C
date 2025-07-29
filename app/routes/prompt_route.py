from fastapi import APIRouter

from app.model.prompt_dto import PromptDTO
from app.container import prompt_controller

prompt_router = APIRouter()


@prompt_router.post("")
def upload_prompt(prompt_request: PromptDTO):
    prompt_id = prompt_controller.process_prompt(
        prompt=prompt_request,
    )
    return {"prompt_id": str(prompt_id)}


@prompt_router.get("/all")
def get_all_prompts():
    """
    Get all prompts from the knowledge base.
    """
    try:
        prompts = prompt_controller.get_all_prompts()
        return {"prompts": prompts}
    except Exception as e:
        return {"error": str(e)}


@prompt_router.post("/{prompt_id}")
def get_prompt(prompt_id: str):
    """
    Get a specific prompt by its ID.
    """
    try:
        prompt = prompt_controller.get_prompt(prompt_id=prompt_id)
        return {"prompt": prompt}
    except Exception as e:
        return {"error": str(e)}
