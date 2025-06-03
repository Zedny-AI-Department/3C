import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from constant_manager import course_outline_prompt, search_prompt
from model.content_dto import CourseOutLines, VideoOutLines
from model.llm_response import VideoContentLLMResponseList
from request_schema.course_content_request import CourseOutlineRequest

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

    def generate_raw_content(self, video: VideoOutLines):
        """
        Sends a prompt to the ChatGPT model with web search options and returns the response.
        """
        try:
            result = self.client.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=search_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=
                        f"## Video Name: {video.video_name}\n"
                        f"## Video Description: {video.video_description}\n"
                        f"## Video Keywords: {', '.join(video.video_keywords) if video.video_keywords else 'Generate appropriate keywords based on video content'}\n"
                        f"## Video Skills: {', '.join(video.video_skill) if video.video_skill else 'Generate appropriate skills based on course content'}\n"
                        f"## Video Objectives: {', '.join(video.video_objective) if video.video_objective else 'Generate appropriate objectives based on course content'}\n"
                    )
                ],
            )
            print(result.choices[0].message.content)
            return result.choices[0].message.content
        except Exception as e:
            print(f"Error during web search: {str(e)}")
            return None


    def generate_video(self, course: CourseOutLines, video: VideoOutLines, raw_content: str) -> list[str]:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=""
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=""
                    )
                ],
                response_format=VideoContentLLMResponseList,
                temperature=0.1
            )
            return response.choices[0].message.parsed.video_content
        except Exception as e:
            raise e