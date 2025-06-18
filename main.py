from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from constant_manager import course_outline_prompt
from controller import generate_course_outline, generate_course_content, generate_course_quiz
from model.content_dto import CourseOutLines, CourseScript, CourseScriptWithQuiz
from request_schema.course_content_request import CourseOutlineRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate-course-outlines")
def generate_course_outlines(outline_request: CourseOutlineRequest) -> CourseOutLines:
    try:
        return generate_course_outline(outline_request=outline_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/outlines-prompt")
def get_outlines_prompt():
    try:
        return course_outline_prompt,
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-course-content")
def course_content(outline_request: CourseOutLines) -> CourseScript:
    try:
        return generate_course_content(outline_request=outline_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-course-quiz")
def quiz_generator(course_content: CourseScript) -> CourseScriptWithQuiz:
    try:
        quiz = generate_course_quiz(course_content=course_content)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))