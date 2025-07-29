from app.knowledge_base.knowledge_base import KnowledgeBase
from app.model.prompt_dto import PromptDTO, GetPromptDTO


class PromptController:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base

    def process_prompt(self, prompt: PromptDTO):
        """
        Process the prompt and return the response.
        """
        try:
            # Use the knowledge base to process the prompt
            response = self.knowledge_base.add_prompt(
                collection_name="prompts",
                prompt_name=prompt.prompt_name,
                system_prompt=prompt.system_prompt,
                user_id=prompt.user_id,
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def get_all_prompts(self):
        """
        Get all prompts from the knowledge base.
        """
        try:
            prompt_list = []
            prompts = self.knowledge_base.get_prompts(
                collection_name="prompts"
            )
            for prompt in prompts:
                prompt_list.append(GetPromptDTO(**prompt))
            return prompt_list
        except Exception as e:
            return {"error": str(e)}

    def get_prompt(self, prompt_id: str) -> GetPromptDTO:
        """
        Get a specific prompt by its ID.
        """
        try:
            prompt = self.knowledge_base.get_prompt(
                collection_name="prompts", prompt_id=prompt_id
            )
            return GetPromptDTO(**prompt)
        except Exception as e:
            raise e
