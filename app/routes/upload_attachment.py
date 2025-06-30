from typing import List

from fastapi import APIRouter, UploadFile, File, Form

from app.controller.course_attachment_controller import upload_file

upload_attachment_router = APIRouter()


@upload_attachment_router.post("/upload/course-files")
async def upload_course_files(files: List[UploadFile] = File(...),
                              source_name: str = Form(...)):
    """
    Upload multiple course files and extract text from them.
    """
    results = await upload_file(files=files,
                                source_name=source_name)
    return results
