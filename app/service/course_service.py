import asyncio
import logging
import os
import uuid
from typing import List

from dotenv import load_dotenv

from app.client.llm_client import OpenAITextProcessor
from app.model.processing_models import ProcessedParagraph, SimplifyResults, QuizResults
from app.schema.video_schema import VideoRequestSchema

# Load environment variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the LLM client
llm_client = OpenAITextProcessor(os.getenv(" "), model="gpt-4o", max_workers=5)


async def get_paragraph(video: VideoRequestSchema) -> List[ProcessedParagraph]:
    try:
        logger.info("Generating paragraphs from video...")
        response = await asyncio.to_thread(llm_client.get_paragraph,
                                           objective=video.objective,
                                           skills=video.skills,
                                           video=video.video)
        logger.info(f"Received {len(response.paragraph)} paragraphs.")

        paragraph_with_id = [
            ProcessedParagraph(
                video_id=str(video.video_id),
                paragraph=p.paragraph,
                paragraph_level=p.paragraph_level,
                start_word=p.start_word,
                end_word=p.end_word,
                paragraph_id=str(uuid.uuid4()),
                objective=[p.related_objectives],
                skills=[p.related_skills],
                language=video.language,
            )
            for p in response.paragraph
        ]

        return paragraph_with_id
    except Exception as e:
        logger.exception("Error while generating paragraphs")
        raise e


async def simplify_paragraph_v1(paragraphs: List[ProcessedParagraph]) -> List[SimplifyResults]:
    logger.info("Starting paragraph simplification...")

    async def simplify_single(paragraph: ProcessedParagraph) -> SimplifyResults:
        try:
            result = await asyncio.to_thread(llm_client.simplify, paragraph=paragraph.paragraph,
                                             language=paragraph.language)
            return SimplifyResults(
                video_id=paragraph.video_id,
                paragraph=paragraph.paragraph,
                paragraph_level=paragraph.paragraph_level,
                start_word=paragraph.start_word,
                end_word=paragraph.end_word,
                paragraph_id=paragraph.paragraph_id,
                simplify1=result.simplify1,
                simplify1_id=str(uuid.uuid4()),
                simplify1_first_word=result.simplify1_first_word,
                simplify1_last_word=result.simplify1_last_word,
                simplify2=result.simplify2,
                simplify2_id=str(uuid.uuid4()),
                simplify2_first_word=result.simplify2_first_word,
                simplify2_last_word=result.simplify2_last_word,
                simplify3=result.simplify3,
                simplify3_id=str(uuid.uuid4()),
                simplify3_first_word=result.simplify3_first_word,
                simplify3_last_word=result.simplify3_last_word,
                skills=paragraph.skills,
                objective=paragraph.objective,
                language=paragraph.language,
            )
        except Exception as e:
            logger.exception(f"Error simplifying paragraph {paragraph.paragraph_id}")
            raise e

    results = await asyncio.gather(*(simplify_single(p) for p in paragraphs))
    logger.info(f"Simplified {len(results)} paragraphs.")
    return results


async def generate_quiz(paragraphs: List[SimplifyResults]) -> List[QuizResults]:
    logger.info("Starting quiz generation...")

    async def generate_single(paragraph: SimplifyResults) -> QuizResults:
        try:
            result = await asyncio.to_thread(llm_client.generate_quiz,
                                             skills=paragraph.skills,
                                             objective=paragraph.objective,
                                             paragraph_content=paragraph.paragraph,
                                             language=paragraph.language)
            return QuizResults(
                video_id=paragraph.video_id,
                paragraph=paragraph.paragraph,
                paragraph_level=paragraph.paragraph_level,
                start_word=paragraph.start_word,
                end_word=paragraph.end_word,
                paragraph_id=paragraph.paragraph_id,
                simplify1=paragraph.simplify1,
                simplify1_id=paragraph.simplify1_id,
                simplify1_first_word=paragraph.simplify1_first_word,
                simplify1_last_word=paragraph.simplify1_last_word,
                simplify2=paragraph.simplify2,
                simplify2_id=paragraph.simplify2_id,
                simplify2_first_word=paragraph.simplify2_first_word,
                simplify2_last_word=paragraph.simplify2_last_word,
                simplify3=paragraph.simplify3,
                simplify3_id=paragraph.simplify3_id,
                simplify3_first_word=paragraph.simplify3_first_word,
                simplify3_last_word=paragraph.simplify3_last_word,
                quiz=result.quiz,
                skills=paragraph.skills,
                objective=paragraph.objective,
                language=paragraph.language
            )
        except Exception as e:
            logger.exception(f"Error generating quiz for paragraph {paragraph.paragraph_id}")
            raise e

    results = await asyncio.gather(*(generate_single(p) for p in paragraphs))
    logger.info(f"Generated quizzes for {len(results)} paragraphs.")
    return results
