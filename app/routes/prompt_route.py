from fastapi import APIRouter

from app.model.prompt_dto import PromptDTO, GetPromptDTO
from app.container import prompt_controller

prompt_router = APIRouter()


@prompt_router.post("")
def upload_prompt(prompt_request: PromptDTO):
    prompt_id = prompt_controller.process_prompt(
        prompt=prompt_request,
    )
    return {"prompt_id": str(prompt_id)}


@prompt_router.get("/all")
def get_all_prompts() -> dict[str, list[GetPromptDTO]]:
    """
    Get all prompts from the knowledge base.
    """
    try:
        prompts = prompt_controller.get_all_prompts()
        return {"prompts": prompts}
    except Exception as e:
        raise e


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


@prompt_router.delete("/{prompt_id}")
def delete_prompt(prompt_id: str):
    """
    Delete a specific prompt by its ID.
    """
    try:
        prompt_controller.delete_prompt(prompt_id=prompt_id)
        return {"message": "Prompt deleted successfully"}
    except Exception as e:
        return {"error": str(e)}


@prompt_router.put("/{prompt_id}")
def update_prompt(prompt_id: str, prompt_request: PromptDTO):
    """
    Update a specific prompt by its ID.
    """
    try:
        return prompt_controller.update_prompt(
            prompt_id=prompt_id,
            update_data=prompt_request
        )
    except Exception as e:
        return {"error": str(e)}