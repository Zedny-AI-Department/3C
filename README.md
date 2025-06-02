# 📘 3C: Triple C – Course Content Creator

**3C (Triple C)** is a scalable, AI-powered pipeline for automated course content generation. It aims to empower educators, content creators, and edtech platforms by producing high-quality, structured, and pedagogically sound learning materials with minimal manual effort.

---

## 🌟 Project Overview

The 3C project is composed of **three major phases**, each building on top of the previous to form a complete educational content generation pipeline:

### ✅ Phase 1: Course Outline Generation (Implemented)
Generates a complete professional course outline using OpenAI's GPT-4o via FastAPI. The outline includes:

- Course title, slogan, and description
- Learning skills and measurable objectives
- Chapters and video modules
- Keywords and brief descriptions for each video

> ✔️ This is the current working module, fully implemented and production-ready.

---

### 🔄 Phase 2: Content Sourcing via Keyword-based Web Search (Coming Soon)
Utilize the keywords generated in Phase 1 to search the web and gather high-quality reference content for each video. This step will:

- Perform intelligent web search or scraping
- Extract and clean relevant educational material
- Structure findings per video for use in script generation

---

### 🧠 Phase 3: Video Content Generation (Coming Soon)
Generate complete, coherent, and engaging scripts for each video module using:

- The metadata (title, skill, objective, keyword) from Phase 1
- The reference material sourced in Phase 2

Outputs will include:
- Professional-grade video scripts
- Estimated reading durations
- Instructional formatting for production teams

---

## 🏗️ Architecture (Phase 1)

Client (Frontend)  
|  
v  
FastAPI Backend  
├── /generate-course-outlines [POST] → Generates course outline  
└── /outlines-prompt [GET] → Returns system prompt used for generation  

LLM Client  
└── GPT-4o (via OpenAI API)  
  |  
  └── Prompt + Parameters → Structured JSON Output

---

## 🚀 Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/<your-org>/triple-c.git
cd triple-c
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment  
Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_key_here
```

### 4. Run the FastAPI App
```bash
uvicorn main:app --reload
```

---

## 📈 Roadmap

| Phase | Name                        | Status     |
| ----- | --------------------------- | ---------- |
| 1     | Course Outline Generator    | ✅ Complete |
| 2     | Keyword-Based Content Fetch | 🔜 Planned  |
| 3     | AI-Powered Script Generator | 🔜 Planned  |

---

## 📄 License

This project is licensed under the MIT License.
