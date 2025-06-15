from client.llm_client import OpenAITextProcessor
from model.content_dto import CourseOutLines, VideoScript, CourseScript, ChapterScript
from request_schema.course_content_request import CourseOutlineRequest


def generate_course_outline(outline_request: CourseOutlineRequest) -> CourseOutLines:
    try:
        llm_client = OpenAITextProcessor()
        return llm_client.generate_outline(outline_request)
    except Exception as error:
        print(f"An error occurred: {error}")
        raise error


def generate_course_content(outline_request: CourseOutLines):
    try:
        video_list = []
        chapter_list = []
        llm_client = OpenAITextProcessor()
        for chapter in outline_request.chapters:
            for video in chapter.videos:
                raw_content = llm_client.generate_raw_content(video=video)
                video_script = llm_client.generate_video(
                    raw_content=raw_content,
                    course=outline_request,
                    video=video,
                )
                video = VideoScript(
                    video_name=video.video_name,
                    previous_video_name=video.previous_video_name,
                    video_description=video.video_description,
                    video_keywords=video.video_keywords,
                    video_script=video_script,
                    raw_content=raw_content,
                    video_skill=video.video_skill,
                    video_objective=video.video_objective,
                    video_duration=video.video_duration
                )
                video_list.append(video)
            chapter = ChapterScript(
                chapter_name=chapter.chapter_name,
                videos=video_list
            )
            chapter_list.append(chapter)
        course_script = CourseScript(
            country=outline_request.country,
            course_name=outline_request.course_name,
            course_description=outline_request.course_description,
            target_audience=outline_request.target_audience,
            course_level=outline_request.course_level,
            course_slogan=outline_request.course_slogan,
            course_skills=outline_request.course_skills,
            course_objectives=outline_request.course_objectives,
            chapters=chapter_list
        )
        return course_script
    except Exception as error:
        print(f"An error occurred: {error}")
        raise error
