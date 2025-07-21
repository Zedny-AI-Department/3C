from typing import List

from fastapi import APIRouter, HTTPException

from app.model.processing_models import QuizResults
from app.model.translate_video_metadata import CourseWrapper
from app.schema.video_schema import VideoRequestSchema
from app.service.course_service import generate_quiz, get_paragraph, simplify_paragraph_v1
from app.service.translate_service import translate_video, translate_course_meta_data

ai_course_processing_router = APIRouter()


# List[QuizResults]

@ai_course_processing_router.post("/process_video")
async def process_video(process_video_request: VideoRequestSchema):
    try:
        # Generate paragraph
        paragraph_list = await get_paragraph(process_video_request)
        simplify = await simplify_paragraph_v1(paragraph_list)
        quiz = await generate_quiz(simplify)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_course_processing_router.post("/translate_video/{language}")
async def translate_script(process_video_request: List[QuizResults], language: str) -> List[QuizResults]:
    try:
        paragraph_list = await translate_video(process_video_request, language)
        return paragraph_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_course_processing_router.post("/translate_course_meta/{language}")
async def translate_course_meta(process_video_request: CourseWrapper, language: str) -> CourseWrapper:
    try:
        paragraph_list = await translate_course_meta_data(process_video_request, language)
        return paragraph_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
