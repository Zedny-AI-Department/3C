from collections import defaultdict
from datetime import datetime
from typing import Optional, Any
from bson import ObjectId
from pyobjectID import PyObjectId

from app.knowledge_base.chat_controller.chat_database import ChatDatabase
from app.knowledge_base.vector_database.vector_database import VectorDatabase
from app.knowledge_base.vector_embedding.vector_embedding import VectorEmbedding
from app.model.content_dto import CourseScript
from app.model.course_knowledge import CourseKnowledge


class KnowledgeBase:
    def __init__(self, vector_embeddings: VectorEmbedding,
                 vector_database: VectorDatabase,
                 chat_database: Optional[ChatDatabase] = None):
        """Initialize the KnowledgeBase with vector embeddings and a vector database."""
        self.vector_embeddings = vector_embeddings
        self.vector_database = vector_database
        self.chat_database = chat_database

    def add_knowledge(self, query_text: str, collection_name: str, payload: dict):
        """
        Add knowledge to the knowledge base by embedding the query text and storing it in the vector database.
        """
        try:
            vector = self.vector_embeddings.embed(query_text)
            self.vector_database.insert_item(collection_name=collection_name, vector=vector, metadata=payload)
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            raise e

    def get_knowledge(self, collection_name: str, query_text: str,
                      top_k: int = 10, score_threshold: float = None,
                      filter_key: str = None,
                      filter_value: str = None
                      ):
        try:
            query_vector = self.vector_embeddings.embed(query_text)
            results = self.vector_database.vector_search(collection_name=collection_name,
                                                         query_vector=query_vector,
                                                         top_k=top_k,
                                                         score_threshold=score_threshold,
                                                         filter_key=filter_key,
                                                         filter_value=filter_value)
            return results
        except Exception as e:
            print(f"Error retrieving knowledge: {e}")
            raise e

    def add_chat(self, chat_data: dict = None) -> str:
        """
        Add a chat to the chat database.
        """
        try:
            if self.chat_database:
                result = self.chat_database.add_chat(chat_data)
                return result['inserted_id'] if 'inserted_id' in result else result
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error adding chat: {e}")
            raise e

    def get_messages(self, chat_id: str, limit: int = 100) -> list[Any]:
        """
        Retrieve messages from the chat database.
        """
        try:
            messages_list = []
            if self.chat_database:
                messages = self.chat_database.get_messages(chat_id, limit)
                for message in messages:
                    messages_list.append({
                        "role": message["role"],
                        "content": message["content"],
                    })
                return messages_list
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            raise e

    def add_message(self, chat_id: str, message: dict):
        """
        Add a message to the chat database.
        """
        try:
            if self.chat_database:
                self.chat_database.add_message(chat_id, message)
            else:
                raise ValueError("Chat database is not initialized.")
        except Exception as e:
            print(f"Error adding message: {e}")
            raise e

    def check_collection(self, collection_name: str):
        is_exist = self.vector_database.check_collection(collection_name=collection_name)
        if is_exist:
            return True
        else:
            return False

    def create_collection(self, collection_name: str):
        self.vector_database.create_collection(collection_name=collection_name)

    def get_all_collections(self) -> list[str]:
        """
        Get a list of all collections in the vector database.
        """
        try:
            return self.vector_database.get_all_collections()
        except Exception as e:
            print(f"Error retrieving collections: {e}")
            raise e

    def add_course(self, course_data: CourseScript) -> dict:
        # 1️⃣ Insert course
        course_doc = {
            "course_name": course_data.course_name,
            "course_description": course_data.course_description,
            "course_level": course_data.course_level,
            "course_slogan": course_data.course_slogan,
            "course_skills": course_data.course_skills,
            "course_objectives": course_data.course_objectives,
            "target_audience": course_data.target_audience,
            "country": course_data.country,
            "source": course_data.source,
            "language": course_data.language,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        course_id = self.chat_database.add_document(
            collection_name="course",
            document=course_doc
        )

        chapter_ids = []
        video_ids = []
        paragraph_ids = []

        for chapter_index, chapter in enumerate(course_data.chapters, start=1):
            # 2️⃣ Insert chapter
            chapter_doc = {
                "course_id": str(course_id),
                "chapter_name": chapter.chapter_name,
                "index": chapter_index,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            chapter_id = self.chat_database.add_document(
                collection_name="chapter",
                document=chapter_doc
            )
            chapter_ids.append(str(chapter_id))

            for video_index, video in enumerate(chapter.videos, start=1):
                # 3️⃣ Insert video
                video_doc = {
                    "chapter_id": str(chapter_id),
                    "video_name": video.video_name,
                    "previous_video_name": video.previous_video_name,
                    "video_source_knowledge": video.video_source_knowledge,
                    "video_description": video.video_description,
                    "video_skill": video.video_skill,
                    "video_objective": video.video_objective,
                    "video_duration": video.video_duration,
                    "index": video_index,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                video_id = self.chat_database.add_document(
                    collection_name="video",
                    document=video_doc
                )
                video_ids.append(str(video_id))

                for paragraph_index, paragraph_text in enumerate(video.video_script, start=1):
                    # 4️⃣ Insert paragraph
                    paragraph_doc = {
                        "video_id": str(video_id),
                        "index": paragraph_index,
                        "text": paragraph_text,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    paragraph_id = self.chat_database.add_document(
                        collection_name="paragraph",
                        document=paragraph_doc
                    )
                    paragraph_ids.append(str(paragraph_id))
                    self.add_knowledge(
                        collection_name="course",
                        query_text=paragraph_text,
                        payload={
                            "course_id": str(course_id),
                            "chapter_id": str(chapter_id),
                            "chapter_index": chapter_index,
                            "video_id": str(video_id),
                            "video_index": video_index,
                            "paragraph_id": str(paragraph_id),
                            "paragraph_index": paragraph_index,
                            "paragraph_text": paragraph_text,
                            "created_at": datetime.utcnow(),
                        }
                    )

        return {
            "course_id": str(course_id),
            "chapter_ids": [str(cid) for cid in chapter_ids],
            "video_ids": [str(vid) for vid in video_ids],
            "paragraph_ids": [str(pid) for pid in paragraph_ids]
        }

    def _format_nested_results(self, matches: list) -> CourseKnowledge:
        """
        Group ScoredPoint matches by chapter → video → paragraphs,
        sort all levels, and build both:
          - structured tree (`results`)
          - flat ordered list of paragraph_texts (`context`)
        """
        tree = defaultdict(lambda: defaultdict(lambda: {"video_index": 0, "paragraphs": []}))
        chapter_indexes = {}

        for match in matches:
            payload = match.payload

            chapter_id = str(payload["chapter_id"])
            video_id = str(payload["video_id"])
            video_index = payload.get("video_index", 0)
            chapter_index = payload.get("chapter_index", 0)

            chapter_indexes[chapter_id] = chapter_index

            tree[chapter_id][video_id]["video_index"] = video_index
            tree[chapter_id][video_id]["paragraphs"].append({
                "paragraph_id": str(payload["paragraph_id"]),
                "paragraph_index": payload["paragraph_index"],
                "paragraph_text": payload["paragraph_text"],
                "score": match.score
            })

        result = []
        context = []

        for chapter_id, videos in tree.items():
            videos_list = []

            for video_id, video_data in videos.items():
                sorted_paragraphs = sorted(
                    video_data["paragraphs"],
                    key=lambda x: x["paragraph_index"]
                )

                # Add ordered paragraph_texts to context
                context.extend([p["paragraph_text"] for p in sorted_paragraphs])

                videos_list.append({
                    "video_id": video_id,
                    "video_index": video_data["video_index"],
                    "paragraphs": sorted_paragraphs
                })

            videos_list = sorted(videos_list, key=lambda x: x["video_index"])

            result.append({
                "chapter_id": chapter_id,
                "chapter_index": chapter_indexes[chapter_id],
                "videos": videos_list
            })

        result = sorted(result, key=lambda x: x["chapter_index"])
        return CourseKnowledge(
            context=context,
            detailed_results=result
        )

    def ask_course(self, course_id: str, query_text: str):
        matches = self.get_knowledge(
            collection_name="course",
            query_text=query_text,
            filter_key="course_id",
            filter_value=course_id,
            score_threshold=0.4,
            top_k=5
        )
        return self._format_nested_results(matches)

    def ask_chapter(self, chapter_id: str, query_text: str):
        matches = self.get_knowledge(
            collection_name="course",
            query_text=query_text,
            filter_key="chapter_id",
            filter_value=chapter_id,
            score_threshold=0.4,
            top_k=5
        )
        return self._format_nested_results(matches)

    def ask_video(self, video_id: str, query_text: str):
        matches = self.get_knowledge(
            collection_name="course",
            query_text=query_text,
            filter_key="video_id",
            filter_value=video_id,
            score_threshold=0.4,
            top_k=5
        )
        return self._format_video_results(matches)

    def _format_video_results(self, matches) -> CourseKnowledge:
        sorted_matches = sorted(
            matches,
            key=lambda x: x.payload.get("paragraph_index", 0)
        )

        results = [
            {
                "paragraph_id": str(item.payload["paragraph_id"]),
                "paragraph_index": item.payload["paragraph_index"],
                "paragraph_text": item.payload["paragraph_text"],
                "score": item.score
            }
            for item in sorted_matches
        ]

        context = [item["paragraph_text"] for item in results]

        return CourseKnowledge(
            context=context,
            detailed_results=[{"paragraphs": results}]
        )

    def add_prompt(self, collection_name: str, system_prompt: str,
                   prompt_name: str, user_id: PyObjectId = None):
        try:
            payload = {
                "system_prompt": system_prompt,
                "prompt_name": prompt_name,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            prompt_id = self.chat_database.add_document(collection_name=collection_name,
                                                        document=payload)
            return prompt_id
        except Exception as e:
            print(f"Error adding prompt: {e}")
            raise e

    def get_prompts(self, collection_name: str, user_id: str = None):
        try:
            query = {"user_id": user_id} if user_id else {}
            prompts = self.chat_database.get_documents(collection_name=collection_name, query=query)
            return [prompt for prompt in prompts]
        except Exception as e:
            print(f"Error retrieving prompts: {e}")
            raise e

    def get_prompt(self, collection_name: str, prompt_id: str):
        try:
            prompt = self.chat_database.get_document(collection_name=collection_name, document_id=ObjectId(prompt_id))
            return prompt
        except Exception as e:
            print(f"Error retrieving prompt: {e}")
            raise e
