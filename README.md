# 📚 Course Content Creator

**Course Content Creator** is a **FastAPI** backend service that automates the creation of complete online courses. It generates structured course outlines, detailed course scripts, quizzes, stores the content in a knowledge base, allows uploading and parsing external files (PDF/TXT) as new sources, and provides an interactive Q&A chat with the generated course content.

---

## 🚀 Key Features

### 🎯 Core Functionality
✅ **Generate Course Outlines**  
Create structured outlines for new courses, optionally using external knowledge sources.

✅ **Generate Course Content**  
Produce detailed scripts for each chapter and video, with multi-threaded processing for speed.

✅ **Generate Quizzes**  
Automatically create quiz questions for videos to reinforce learning.

### 🗄️ Knowledge Management
✅ **Knowledge Base Integration**  
Store generated course content in a knowledge base for later retrieval and enrichment.

✅ **Upload Course Files**  
Upload and parse PDF or TXT files to populate the knowledge base as new content sources.

✅ **Interactive Chat**  
Chat with the course content to answer learner queries based on the stored knowledge.

---

## 📂 Project Structure

```plaintext
app/
 ├── controller/
 │    ├── course_generation_controller.py   # Business logic for generation and chat
 │    └── course_attachment_controller.py   # Logic for file uploads & knowledge extraction
 ├── model/
 │    └── content_dto.py                    # Data models (CourseOutline, CourseScript, etc.)
 ├── request_schema/
 │    └── course_content_request.py         # Input request schemas
 ├── schema/
 │    └── chat_request_schema.py            # Chat request schema
 ├── routes/
 │    ├── course_generation_router.py       # FastAPI routes for generation & chat
 │    └── course_attachment_router.py       # FastAPI routes for uploading course files
 ├── constant_manager.py                    # Prompts and system constants
 ├── container.py                           # Knowledge base and LLM client dependencies
 ├── main.py                                # FastAPI app entry point
 ├── requirements.txt
 ├── streamlit_app.py
 └── README.md
```
---

## ⚙️ API Endpoints

| Endpoint                     | Method | Description                                      | Request Body                   | Response                     |
|------------------------------|--------|--------------------------------------------------|--------------------------------|------------------------------|
| `/generate-course-outlines`   | POST   | Create a new course outline                     | `CourseOutlineRequest`         | `CourseOutLines`             |
| `/outlines-prompt`            | GET    | Retrieve the default outline prompt used by LLM  | -                              | Prompt text                  |
| `/generate-course-content`    | POST   | Generate detailed course content from outline    | `CourseOutLines`               | `CourseScript`               |
| `/add-course-content`         | POST   | Save course content to knowledge base            | `CourseScript`                 | Success message              |
| `/generate-course-quiz`       | POST   | Generate quizzes for videos                      | `CourseScript`                 | `CourseScriptWithQuiz`       |
| `/chat`                      | POST   | Ask questions about course content               | `ChatRequestSchema`            | Generated answer with context|
| `/upload/course-files`        | POST   | Upload PDF/TXT files to knowledge base           | Form data (files + source_name)| Upload confirmation          |
| `/sources`                   | GET    | List all knowledge base collections              | -                              | List of source names         |

## 🧩 How It Works

### 🔄 Workflow Overview
1. **Outline Generation** - Uses an LLM to generate structured outline based on course parameters
2. **Content Creation** - Processes chapters/videos in parallel with ThreadPoolExecutor
3. **Quiz Generation** - Creates assessments for each video (excluding intro/conclusion)
4. **Knowledge Storage** - Stores content in searchable knowledge base
5. **File Processing** - Extracts/chunks uploaded files for knowledge enrichment
6. **Interactive Chat** - Combines queries with stored knowledge for contextual answers

## ▶️ Getting Started

### Installation & Running
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload
```
Access the API docs at: http://localhost:8000/docs

