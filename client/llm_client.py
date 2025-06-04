import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from constant_manager import course_outline_prompt
from model.content_dto import CourseOutLines
from request_schema.course_content_request import CourseOutlineRequest
from dotenv import load_dotenv

load_dotenv()


class OpenAITextProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", max_workers: int = 5):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate_outline(self, course_details: CourseOutlineRequest) -> CourseOutLines:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=course_outline_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=
                        f"Create a professional course outline with the following specifications:\n\n"
                        f"**Country**: {course_details.country}\n"
                        f"**Course Topic**: {course_details.course_name}\n"
                        f"**Course Description Context**: {course_details.brief}\n"
                        f"**Target Audience**: {course_details.target_audience}\n"
                        f"**Course Level**: {course_details.course_level}\n"
                        f"**Required Chapters**: {course_details.chapter_count}\n"
                        f"**Total Videos**: {course_details.video_count} (including introduction and conclusion)\n"
                        f"**Video Duration Range**: {course_details.min_words_per_video}-{course_details.max_words_per_video} words per video (except intro/conclusion which should be 150 words)\n"
                        f"**Target Skills**: {', '.join(course_details.skills) if course_details.skills else 'Generate appropriate skills based on course content'}\n\n"
                        f"Distribute the {course_details.video_count} videos across {course_details.chapter_count} chapters, "
                        f"with the first video being an introduction and the last video being a conclusion."
                    )
                ],
                response_format=CourseOutLines,
                temperature=0.1
            )
            return response.choices[0].message.parsed
        except Exception as e:
            # More specific error handling
            print(f"Error generating course outline: {str(e)}")
            raise e
