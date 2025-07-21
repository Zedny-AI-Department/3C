import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import List
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.constant_manager import paragraph_generator, simplify_prompt, question_generation_prompt, paragraph_level, \
    EMBEDDING_MODEL, quiz_note, translate_quiz_prompt, translate_content, translate_video_metadata
from app.constant_manager import search_prompt, script_generator_prompt, generate_question_prompt, \
    final_question_prompt, intro_script_prompt
from app.model.content_dto import CourseOutLines, VideoOutLines, ContentWithQuiz, LLMOutLines
from app.model.llm_response import VideoContentLLMResponseList, QuestionResponse
from app.model.llm_response_model import ParagraphResponse, SimplifyResponse, QuizResponse
from app.model.processing_models import SimplifyResults, TranslateP1Response, TranslateP2Response
from app.model.translate_video_metadata import CourseWrapper, Chapter
from app.request_schema.course_content_request import CourseOutlineRequest

load_dotenv()


class OpenAITextProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", max_workers: int = 5):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate_outline(self, course_details: CourseOutlineRequest, prompt: str) -> LLMOutLines:
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
                        f"**Video Duration Range**: from {course_details.min_words_per_video} to {course_details.max_words_per_video} words per video (except intro/conclusion which should be 150 words)\n"
                        f"**Target Skills**: {', '.join(course_details.skills) if course_details.skills else 'Generate appropriate skills based on course content'}\n\n"
                        f"Distribute the {course_details.video_count} videos across {course_details.chapter_count} chapters, "
                        f"with the first video being an introduction and the last video being a conclusion."
                        f"Generate the outlines in {course_details.language} language"
                    )
                ],
                response_format=LLMOutLines,
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
            return result.choices[0].message.content
        except Exception as e:
            print(f"Error during web search: {str(e)}")
            return None

    def generate_video(self, course: CourseOutLines, video: VideoOutLines,
                       raw_content: List[str], prompt: str = script_generator_prompt) -> list[str]:
        try:
            if not video.previous_video_name:
                prompt = intro_script_prompt
            else:
                prompt = prompt
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

    def generate_quiz_3c(self, video_content: list[str], course_name: str,
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

    def get_embed(self, arabic_text: str):
        embed = self.client.embeddings.create(
            input=arabic_text,
            model=EMBEDDING_MODEL
        )

        return embed.data[0].embedding

    def get_paragraph(self, video: str, objective: list, skills: list) -> ParagraphResponse | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=paragraph_generator
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"##Script: {video}\n"
                                f"##Paragraph Level: {paragraph_level}\n"
                                f"##Objectives: {objective}\n"
                                f"##Skills: {skills}\n##\n"
                    )
                ],
                temperature=0,
                response_format=ParagraphResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def simplify(self, paragraph: str, language: str) -> SimplifyResponse | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=simplify_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"##Script: {paragraph}\n##\n##Answer in {language} language:\n##\n"
                    )
                ],
                temperature=0,
                response_format=SimplifyResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_quiz(self, quiz, language: str) -> QuizResponse:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_quiz_prompt.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=quiz
                    )
                ],
                temperature=0,
                response_format=QuizResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_content(self, video_data, language: str) -> SimplifyResults | None:
        try:
            p1_translate = {
                "video_id": video_data['video_id'],
                "objective": video_data['objective'],
                "language": language,
                "paragraph_id": video_data['paragraph_id'],
                "paragraph": video_data['paragraph'],
                "paragraph_level": video_data['paragraph_level'],
                "start_word": video_data['start_word'],
                "end_word": video_data['end_word'],
                "skills": video_data['skills'],
                "simplify1_id": video_data['simplify1_id'],
                "simplify1": video_data['simplify1'],
                "simplify1_first_word": video_data['simplify1_first_word'],
                "simplify1_last_word": video_data['simplify1_last_word']
            }
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_content.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(p1_translate)
                    )
                ],
                temperature=0,
                response_format=TranslateP1Response,
                timeout=600
            )

            # Extract the translated content from the response
            p1_translate_response = response.choices[0].message.parsed

            p2_translate = {
                "simplify2_id": video_data['simplify2_id'],
                "simplify2": video_data['simplify2'],
                "simplify2_first_word": video_data['simplify2_first_word'],
                "simplify2_last_word": video_data['simplify2_last_word'],
                "simplify3_id": video_data['simplify3_id'],
                "simplify3": video_data['simplify3'],
                "simplify3_first_word": video_data['simplify3_first_word'],
                "simplify3_last_word": video_data['simplify3_last_word']
            }
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_content.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(p2_translate)
                    )
                ],
                temperature=0,
                response_format=TranslateP2Response,
                timeout=600
            )
            p2_translate_response = response.choices[0].message.parsed
            return SimplifyResults(
                video_id=p1_translate_response.video_id,
                objective=p1_translate_response.objective,
                language=language,
                paragraph_id=p1_translate_response.paragraph_id,
                paragraph=p1_translate_response.paragraph,
                paragraph_level=p1_translate_response.paragraph_level,
                start_word=p1_translate_response.start_word,
                end_word=p1_translate_response.end_word,
                skills=p1_translate_response.skills,
                simplify1_id=p1_translate_response.simplify1_id,
                simplify1=p1_translate_response.simplify1,
                simplify1_first_word=p1_translate_response.simplify1_first_word,
                simplify1_last_word=p1_translate_response.simplify1_last_word,
                simplify2_id=p2_translate_response.simplify2_id,
                simplify2=p2_translate_response.simplify2,
                simplify2_first_word=p2_translate_response.simplify2_first_word,
                simplify2_last_word=p2_translate_response.simplify2_last_word,
                simplify3_id=p2_translate_response.simplify3_id,
                simplify3=p2_translate_response.simplify3,
                simplify3_first_word=p2_translate_response.simplify3_first_word,
                simplify3_last_word=p2_translate_response.simplify3_last_word
            )
        except Exception as e:
            raise e

    def translate_chapter_meta(self, chapter_data: Chapter, language: str) -> Chapter:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_video_metadata.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(chapter_data)
                    )
                ],
                temperature=0,
                response_format=Chapter,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_text(self, text: str, language: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Translate the following text to {language}."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise e

    def translate_video_meta(self, video_data, language: str) -> CourseWrapper | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_video_metadata.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(video_data)
                    )
                ],
                temperature=0,
                response_format=CourseWrapper,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def generate_quiz(self, paragraph_content, skills: list, objective: list, language: str) -> QuizResponse:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=question_generation_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"{quiz_note}\n"
                                f"##Script: {paragraph_content}\n"
                                f"##Skills: {skills}\n##Objectives: {objective}\n##\n"
                                f"##Answer in {language} language:\n##\n"
                    )
                ],
                temperature=0,
                response_format=QuizResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e
