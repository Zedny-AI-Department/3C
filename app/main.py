from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.ai_course_processing import ai_course_processing_router
from app.routes.course_generation import course_generation_router
from app.routes.prompt_route import prompt_router
from app.routes.upload_attachment import upload_attachment_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(course_generation_router, prefix="/v1/course-generation", tags=["Course Generation"])
app.include_router(upload_attachment_router, prefix="/v1/upload", tags=["Upload Attachment"])
app.include_router(prompt_router, prefix="/v1/prompt", tags=["Prompt Management"])
app.include_router(ai_course_processing_router, prefix="/v1/ai-course-processing", tags=["AI Course Processing"])