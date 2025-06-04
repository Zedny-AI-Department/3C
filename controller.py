from client.llm_client import OpenAITextProcessor
from request_schema.course_content_request import CourseOutlineRequest


def generate_course_outline(outline_request: CourseOutlineRequest):
    try:
        llm_client = OpenAITextProcessor()
        return llm_client.generate_outline(outline_request)
    except Exception as error:
        print(f"An error occurred: {error}")
        raise error
