import streamlit as st
import json
from controller import generate_course_outline
from constant_manager import course_outline_prompt
from pydantic import BaseModel, Field
from typing import List, Optional

# Set page config
st.set_page_config(
    page_title="Course Outline Generator",
    page_icon="📚",
    layout="wide"
)

# Title and description
st.title("📚 Course Outline Generator")
st.markdown("Generate comprehensive course outlines with structured chapters and video content.")


# Define the request model to match your updated API
class CourseOutlineRequest(BaseModel):
    country: Optional[str] = Field('US', title="Country of the course")
    course_name: str = Field(..., title="Name of the course")
    target_audience: str = Field(..., title="Target audience for the course")
    course_level: str = Field(..., title="Level of the course (e.g., beginner, intermediate, advanced)")
    brief: Optional[str] = Field(
        None,
        title="Brief description of the course",
        description="A brief description to help in generating the course outline"
    )
    chapter_count: int = Field(
        ...,
        title="Number of chapters in the course",
        description="The number of chapters to be included in the course outline"
    )
    video_count: int = Field(
        ...,
        title="Number of videos per chapter",
        description="The number of videos to be included in each chapter of the course outline"
    )
    min_words_per_video: int = Field(
        ...,
        title="Minimum words per video",
        description="The minimum number of words that should be included in each video script"
    )
    max_words_per_video: int = Field(
        ...,
        title="Maximum words per video",
        description="The maximum number of words that should be included in each video script"
    )
    language: Optional[str] = Field(
        default="English",
        title="Language of the course",
        description="The language in which the course will be delivered"
    )
    limitations: Optional[str] = Field(
        default=None,
        title="Limitations of the course",
        description="Any limitations or constraints that should be considered while generating the course outline"
    )
    skills: List[str] = Field(
        ...,
        title="Skills to be acquired",
        description="Skills that the course aims to impart to the learners"
    )


# Create two columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Course Details")

    # Country selection (new field)
    country = st.selectbox(
        "Country",
        ["US", "UK", "Canada", "Australia", "Germany", "France", "Spain", "Italy", "Japan", "India", "Brazil", "Mexico",
         "Other"],
        index=0,
        help="Select the country where the course will be delivered"
    )

    # Basic course information
    course_name = st.text_input(
        "Course Name *",
        placeholder="e.g., Introduction to Python Programming"
    )

    target_audience = st.text_input(
        "Target Audience *",
        placeholder="e.g., Beginners with no programming experience"
    )

    course_level = st.selectbox(
        "Course Level *",
        ["Beginner", "Intermediate", "Advanced", "Expert"]
    )

    brief = st.text_area(
        "Course Brief",
        placeholder="Provide a brief description of what the course will cover... (Optional)",
        help="This field is optional but recommended for better course outline generation",
        height=100
    )

    # Skills section
    st.subheader("Learning Skills & Outcomes *")

    # Skills management with session state
    if 'skills_list' not in st.session_state:
        st.session_state.skills_list = []

    # Add new skill
    col_skill1, col_skill2 = st.columns([3, 1])
    with col_skill1:
        new_skill = st.text_input(
            "Add a skill",
            placeholder="e.g., Python programming fundamentals",
            key="skill_input",
            label_visibility="collapsed"
        )
    with col_skill2:
        if st.button("➕ Add", type="secondary", use_container_width=True):
            if new_skill.strip() and new_skill.strip() not in st.session_state.skills_list:
                st.session_state.skills_list.append(new_skill.strip())
                st.rerun()

    # Display current skills
    if st.session_state.skills_list:
        st.write("**Added Skills:**")
        for i, skill in enumerate(st.session_state.skills_list):
            col_skill_display, col_skill_remove = st.columns([4, 1])
            with col_skill_display:
                st.write(f"• {skill}")
            with col_skill_remove:
                if st.button("🗑️", key=f"remove_{i}", help="Remove skill"):
                    st.session_state.skills_list.pop(i)
                    st.rerun()
    else:
        st.info("💡 Add skills that students will learn in this course (Required)")

    # Use the skills from session state
    skills = st.session_state.skills_list

with col2:
    st.header("Course Structure")

    # Numeric inputs
    chapter_count = st.number_input(
        "Number of Chapters *",
        min_value=1,
        max_value=20,
        value=5,
        help="Total number of chapters in the course"
    )

    video_count = st.number_input(
        "Videos per Chapter *",
        min_value=1,
        max_value=20,
        value=3,
        help="Number of videos in each chapter"
    )

    st.subheader("Video Requirements")

    min_words = st.number_input(
        "Min Words per Video *",
        min_value=50,
        max_value=2000,
        value=300,
        help="Minimum words for each video script"
    )

    max_words = st.number_input(
        "Max Words per Video *",
        min_value=100,
        max_value=5000,
        value=800,
        help="Maximum words for each video script"
    )

    language = st.selectbox(
        "Language",
        ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese", "Korean", "Hindi",
         "Arabic"],
        help="Language in which the course will be delivered"
    )

    limitations = st.text_area(
        "Limitations/Constraints",
        placeholder="Any specific limitations or constraints for the course... (Optional)",
        height=80,
        help="Optional field for any constraints to consider"
    )

# Generate button and prompt viewer
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn1:
    prompt_button_text = "❌ Hide Prompt" if st.session_state.get('show_prompt', False) else "📋 View AI Prompt"
    view_prompt_button = st.button(
        prompt_button_text,
        type="secondary",
        use_container_width=True,
        help="Toggle visibility of the AI prompt template"
    )

with col_btn2:
    generate_button = st.button(
        "🚀 Generate Course Outline",
        type="primary",
        use_container_width=True
    )

# Initialize prompt visibility state
if 'show_prompt' not in st.session_state:
    st.session_state.show_prompt = False

# Handle prompt viewing
if view_prompt_button:
    st.session_state.show_prompt = not st.session_state.show_prompt

# Display prompt if visible
if st.session_state.show_prompt:
    try:
        prompt_text = course_outline_prompt

        # Header with hide button
        col_prompt_header, col_hide_btn = st.columns([3, 1])
        with col_prompt_header:
            st.header("🤖 AI Prompt Template")
        with col_hide_btn:
            if st.button("❌ Hide", key="hide_prompt", help="Hide the prompt template"):
                st.session_state.show_prompt = False
                st.rerun()

        st.markdown("This is the prompt template used to generate your course outlines:")

        with st.expander("View Full Prompt", expanded=True):
            st.code(prompt_text, language="text")

        # Option to download the prompt
        st.download_button(
            label="📥 Download Prompt Template",
            data=prompt_text,
            file_name="course_outline_prompt.txt",
            mime="text/plain",
            help="Download the prompt template as a text file"
        )

        st.markdown("---")  # Add separator when prompt is shown

    except Exception as e:
        st.error(f"❌ Error retrieving prompt: {str(e)}")
        st.info("Make sure the constant_manager module is properly configured.")

# Display total video count info
if chapter_count and video_count:
    st.info(f"📊 Total videos in course: {video_count} videos")

# Validation and API call
if generate_button:
    # Validate required fields
    missing_fields = []
    if not course_name:
        missing_fields.append("Course Name")
    if not target_audience:
        missing_fields.append("Target Audience")
    if not course_level:
        missing_fields.append("Course Level")
    if not skills:
        missing_fields.append("Skills (at least one skill required)")

    if missing_fields:
        st.error(f"Please fill in the following required fields: {', '.join(missing_fields)}")
    else:
        # Validate word count logic
        if min_words >= max_words:
            st.error("Minimum words per video must be less than maximum words per video")
        else:
            # Prepare the request object
            outline_request = CourseOutlineRequest(
                country=country,
                course_name=course_name,
                target_audience=target_audience,
                course_level=course_level.lower(),
                brief=brief if brief else None,
                chapter_count=chapter_count,
                video_count=video_count,
                min_words_per_video=min_words,
                max_words_per_video=max_words,
                language=language,
                limitations=limitations if limitations else None,
                skills=skills
            )

            # Show loading spinner
            with st.spinner("Generating course outline... This may take a few moments."):
                try:
                    # Call the function directly
                    course_data = generate_course_outline(outline_request)

                    # Convert Pydantic model to dict for display
                    if hasattr(course_data, 'dict'):
                        course_dict = course_data.dict()
                    elif hasattr(course_data, 'model_dump'):
                        course_dict = course_data.model_dump()
                    else:
                        course_dict = course_data.__dict__

                    # Display results
                    st.success("Course outline generated successfully!")

                    # Course overview
                    st.header("📋 Course Overview")
                    st.subheader(course_dict.get("course_name", ""))
                    st.write(course_dict.get("course_description", ""))

                    if course_dict.get("course_slogan"):
                        st.info(f"**Slogan:** {course_dict['course_slogan']}")

                    # Course details in columns
                    col_details1, col_details2 = st.columns(2)

                    with col_details1:
                        st.subheader("🎯 Course Objectives")
                        objectives = course_dict.get("course_objectives", [])
                        for i, objective in enumerate(objectives, 1):
                            st.write(f"{i}. {objective}")

                    with col_details2:
                        st.subheader("💡 Skills You'll Learn")
                        skills_learned = course_dict.get("course_skills", [])
                        for skill in skills_learned:
                            st.write(f"• {skill}")

                    # Chapters and videos
                    st.header("📚 Course Structure")
                    chapters = course_dict.get("chapters", [])

                    for i, chapter in enumerate(chapters, 1):
                        with st.expander(f"Chapter {i}: {chapter.get('chapter_name', '')}", expanded=True):
                            videos = chapter.get("videos", [])

                            for j, video in enumerate(videos, 1):
                                st.subheader(f"Video {j}: {video.get('video_name', '')}")

                                col_video1, col_video2 = st.columns([2, 1])

                                with col_video1:
                                    st.write(f"**Description:** {video.get('video_description', '')}")
                                    st.write(f"**Objective:** {video.get('video_objective', '')}")
                                    st.write(f"**Skill Focus:** {video.get('video_skill', '')}")

                                    keywords = video.get('video_keywords', [])
                                    if keywords:
                                        st.write(f"**Keywords:** {', '.join(keywords)}")

                                with col_video2:
                                    duration = video.get('video_duration', 0)
                                    st.metric("Duration", f"{duration} words")

                                    prev_video = video.get('previous_video_name', '')
                                    if prev_video:
                                        st.write(f"**Previous:** {prev_video}")

                                st.markdown("---")

                    # Download option
                    st.header("💾 Export")
                    json_str = json.dumps(course_dict, indent=2)
                    st.download_button(
                        label="Download Course Outline (JSON)",
                        data=json_str,
                        file_name=f"{course_name.lower().replace(' ', '_')}_outline.json",
                        mime="application/json"
                    )

                except Exception as e:
                    st.error(f"❌ An error occurred while generating the course outline: {str(e)}")
                    st.error("Please check your configuration and try again.")

# Sidebar with info
with st.sidebar:
    st.header("📋 How to Use")
    st.markdown("""
    **Step 1: Course Information**
    - Select your country/region
    - Enter your course name and description
    - Define your target audience clearly
    - Select appropriate difficulty level
    - Brief description is optional but recommended

    **Step 2: Learning Outcomes**
    - Add specific skills students will gain (Required)
    - Use clear, measurable skill descriptions
    - Examples: "Build REST APIs", "Analyze data with pandas"

    **Step 3: Course Structure**
    - Set number of chapters
    - Set videos per chapter (not total videos)
    - Define word count per video script
    - Add any specific constraints (optional)

    **Step 4: Generate & Review**
    - Click generate to create your outline
    - Review the structured content
    - Download as JSON for further use
    """)

    st.header("💡 Best Practices")
    st.markdown("""
    **Course Naming:**
    - Be specific and descriptive
    - Include skill level if relevant

    **Target Audience:**
    - Specify prior knowledge required
    - Mention relevant background

    **Skills Definition:**
    - Use action verbs (Build, Create, Analyze)
    - Be specific about tools/technologies
    - Focus on practical outcomes
    - At least one skill is required
    """)

    st.header("🎯 Sample Skills")
    st.markdown("""
    ```
    Build responsive web applications
    Implement data visualization techniques  
    Design database schemas
    Apply machine learning algorithms
    Create automated testing workflows
    ```
    """)

    st.header("📊 Course Structure")
    st.markdown("""
    **Note:** Video count now refers to videos per chapter, not total videos.

    **Example:**
    - 5 chapters × 3 videos per chapter = 15 total videos
    """)

    st.header("🔍 Advanced Features")
    st.markdown("""
    **View AI Prompt:**
    - Click "View AI Prompt" to see the template used
    - Download the prompt for customization
    - Understand how the AI generates outlines

    **Export Options:**
    - Download course outline as JSON
    - Use data in other applications
    - Share with team members
    """)

    st.markdown("---")
    st.caption("💫 AI-Powered Course Design Assistant")