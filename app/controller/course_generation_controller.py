import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.model.content_dto import CourseOutLines, VideoScript, CourseScript, ChapterScript, VideoScriptWithQuiz, \
    ChapterScriptWithQuiz, CourseScriptWithQuiz, VideoOutLines, LLMOutLines
from app.request_schema.course_content_request import CourseOutlineRequest
from app.schema.chat_request_schema import ChatRequestSchema
from app.constant_manager import course_outline_prompt_with_source, course_outline_prompt, chat_system_prompt
from app.container import knowledge_base, llm_client, prompt_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_course_outline(outline_request: CourseOutlineRequest) -> LLMOutLines:
    logger.info(f"Starting course outline generation for course: {outline_request.course_name}")
    try:
        if outline_request.source:
            result = llm_client.generate_outline(course_details=outline_request,
                                                 prompt=course_outline_prompt_with_source)
        else:
            result = llm_client.generate_outline(course_details=outline_request,
                                                 prompt=course_outline_prompt)
        logger.info(f"Successfully generated course outline with {len(result.chapters)} chapters")
        return result
    except Exception as error:
        logger.error(f"Error generating course outline: {error}")
        raise error


def get_source_raw_content(source: str, video_source_knowledge: list[str]):
    raw_content = []
    for query_text in video_source_knowledge:
        knowledge = knowledge_base.get_knowledge(collection_name=source,
                                                 query_text=query_text,
                                                 top_k=2,
                                                 score_threshold=0.5
                                                 )
        for kn in knowledge:
            raw_content.append(kn.payload['content'])
    return raw_content


def process_video(video: VideoOutLines, course_outline: CourseOutLines, system_prompt: str) -> VideoScript:
    """Process a single video with error handling and logging"""
    logger.info(f"Processing video: {video.video_name}")
    try:
        if course_outline.source:
            raw_content = get_source_raw_content(source=course_outline.source,
                                                 video_source_knowledge=video.video_source_knowledge)
        else:
            raw_content = llm_client.generate_raw_content(video=video)
            raw_content = [raw_content]
        logger.debug(f"Generated raw content for video: {video.video_name}")

        video_script = llm_client.generate_video(
            raw_content=raw_content,
            course=course_outline,
            video=video,
            prompt=system_prompt
        )
        logger.debug(f"Generated video script for video: {video.video_name}")

        processed_video = VideoScript(
            video_name=video.video_name,
            previous_video_name=video.previous_video_name,
            video_description=video.video_description,
            video_source_knowledge=video.video_source_knowledge,
            video_script=video_script,
            raw_content=raw_content,
            video_skill=video.video_skill,
            video_objective=video.video_objective,
            video_duration=video.video_duration
        )
        logger.info(f"Successfully processed video: {video.video_name}")
        return processed_video
    except Exception as error:
        logger.error(f"Error processing video {video.video_name}: {error}")
        raise error


def generate_course_content(outline_request: CourseOutLines, max_workers: int = 10) -> CourseScript:
    logger.info(f"Starting course content generation for: {outline_request.course_name}")
    logger.info(f"Total chapters to process: {len(outline_request.chapters)}")

    try:
        chapter_list = []
        if outline_request.prompt_id:
            system_prompt = prompt_controller.get_prompt(outline_request.prompt_id).system_prompt
        else:
            system_prompt = course_outline_prompt

        for chapter_idx, chapter in enumerate(outline_request.chapters, 1):
            logger.info(f"Processing chapter {chapter_idx}/{len(outline_request.chapters)}: {chapter.chapter_name}")
            logger.info(f"Videos in chapter: {len(chapter.videos)}")

            video_list = []

            # Process videos in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create LLM client instances for each thread
                future_to_video = {}

                for video in chapter.videos:
                    future = executor.submit(process_video, video, outline_request,
                                             system_prompt)
                    future_to_video[future] = video

                # Collect results as they complete
                for future in as_completed(future_to_video):
                    video = future_to_video[future]
                    try:
                        processed_video = future.result()
                        video_list.append(processed_video)
                        logger.info(f"Completed processing video: {video.video_name}")
                    except Exception as error:
                        logger.error(f"Failed to process video {video.video_name}: {error}")
                        raise error

            # Sort videos to maintain original order if needed
            # Assuming videos have some ordering attribute, or you want to maintain input order
            video_list.sort(key=lambda v: next(i for i, orig_video in enumerate(chapter.videos)
                                               if orig_video.video_name == v.video_name))

            chapter_script = ChapterScript(
                chapter_name=chapter.chapter_name,
                videos=video_list
            )
            chapter_list.append(chapter_script)
            logger.info(f"Completed chapter: {chapter.chapter_name} with {len(video_list)} videos")

        course_script = CourseScript(
            language=outline_request.language,
            country=outline_request.country,
            source=outline_request.source,
            course_name=outline_request.course_name,
            course_description=outline_request.course_description,
            target_audience=outline_request.target_audience,
            course_level=outline_request.course_level,
            course_slogan=outline_request.course_slogan,
            course_skills=outline_request.course_skills,
            course_objectives=outline_request.course_objectives,
            chapters=chapter_list
        )

        total_videos = sum(len(chapter.videos) for chapter in chapter_list)
        logger.info(
            f"Successfully generated complete course content with {len(chapter_list)} chapters and {total_videos} videos")
        return course_script

    except Exception as error:
        logger.error(f"Error generating course content: {error}")
        raise error


def add_course_to_knowledge_base(course_content: CourseScript):
    """
    Add the course content to the knowledge base.
    This function is called after the course content is generated.
    """
    try:
        knowledge_base.add_course(course_data=course_content)
        logger.info(f"The course {course_content.course_name} has been added to the knowledge base")
        return "Course content added successfully"
    except Exception as error:
        logger.error(f"Error adding course to knowledge base: {error}")
        raise error

def generate_course_quiz(course_content: CourseScript) -> CourseScriptWithQuiz:
    try:
        chapter_list = []
        chapter_count = len(course_content.chapters)

        for chapter_index, chapter in enumerate(course_content.chapters):
            video_list = []
            video_count = len(chapter.videos)

            # Avoid division by zero
            if video_count == 0:
                continue

            question_per_video = (chapter_count * 20) // video_count

            for video_index, video in enumerate(chapter.videos):
                # Skip the first video in the first chapter (Introduction)
                if chapter_index == 0 and video_index == 0:
                    video_script = None
                    video_quiz = None

                # Skip the last video in the last chapter (Conclusion)
                elif chapter_index == chapter_count - 1 and video_index == len(chapter.videos) - 1:
                    video_script = None
                    video_quiz = None

                else:
                    quiz = llm_client.generate_quiz_3c(
                        video_content=video.video_script,
                        course_name=course_content.course_name,
                        video_name=video.video_name,
                        skill=video.video_skill,
                        objective=video.video_objective,
                        question_per_video=question_per_video
                    )
                    video_script = quiz['content_with_question_list']
                    video_quiz = quiz['video_quiz']

                video_with_quiz = VideoScriptWithQuiz(
                    video_name=video.video_name,
                    previous_video_name=video.previous_video_name,
                    video_description=video.video_description,
                    video_source_knowledge=video.video_source_knowledge,
                    video_script=video_script,
                    video_skill=video.video_skill,
                    video_objective=video.video_objective,
                    video_duration=video.video_duration,
                    VideoQuiz=video_quiz
                )
                video_list.append(video_with_quiz)

            chapter_with_quiz = ChapterScriptWithQuiz(
                chapter_name=chapter.chapter_name,
                videos=video_list
            )
            chapter_list.append(chapter_with_quiz)

        course_with_quiz = CourseScriptWithQuiz(
            country=course_content.country,
            source=course_content.source,
            course_name=course_content.course_name,
            course_description=course_content.course_description,
            target_audience=course_content.target_audience,
            course_level=course_content.course_level,
            course_slogan=course_content.course_slogan,
            course_skills=course_content.course_skills,
            course_objectives=course_content.course_objectives,
            chapters=chapter_list
        )
        logger.info("Successfully generated course quiz")
        return course_with_quiz

    except Exception as error:
        logger.error(f"Error generating course quiz: {error}")
        raise error


def chat_with_course(chat_request: ChatRequestSchema):
    try:
        messages = [{
            "role": "system",
            "content": chat_system_prompt
        }]

        chat_id = chat_request.chat_id
        search_query = chat_request.query
        if chat_id:
            history = knowledge_base.get_messages(chat_id)
            if history:
                messages.extend(history[-4:])
                # Extract last two user messages from history
                user_msgs = [msg['content'] for msg in history if msg['role'] == 'user']
                last_two = user_msgs[-2:] if len(user_msgs) >= 2 else user_msgs
                # Merge last two with current query
                search_query = "\n".join(last_two + [chat_request.query])
        else:
            chat_id = str(knowledge_base.add_chat())
            logger.info(f"New chat started with ID: {chat_id}")

        if chat_request.video_id:
            knowledge = knowledge_base.ask_video(
                query_text=search_query,
                video_id=chat_request.video_id)

        elif chat_request.chapter_id:
            knowledge = knowledge_base.ask_chapter(
                query_text=search_query,
                chapter_id=chat_request.chapter_id)
        else:
            knowledge = knowledge_base.ask_course(
                query_text=search_query,
                course_id=chat_request.course_id)

        user_query = {
            "role": "user",
            "content": f"##Knowledge: {knowledge.context}\n\n##User Query: {chat_request.query}"
        }
        messages.append(user_query)

        answer = llm_client.chat(messages=messages, temperature=chat_request.temperature)
        now = datetime.now().isoformat()
        knowledge_base.add_message(chat_id=chat_id,
                                   message={"role": "user", "content": chat_request.query, "time": now})
        knowledge_base.add_message(chat_id=chat_id, message={"role": "assistant", "content": answer, "time": now})

        return {
            "messages": messages,
            "chat_id": chat_id,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"Error in chat_with_course: {e}")
        raise e
