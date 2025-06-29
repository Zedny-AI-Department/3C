import io
import logging
from typing import List

from PyPDF2 import PdfReader
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

from container import knowledge_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF file given as bytes.
    :param pdf_bytes: The content of the PDF file as bytes.
    :return: Extracted text as a string.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        logger.info("Successfully extracted text from PDF bytes")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {e}")
        raise e


def extract_text_from_text_file(text_file_bytes: bytes) -> str:
    """
    Extract text from a text file given as bytes.
    :param text_file_bytes: The content of the text file as bytes.
    :return: Extracted text as a string.
    """
    try:
        text = text_file_bytes.decode('utf-8')
        logger.info("Successfully extracted text from TXT bytes")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from text bytes: {e}")
        raise e


async def read_file_content(files: List[UploadFile]):
    try:
        results = []
        for file in files:
            contents = await file.read()
            if file.filename.endswith('.pdf'):
                text = extract_text_from_pdf(contents)
            elif file.filename.endswith('.txt'):
                text = extract_text_from_text_file(contents)
            else:
                raise Exception(f"Unsupported file type: {file.filename} not supported")
            results.append({
                "filename": file.filename,
                "text": text
            })
        return results
    except Exception as e:
        logger.error(f"Error reading file content: {e}")
        raise e


def chunker(text_file: list):
    try:
        chunks_list = []
        for text in text_file:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = splitter.split_text(text["text"])
            chunks_list.append({
                "filename": text["filename"],
                "chunks": chunks
            })
        return chunks_list
    except Exception as e:
        logger.error(f"Error splitting text into chunks: {e}")
        raise e


def upload_file_knowledge(source_name: str, files_with_chunks: List[dict]):
    try:
        is_exist = knowledge_base.check_collection(collection_name=source_name)
        if not is_exist:
            print("Collection created successfully******************")
            knowledge_base.create_collection(collection_name=source_name)
        for file in files_with_chunks:
            for chunk in file["chunks"]:
                knowledge_base.add_knowledge(
                    collection_name=source_name,
                    query_text=chunk,
                    payload={
                        "file_name": file["filename"],
                        "content": chunk
                    }
                )
    except Exception as e:
        print(f"Error adding knowledge base: {e}")
        raise e


async def upload_file(files: List[UploadFile], source_name: str):
    try:
        files_with_text = await read_file_content(files)
        chunk_text = chunker(files_with_text)
        upload_file_knowledge(source_name=source_name, files_with_chunks=chunk_text)
        return chunk_text
    except Exception as e:
        raise e
