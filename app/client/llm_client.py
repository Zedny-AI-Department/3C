import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.model.content_dto import CourseOutLines, VideoOutLines, ContentWithQuiz
from app.model.llm_response import VideoContentLLMResponseList, QuestionResponse
from app.request_schema.course_content_request import CourseOutlineRequest
from constant_manager import search_prompt, script_generator_prompt, generate_question_prompt, \
    final_question_prompt

load_dotenv()


class OpenAITextProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", max_workers: int = 5):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate_outline(self, course_details: CourseOutlineRequest, prompt: str) -> CourseOutLines:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=
                        f"Create a professional course outline with the following specifications:\n\n"
                        f"**Country**: {course_details.country}\n"
                        f"**Source**: {course_details.source}\n"
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
                        f"Generate the outlines in {course_details.language} language"
                    )
                ],
                response_format=CourseOutLines,
                temperature=0.3
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
                        f"## Video Keywords: {', '.join(video.video_source_knowledge) if video.video_source_knowledge else 'Generate appropriate keywords based on video content'}\n"
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

    def generate_video(self, course: CourseOutLines, video: VideoOutLines, raw_content: List[str]) -> list[str]:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=script_generator_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=
                        f"Create a professional video script with the following specifications:\n\n"
                        f"**Country**: {course.country}\n"
                        f"**Course Topic**: {course.course_name}\n"
                        f"**Course Description Context**: {course.course_description}\n"
                        f"**Target Audience**: {course.target_audience}\n"
                        f"**Course Level**: {course.course_level}\n"
                        f"**Previous Video Name**: {video.previous_video_name}"
                        f"**Video Name**: {video.video_name}\n"
                        f"**Video Description**: {video.video_description}\n"
                        f"**Video Objectives**: {', '.join(video.video_objective) if video.video_objective else 'This may be the introduction or conclusion video, so no specific objectives'}\n"
                        f"**Video Skills**: {', '.join(video.video_skill) if video.video_skill else 'This may be the introduction or conclusion video, so no specific skills'}\n"
                        f"**Video Duration Range**: {video.video_duration} words\n"
                        f"Use the following raw content as a reference:\n{str(raw_content)}"
                        f"Generate the script in {course.language} language"
                    )
                ],
                response_format=VideoContentLLMResponseList,
                temperature=0.3
            )
            return response.choices[0].message.parsed.video_content
        except Exception as e:
            raise e

    def generate_quiz(self, video_content: list[str], course_name: str,
                      video_name: str, skill: str, objective: str,
                      question_per_video: int) -> dict:
        try:
            def generate_question(i, content):
                if i == 0 or i == len(video_content) - 1:
                    return ContentWithQuiz(paragraph=content, question=None)

                paragraph_question = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        ChatCompletionSystemMessageParam(
                            role="system",
                            content=generate_question_prompt
                        ),
                        ChatCompletionUserMessageParam(
                            role="user",
                            content=f"## Course Name: {course_name}\n"
                                    f"## Video Name: {video_name}\n"
                                    f"## Skill: {skill}\n"
                                    f"## Objective: {objective}\n"
                                    f"## Paragraph Content: {content}\n"
                                    f"Generate a quiz question based on the above paragraph content.\n"
                        )
                    ],
                    response_format=QuestionResponse,
                    temperature=0.3
                )

                return ContentWithQuiz(
                    paragraph=content,
                    question=paragraph_question.choices[0].message.parsed.question
                )

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(generate_question, i, content): i for i, content in enumerate(video_content)}
                results = [None] * len(video_content)
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        print(f"Error generating question for paragraph {i}: {e}")
                        results[i] = ContentWithQuiz(paragraph=video_content[i], question=None)
            video_quiz = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=final_question_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"## Course Name: {course_name}\n"
                                f"## Video Name: {video_name}\n"
                                f"## Skill: {skill}\n"
                                f"## Objective: {objective}\n"
                                f"## Video Script: {str(video_content)}\n"
                                f"Generate exactly **{question_per_video}** questions based on the video script content.\n"
                    )
                ],
                response_format=QuestionResponse,
                temperature=0.3
            )

            return {
                "content_with_question_list": results,
                "video_quiz": video_quiz.choices[0].message.parsed.question
            }

        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            raise e

    def chat(self, messages: List, model: str = "gpt-4o",
             temperature: float = 0.7) -> str:
        try:
            response = self.client.responses.create(
                model=model,
                input=messages,
                temperature=temperature,
            )
            return response.output_text
        except Exception as e:
            print(f"Error during chat: {str(e)}")
            raise e
