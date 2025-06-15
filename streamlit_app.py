import streamlit as st
import json
from controller import generate_course_outline, generate_course_content
from constant_manager import course_outline_prompt
from pydantic import BaseModel, Field
from typing import List, Optional

from model.content_dto import CourseOutLines, ChapterOutLines, VideoOutLines


def create_formatted_scripts(content_dict):
    """Create a formatted text version of all video scripts"""
    formatted_text = []

    # Course header
    formatted_text.append("=" * 80)
    formatted_text.append(f"COURSE: {content_dict.get('course_name', 'Untitled Course')}")
    formatted_text.append("=" * 80)
    formatted_text.append("")

    if content_dict.get('course_description'):
        formatted_text.append(f"Description: {content_dict['course_description']}")
        formatted_text.append("")

    if content_dict.get('course_slogan'):
        formatted_text.append(f"Slogan: {content_dict['course_slogan']}")
        formatted_text.append("")

    formatted_text.append("-" * 80)
    formatted_text.append("")

    # Process chapters and videos
    chapters = content_dict.get("chapters", [])
    for i, chapter in enumerate(chapters, 1):
        formatted_text.append(f"CHAPTER {i}: {chapter.get('chapter_name', 'Untitled Chapter')}")
        formatted_text.append("=" * 60)
        formatted_text.append("")

        videos = chapter.get("videos", [])
        for j, video in enumerate(videos, 1):
            formatted_text.append(f"Video {i}.{j}: {video.get('video_name', 'Untitled Video')}")
            formatted_text.append("-" * 40)
            formatted_text.append("")

            # Video details
            if video.get('video_description'):
                formatted_text.append(f"Description: {video['video_description']}")
                formatted_text.append("")

            if video.get('video_objective'):
                formatted_text.append(f"Objective: {video['video_objective']}")
                formatted_text.append("")

            if video.get('video_skill'):
                formatted_text.append(f"Skill Focus: {video['video_skill']}")
                formatted_text.append("")

            if video.get('video_keywords'):
                keywords = video['video_keywords']
                if isinstance(keywords, list):
                    formatted_text.append(f"Keywords: {', '.join(keywords)}")
                else:
                    formatted_text.append(f"Keywords: {keywords}")
                formatted_text.append("")

            # Video script
            formatted_text.append("SCRIPT:")
            formatted_text.append("-" * 20)

            video_script = video.get('video_script', [])
            if isinstance(video_script, list):
                for idx, segment in enumerate(video_script, 1):
                    if len(video_script) > 1:
                        formatted_text.append(f"[Segment {idx}]")
                    formatted_text.append(segment)
                    formatted_text.append("")
            else:
                formatted_text.append(str(video_script) if video_script else "No script available")
                formatted_text.append("")

            formatted_text.append("-" * 40)
            formatted_text.append("")

        formatted_text.append("")

    return "\n".join(formatted_text)


# Set page config
st.set_page_config(
    page_title="Course Generator",
    page_icon="📚",
    layout="wide"
)

# Title and description
st.title("📚 Course Generator")
st.markdown(
    "Generate comprehensive course outlines with structured chapters and video content, then create full course scripts.")


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


# Initialize session state for course data
if 'course_outline' not in st.session_state:
    st.session_state.course_outline = None
if 'course_content' not in st.session_state:
    st.session_state.course_content = None
if 'step' not in st.session_state:
    st.session_state.step = 'input'  # 'input', 'edit', 'content'

# Step 1: Course Input Form
if st.session_state.step == 'input':
    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Course Details")

        # Country selection (new field)
        country = st.selectbox(
            "Country",
            ["US", "UK", "Canada", "Australia", "Germany", "France", "Spain", "Italy", "Japan", "India", "Brazil",
             "Mexico",
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
            ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese", "Korean",
             "Hindi",
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
        st.info(f"📊 Total videos in course: {chapter_count * video_count} videos")

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
                        st.session_state.course_outline = course_data
                        st.session_state.step = 'edit'
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ An error occurred while generating the course outline: {str(e)}")
                        st.error("Please check your configuration and try again.")

# Step 2: Edit Course Outline
elif st.session_state.step == 'edit':
    st.header("✏️ Edit Course Outline")
    st.markdown("Review and edit your course outline before generating the full content.")

    course_data = st.session_state.course_outline

    # Convert Pydantic model to dict for editing
    if hasattr(course_data, 'dict'):
        course_dict = course_data.dict()
    elif hasattr(course_data, 'model_dump'):
        course_dict = course_data.model_dump()
    else:
        course_dict = course_data.__dict__

    # Course overview editing
    st.subheader("📋 Course Overview")

    edited_course_name = st.text_input(
        "Course Name",
        value=course_dict.get("course_name", ""),
        key="edit_course_name"
    )

    edited_course_description = st.text_area(
        "Course Description",
        value=course_dict.get("course_description", ""),
        height=100,
        key="edit_course_description"
    )

    edited_course_slogan = st.text_input(
        "Course Slogan",
        value=course_dict.get("course_slogan", ""),
        key="edit_course_slogan"
    )

    # Course objectives editing
    st.subheader("🎯 Course Objectives")
    objectives = course_dict.get("course_objectives", [])
    edited_objectives = []

    for i, objective in enumerate(objectives):
        edited_obj = st.text_area(
            f"Objective {i + 1}",
            value=objective,
            height=80,
            key=f"edit_objective_{i}"
        )
        edited_objectives.append(edited_obj)

    # Course skills editing
    st.subheader("💡 Course Skills")
    skills = course_dict.get("course_skills", [])
    edited_skills = []

    for i, skill in enumerate(skills):
        edited_skill = st.text_input(
            f"Skill {i + 1}",
            value=skill,
            key=f"edit_skill_{i}"
        )
        edited_skills.append(edited_skill)

    # Chapters and videos editing
    st.subheader("📚 Course Structure")
    chapters = course_dict.get("chapters", [])
    edited_chapters = []

    for i, chapter in enumerate(chapters):
        with st.expander(f"Chapter {i + 1}: {chapter.get('chapter_name', '')}", expanded=True):
            edited_chapter_name = st.text_input(
                "Chapter Name",
                value=chapter.get('chapter_name', ''),
                key=f"edit_chapter_{i}_name"
            )

            videos = chapter.get("videos", [])
            edited_videos = []

            for j, video in enumerate(videos):
                st.markdown(f"**Video {j + 1}**")

                col_video1, col_video2 = st.columns([2, 1])

                with col_video1:
                    edited_video_name = st.text_input(
                        "Video Name",
                        value=video.get('video_name', ''),
                        key=f"edit_video_{i}_{j}_name"
                    )

                    edited_video_description = st.text_area(
                        "Video Description",
                        value=video.get('video_description', ''),
                        height=80,
                        key=f"edit_video_{i}_{j}_desc"
                    )

                    edited_video_objective = st.text_area(
                        "Video Objective",
                        value=video.get('video_objective', ''),
                        height=80,
                        key=f"edit_video_{i}_{j}_obj"
                    )

                    edited_video_skill = st.text_input(
                        "Video Skill Focus",
                        value=video.get('video_skill', ''),
                        key=f"edit_video_{i}_{j}_skill"
                    )

                with col_video2:
                    edited_video_duration = st.number_input(
                        "Duration (words)",
                        value=video.get('video_duration', 0),
                        min_value=0,
                        key=f"edit_video_{i}_{j}_duration"
                    )

                    keywords = video.get('video_keywords', [])
                    edited_keywords_str = st.text_area(
                        "Keywords (one per line)",
                        value='\n'.join(keywords),
                        height=80,
                        key=f"edit_video_{i}_{j}_keywords"
                    )
                    edited_keywords = [kw.strip() for kw in edited_keywords_str.split('\n') if kw.strip()]

                # Store edited video data
                edited_video = {
                    'video_name': edited_video_name,
                    'video_description': edited_video_description,
                    'video_objective': edited_video_objective,
                    'video_skill': edited_video_skill,
                    'video_duration': edited_video_duration,
                    'video_keywords': edited_keywords,
                    'previous_video_name': video.get('previous_video_name', '')
                }
                edited_videos.append(edited_video)

                st.markdown("---")

            # Store edited chapter data
            edited_chapter = {
                'chapter_name': edited_chapter_name,
                'videos': edited_videos
            }
            edited_chapters.append(edited_chapter)

    # Navigation buttons
    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])

    with col_nav1:
        if st.button("⬅️ Back to Input", type="secondary", use_container_width=True):
            st.session_state.step = 'input'
            st.rerun()

    with col_nav2:
        # Download edited outline
        edited_course_dict = {
            'country': course_dict.get('country'),
            'course_name': edited_course_name,
            'course_description': edited_course_description,
            'course_slogan': edited_course_slogan,
            'target_audience': course_dict.get('target_audience'),
            'course_level': course_dict.get('course_level'),
            'course_objectives': [obj for obj in edited_objectives if obj.strip()],
            'course_skills': [skill for skill in edited_skills if skill.strip()],
            'chapters': edited_chapters
        }

        json_str = json.dumps(edited_course_dict, indent=2)
        st.download_button(
            label="💾 Download Outline",
            data=json_str,
            file_name=f"{edited_course_name.lower().replace(' ', '_')}_outline.json",
            mime="application/json"
        )

    with col_nav3:
        if st.button("🚀 Generate Course Content", type="primary", use_container_width=True):
            # Update the course outline with edited data
            try:
                # Create a new course outline object with edited data
                updated_chapters = []
                for chapter_data in edited_chapters:
                    updated_videos = []
                    for video_data in chapter_data['videos']:
                        updated_video = VideoOutLines(
                            video_name=video_data['video_name'],
                            previous_video_name=video_data.get('previous_video_name', ''),
                            video_description=video_data['video_description'],
                            video_keywords=video_data['video_keywords'],
                            video_skill=video_data['video_skill'],
                            video_objective=video_data['video_objective'],
                            video_duration=video_data['video_duration']
                        )
                        updated_videos.append(updated_video)

                    updated_chapter = ChapterOutLines(
                        chapter_name=chapter_data['chapter_name'],
                        videos=updated_videos
                    )
                    updated_chapters.append(updated_chapter)

                updated_course_outline = CourseOutLines(
                    country=course_dict.get('country'),
                    course_name=edited_course_name,
                    course_description=edited_course_description,
                    course_slogan=edited_course_slogan,
                    target_audience=course_dict.get('target_audience'),
                    course_level=course_dict.get('course_level'),
                    course_objectives=[obj for obj in edited_objectives if obj.strip()],
                    course_skills=[skill for skill in edited_skills if skill.strip()],
                    chapters=updated_chapters
                )

                # Generate course content
                with st.spinner("Generating full course content... This may take several minutes."):
                    course_content = generate_course_content(updated_course_outline)
                    st.session_state.course_content = course_content
                    st.session_state.step = 'content'
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error generating course content: {str(e)}")

# Step 3: Display and Edit Final Course Content
elif st.session_state.step == 'content':
    st.header("🎉 Complete Course Content")
    st.markdown("Your full course with scripts has been generated! You can now edit the scripts before downloading.")

    course_content = st.session_state.course_content

    # Convert to dict for display
    if hasattr(course_content, 'dict'):
        content_dict = course_content.dict()
    elif hasattr(course_content, 'model_dump'):
        content_dict = course_content.model_dump()
    else:
        content_dict = course_content.__dict__

    # Initialize edited content in session state if not exists
    if 'edited_content' not in st.session_state:
        st.session_state.edited_content = content_dict.copy()

    edited_content = st.session_state.edited_content

    # Course overview editing
    st.subheader("📋 Course Overview")

    edited_content['course_name'] = st.text_input(
        "Course Name",
        value=edited_content.get("course_name", ""),
        key="final_course_name"
    )

    edited_content['course_description'] = st.text_area(
        "Course Description",
        value=edited_content.get("course_description", ""),
        height=100,
        key="final_course_description"
    )

    edited_content['course_slogan'] = st.text_input(
        "Course Slogan",
        value=edited_content.get("course_slogan", ""),
        key="final_course_slogan"
    )

    # Course details editing
    col_details1, col_details2 = st.columns(2)

    with col_details1:
        st.subheader("🎯 Course Objectives")
        objectives = edited_content.get("course_objectives", [])
        edited_objectives = []

        for i, objective in enumerate(objectives):
            edited_obj = st.text_area(
                f"Objective {i + 1}",
                value=objective,
                height=80,
                key=f"final_objective_{i}"
            )
            edited_objectives.append(edited_obj)

        edited_content['course_objectives'] = [obj for obj in edited_objectives if obj.strip()]

    with col_details2:
        st.subheader("💡 Skills You'll Learn")
        skills_learned = edited_content.get("course_skills", [])
        edited_skills = []

        for i, skill in enumerate(skills_learned):
            edited_skill = st.text_input(
                f"Skill {i + 1}",
                value=skill,
                key=f"final_skill_{i}"
            )
            edited_skills.append(edited_skill)

        edited_content['course_skills'] = [skill for skill in edited_skills if skill.strip()]

    # Chapters with editable content
    st.subheader("📚 Complete Course Content - Editable Scripts")

    # Add save changes button at the top
    col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
    with col_save2:
        if st.button("💾 Save All Changes", type="primary", use_container_width=True):
            st.session_state.edited_content = edited_content
            st.success("✅ All changes saved!")
            st.rerun()

    chapters = edited_content.get("chapters", [])
    edited_chapters = []

    for i, chapter in enumerate(chapters, 1):
        with st.expander(f"Chapter {i}: {chapter.get('chapter_name', '')}", expanded=False):
            # Edit chapter name
            edited_chapter_name = st.text_input(
                "Chapter Name",
                value=chapter.get('chapter_name', ''),
                key=f"final_chapter_{i}_name"
            )

            videos = chapter.get("videos", [])
            edited_videos = []

            for j, video in enumerate(videos, 1):
                st.markdown(f"### Video {j}: {video.get('video_name', '')}")

                # Create tabs for better organization
                tab1, tab2, tab3 = st.tabs(["📝 Script Editor", "📋 Video Details", "🔧 Advanced"])

                with tab1:
                    # Video Script Editing - Main focus
                    st.markdown("#### Edit Video Script")

                    video_script = video.get('video_script', [])

                    # Handle script as list or string
                    if isinstance(video_script, list):
                        current_script = '\n\n'.join(video_script) if video_script else ""
                    else:
                        current_script = str(video_script) if video_script else ""

                    # Large text area for script editing
                    edited_script = st.text_area(
                        "Script Content",
                        value=current_script,
                        height=400,
                        key=f"final_script_{i}_{j}",
                        help="Edit the complete video script. Use double line breaks to separate script segments."
                    )

                    # Word count display
                    word_count = len(edited_script.split()) if edited_script else 0
                    target_duration = video.get('video_duration', 0)

                    col_word1, col_word2, col_word3 = st.columns(3)
                    with col_word1:
                        st.metric("Current Words", word_count)
                    with col_word2:
                        st.metric("Target Words", target_duration)
                    with col_word3:
                        difference = word_count - target_duration
                        st.metric("Difference", f"{difference:+d}", delta=difference)

                    # Split script back into segments for storage
                    if edited_script:
                        script_segments = [seg.strip() for seg in edited_script.split('\n\n') if seg.strip()]
                    else:
                        script_segments = []

                with tab2:
                    # Video details editing
                    col_video_info1, col_video_info2 = st.columns([2, 1])

                    with col_video_info1:
                        edited_video_name = st.text_input(
                            "Video Name",
                            value=video.get('video_name', ''),
                            key=f"final_video_{i}_{j}_name"
                        )

                        edited_video_description = st.text_area(
                            "Video Description",
                            value=video.get('video_description', ''),
                            height=100,
                            key=f"final_video_{i}_{j}_desc"
                        )

                        edited_video_objective = st.text_area(
                            "Video Objective",
                            value=video.get('video_objective', ''),
                            height=100,
                            key=f"final_video_{i}_{j}_obj"
                        )

                        edited_video_skill = st.text_input(
                            "Skill Focus",
                            value=video.get('video_skill', ''),
                            key=f"final_video_{i}_{j}_skill"
                        )

                    with col_video_info2:
                        edited_video_duration = st.number_input(
                            "Target Duration (words)",
                            value=video.get('video_duration', 0),
                            min_value=0,
                            key=f"final_video_{i}_{j}_duration"
                        )

                        keywords = video.get('video_keywords', [])
                        if isinstance(keywords, list):
                            keywords_str = '\n'.join(keywords)
                        else:
                            keywords_str = str(keywords)

                        edited_keywords_str = st.text_area(
                            "Keywords (one per line)",
                            value=keywords_str,
                            height=100,
                            key=f"final_video_{i}_{j}_keywords"
                        )
                        edited_keywords = [kw.strip() for kw in edited_keywords_str.split('\n') if kw.strip()]

                with tab3:
                    # Advanced options and raw content
                    if video.get('raw_content'):
                        edited_raw_content = st.text_area(
                            "Raw Content (Advanced)",
                            value=video.get('raw_content', ''),
                            height=200,
                            key=f"final_raw_{i}_{j}",
                            help="This is the raw AI-generated content before processing into the script."
                        )
                    else:
                        edited_raw_content = video.get('raw_content', '')

                    # Previous video reference
                    edited_previous_video = st.text_input(
                        "Previous Video Reference",
                        value=video.get('previous_video_name', ''),
                        key=f"final_prev_{i}_{j}",
                        help="Reference to the previous video for continuity"
                    )

                # Store edited video data
                edited_video = {
                    'video_name': edited_video_name,
                    'video_description': edited_video_description,
                    'video_objective': edited_video_objective,
                    'video_skill': edited_video_skill,
                    'video_duration': edited_video_duration,
                    'video_keywords': edited_keywords,
                    'video_script': script_segments,  # Store as list of segments
                    'raw_content': edited_raw_content,
                    'previous_video_name': edited_previous_video
                }
                edited_videos.append(edited_video)

                st.markdown("---")

            # Store edited chapter data
            edited_chapter = {
                'chapter_name': edited_chapter_name,
                'videos': edited_videos
            }
            edited_chapters.append(edited_chapter)

    # Update the edited content
    edited_content['chapters'] = edited_chapters

    # Display success metrics
    total_videos = sum(len(chapter.get('videos', [])) for chapter in edited_chapters)
    total_chapters = len(edited_chapters)

    # Calculate total script words from edited content
    total_script_words = 0
    for chapter in edited_chapters:
        for video in chapter.get('videos', []):
            video_script = video.get('video_script', [])
            if isinstance(video_script, list):
                for segment in video_script:
                    total_script_words += len(str(segment).split())
            else:
                total_script_words += len(str(video_script).split())

    # Display metrics
    st.markdown("---")
    st.subheader("📊 Course Statistics")
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)

    with col_metric1:
        st.metric("Chapters", total_chapters)

    with col_metric2:
        st.metric("Total Videos", total_videos)

    with col_metric3:
        st.metric("Script Words", f"{total_script_words:,}")

    with col_metric4:
        avg_words_per_video = total_script_words // total_videos if total_videos > 0 else 0
        st.metric("Avg Words/Video", avg_words_per_video)

    # Download and navigation options
    st.markdown("---")
    col_final1, col_final2, col_final3, col_final4 = st.columns([1, 1, 1, 1])

    with col_final1:
        if st.button("⬅️ Back to Edit", type="secondary", use_container_width=True):
            st.session_state.step = 'edit'
            st.rerun()

    with col_final2:
        # Download complete course content (edited version)
        json_str = json.dumps(edited_content, indent=2)
        st.download_button(
            label="💾 Download Course JSON",
            data=json_str,
            file_name=f"{edited_content.get('course_name', 'course').lower().replace(' ', '_')}_complete.json",
            mime="application/json",
            use_container_width=True
        )

    with col_final3:
        # Download formatted scripts
        formatted_scripts = create_formatted_scripts(edited_content)
        st.download_button(
            label="📄 Download Scripts TXT",
            data=formatted_scripts,
            file_name=f"{edited_content.get('course_name', 'course').lower().replace(' ', '_')}_scripts.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col_final4:
        if st.button("🔄 Start New Course", type="primary", use_container_width=True):
            # Reset session state
            st.session_state.course_outline = None
            st.session_state.course_content = None
            st.session_state.edited_content = None
            st.session_state.step = 'input'
            if 'skills_list' in st.session_state:
                st.session_state.skills_list = []
            st.rerun()

    st.success("✅ Course generation completed! Edit scripts above and download when ready.")