# Course Generation API
from fastapi import APIRouter, HTTPException

from app.controller.course_generation_controller import generate_course_outline, generate_course_content, \
    generate_course_quiz, chat_with_course, add_course_to_knowledge_base
from app.model.content_dto import CourseOutLines, CourseScript, CourseScriptWithQuiz, LLMOutLines
from app.request_schema.course_content_request import CourseOutlineRequest
from app.schema.chat_request_schema import ChatRequestSchema
from app.constant_manager import course_outline_prompt

course_generation_router = APIRouter()


@course_generation_router.post("/generate-course-outlines")
def generate_course_outlines(outline_request: CourseOutlineRequest) -> LLMOutLines:
    try:
        return generate_course_outline(outline_request=outline_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_generation_router.get("/outlines-prompt")
def get_outlines_prompt():
    try:
        return course_outline_prompt,
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_generation_router.post("/generate-course-content")
def course_content(outline_request: CourseOutLines) -> CourseScript:
    try:
        return generate_course_content(outline_request=outline_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_generation_router.post("/add-course-content")
def add_course_content(course_content_request: CourseScript):
    try:
        return add_course_to_knowledge_base(course_content=course_content_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@course_generation_router.post("/generate-course-quiz")
def quiz_generator(course_content_request: CourseScript) -> CourseScriptWithQuiz:
    try:
        quiz = generate_course_quiz(course_content=course_content_request)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_generation_router.post("/chat")
def ask_video_script(chat_request: ChatRequestSchema):
    try:
        return chat_with_course(chat_request=chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
