"""
AI Study Notes Summarizer
=========================
A Streamlit web app that uses Google Gemini AI to turn study notes into
summaries, key points, important terms, quiz questions, and flashcards.

Author: Student Project
Tech: Python · Streamlit · Google Gemini API · python-dotenv
"""

import os
import io
import json
import time
from datetime import datetime
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from fpdf import FPDF

# ─── Load environment variables from .env file ───
load_dotenv()

# ─── Streamlit Cloud: load secrets into env vars ───
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # Not on Streamlit Cloud, use .env instead

# ─── Page Configuration ───
st.set_page_config(
    page_title="AI Study Notes Summarizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CUSTOM CSS — Makes the app look premium and polished
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def inject_custom_css():
    """Inject custom CSS to style the Streamlit app with a premium look."""
    st.markdown("""
    <style>
    /* ── Import Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Styles ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%);
    }

    /* ── Hero Header ── */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }

    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: shimmer 6s ease-in-out infinite;
    }

    @keyframes shimmer {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        50% { transform: translate(10%, 10%) rotate(5deg); }
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: white;
        margin: 0;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
        position: relative;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        font-size: 1.15rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.75rem;
        font-weight: 400;
        position: relative;
        letter-spacing: 0.2px;
    }

    /* ── Glass Card ── */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    }

    .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .card-summary { color: #a78bfa; }
    .card-keypoints { color: #34d399; }
    .card-terms { color: #fbbf24; }
    .card-quiz { color: #f87171; }
    .card-flashcards { color: #60a5fa; }

    .card-content {
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.95rem;
        line-height: 1.75;
    }

    .card-content ul {
        padding-left: 1.25rem;
    }

    .card-content li {
        margin-bottom: 0.5rem;
    }

    /* ── Term Badge ── */
    .term-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(251, 191, 36, 0.05));
        border: 1px solid rgba(251, 191, 36, 0.3);
        color: #fbbf24;
        padding: 0.35rem 0.85rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }

    /* ── Quiz & Flashcard Blocks ── */
    .quiz-block {
        background: rgba(248, 113, 113, 0.08);
        border-left: 3px solid #f87171;
        padding: 1rem 1.25rem;
        border-radius: 0 12px 12px 0;
        margin-bottom: 0.75rem;
        color: rgba(255, 255, 255, 0.85);
    }

    .flashcard-block {
        background: rgba(96, 165, 250, 0.08);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        color: rgba(255, 255, 255, 0.85);
    }

    .flashcard-q {
        font-weight: 600;
        color: #93c5fd;
        margin-bottom: 0.5rem;
    }

    .flashcard-a {
        color: rgba(255, 255, 255, 0.75);
        padding-left: 1rem;
        border-left: 2px solid rgba(96, 165, 250, 0.3);
    }

    /* ── Sidebar Styling ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.85);
    }

    /* ── Input Area Styling ── */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 1rem !important;
    }

    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25) !important;
    }

    /* ── Button Styling ── */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.08) !important;
        color: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }

    /* ── Stats Badge ── */
    .stats-bar {
        display: flex;
        gap: 1rem;
        margin: 0.75rem 0 1.25rem 0;
    }

    .stat-badge {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 50px;
        padding: 0.35rem 1rem;
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
    }

    /* ── Divider ── */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 2rem 0;
    }

    /* ── Footer ── */
    .app-footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: rgba(255, 255, 255, 0.35);
        font-size: 0.85rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 3rem;
    }

    .app-footer a {
        color: #667eea;
        text-decoration: none;
    }

    /* ── Copy box ── */
    .copy-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        font-family: 'Inter', monospace;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.7);
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }

    /* ── Hide default Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ── Sidebar feature item ── */
    .feature-item {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.8);
        border-left: 3px solid #667eea;
    }

    /* ── File Upload Zone ── */
    .upload-zone {
        background: rgba(102, 126, 234, 0.08);
        border: 2px dashed rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .upload-zone:hover {
        border-color: rgba(102, 126, 234, 0.6);
        background: rgba(102, 126, 234, 0.12);
    }

    /* ── Interactive Quiz ── */
    .quiz-interactive {
        background: rgba(248, 113, 113, 0.06);
        border: 1px solid rgba(248, 113, 113, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .quiz-score-card {
        background: linear-gradient(135deg, rgba(52, 211, 153, 0.15), rgba(52, 211, 153, 0.05));
        border: 1px solid rgba(52, 211, 153, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }

    .score-big {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ── Pomodoro Timer ── */
    .pomodoro-display {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        margin: 0.75rem 0;
    }

    .timer-text {
        font-size: 2.5rem;
        font-weight: 800;
        font-family: 'Inter', monospace;
        letter-spacing: 2px;
    }

    .timer-study { color: #34d399; }
    .timer-break { color: #fbbf24; }
    .timer-idle { color: rgba(255, 255, 255, 0.4); }

    .session-count {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 0.5rem;
    }

    /* ── Progress Dashboard ── */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.25rem;
        text-align: center;
        transition: transform 0.2s ease;
    }

    .metric-card:hover { transform: translateY(-2px); }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-label {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 0.25rem;
        font-weight: 500;
    }

    /* ── Tab Navigation ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        color: rgba(255, 255, 255, 0.7) !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(102, 126, 234, 0.2) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEMO MODE — Pre-generated results so the app works without an API key
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_demo_results(notes: str) -> dict:
    """
    Generate realistic demo results based on the user's pasted notes.
    Extracts real words from the input to make the demo feel authentic.
    Works without any API key — great for class presentations!
    """
    import re
    import time

    # Simulate a brief processing delay to feel realistic
    time.sleep(2)

    # ── Extract words from the notes to make demo results relevant ──
    words = notes.split()
    # Get unique capitalized words (likely important terms)
    capitalized = list(set(
        w.strip(".,;:!?\"'()-") for w in words
        if len(w) > 3 and w[0].isupper() and not w.isupper()
    ))
    # Get longer words as potential key terms
    long_words = list(set(
        w.strip(".,;:!?\"'()-").lower() for w in words
        if len(w.strip(".,;:!?\"'()-")) > 5
    ))

    # Build a short preview of the notes
    first_sentence = notes.split(".")[0].strip() if "." in notes else notes[:100]
    note_preview = notes[:200].strip()

    # ── Select terms from the notes (up to 10) ──
    demo_terms = (capitalized[:6] + long_words[:6])[:10]
    if len(demo_terms) < 8:
        demo_terms += ["key concept", "main idea", "analysis", "methodology",
                       "framework", "theory", "application", "evaluation"][:8 - len(demo_terms)]

    return {
        "summary": (
            f"These notes cover the topic starting with: \"{first_sentence}...\" "
            f"The material discusses several important concepts and their relationships. "
            f"Key themes include foundational principles and their practical applications. "
            f"The notes contain approximately {len(words)} words covering multiple subtopics "
            f"that build upon each other to form a comprehensive understanding of the subject."
        ),
        "key_points": [
            f"The notes begin by introducing the core concept: \"{first_sentence[:80]}...\"",
            "Multiple interconnected ideas are presented that form the foundation of this topic",
            f"Approximately {len(words)} words of content covering key definitions and explanations",
            "The material emphasizes both theoretical understanding and practical application",
            "Important relationships between concepts are highlighted throughout the notes",
            "Several examples and supporting details reinforce the main arguments",
            "The content builds progressively from basic to more advanced concepts",
        ],
        "terms": demo_terms,
        "quiz": [
            {
                "question": f"What is the main topic introduced in these notes?",
                "answer": f"The notes primarily discuss concepts related to: {first_sentence[:80]}"
            },
            {
                "question": f"How many key concepts are covered in this material?",
                "answer": f"The material covers approximately {len(demo_terms)} key concepts and terms across {len(words)} words of content."
            },
            {
                "question": "Why is it important to understand the relationship between the concepts discussed?",
                "answer": "Understanding these relationships helps build a comprehensive framework for applying the knowledge in practical scenarios and exams."
            },
            {
                "question": f"Define the term '{demo_terms[0]}' as used in this context.",
                "answer": f"'{demo_terms[0]}' refers to a key concept discussed in the notes that forms part of the foundational understanding of this topic."
            },
            {
                "question": "What are the practical applications of the theories discussed in these notes?",
                "answer": "The theories can be applied to real-world problem solving, critical analysis, and building upon existing knowledge in the field."
            },
        ],
        "flashcards": [
            {
                "front": f"What is '{demo_terms[0]}'?",
                "back": f"A key concept from the notes related to the main topic being studied."
            },
            {
                "front": "What are the main themes of these study notes?",
                "back": f"The main themes include: {', '.join(demo_terms[:4])} and their interconnected relationships."
            },
            {
                "front": f"What is '{demo_terms[1] if len(demo_terms) > 1 else 'the secondary concept'}'?",
                "back": "An important term that supports the understanding of the broader topic discussed in the notes."
            },
            {
                "front": "How do the concepts in these notes relate to each other?",
                "back": "The concepts build progressively — earlier ideas form the foundation for more advanced topics discussed later."
            },
            {
                "front": "What should you focus on when revising this material?",
                "back": f"Focus on understanding the {len(demo_terms)} key terms, their definitions, and how they connect to form the bigger picture."
            },
        ],
    }


def has_api_key() -> bool:
    """Check if a valid Google Gemini API key is configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    return bool(api_key and api_key != "your_google_api_key_here")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FILE UPLOAD — Extract text from PDF, DOCX, or TXT files
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_text_from_file(uploaded_file) -> str:
    """Extract text content from an uploaded PDF, DOCX, or TXT file."""
    file_type = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif file_type == "docx":
            doc = DocxDocument(uploaded_file)
            text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        elif file_type == "txt":
            text = uploaded_file.read().decode("utf-8")
        else:
            text = ""
        return text.strip()
    except Exception as e:
        st.error(f"❌ Could not read file: {str(e)}")
        return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INTERACTIVE QUIZ — Take the quiz with scoring
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_interactive_quiz(quiz: list):
    """Render an interactive quiz with radio-button answers and scoring."""
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    st.markdown("""
    <div class="glass-card">
        <div class="card-title card-quiz">🎮 Interactive Quiz Mode</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.quiz_submitted:
        with st.form("quiz_form"):
            for i, q in enumerate(quiz):
                question = q.get("question", "")
                answer = q.get("answer", "")
                st.markdown(f"""
                <div class="quiz-block">
                    <strong>Q{i + 1}:</strong> {question}
                </div>
                """, unsafe_allow_html=True)
                user_answer = st.text_input(
                    f"Your answer for Q{i + 1}",
                    key=f"quiz_q_{i}",
                    placeholder="Type your answer here...",
                    label_visibility="collapsed",
                )
            col_submit, col_skip = st.columns([1, 3])
            with col_submit:
                submitted = st.form_submit_button("✅ Submit Quiz", type="primary", use_container_width=True)
            with col_skip:
                skipped = st.form_submit_button("👀 Show All Answers", use_container_width=True)

            if submitted or skipped:
                st.session_state.quiz_submitted = True
                st.session_state.quiz_skipped = skipped
                for i in range(len(quiz)):
                    st.session_state.quiz_answers[i] = st.session_state.get(f"quiz_q_{i}", "")
                # Track in progress stats
                if "total_quizzes" not in st.session_state:
                    st.session_state.total_quizzes = 0
                st.session_state.total_quizzes += 1
                st.rerun()
    else:
        # Show results
        score = 0
        total = len(quiz)
        for i, q in enumerate(quiz):
            question = q.get("question", "")
            correct = q.get("answer", "")
            user_ans = st.session_state.quiz_answers.get(i, "")
            # Simple matching — check if key words from answer appear in user's answer
            if not st.session_state.get("quiz_skipped", False) and user_ans.strip():
                key_words = [w.lower() for w in correct.split() if len(w) > 4]
                matches = sum(1 for kw in key_words if kw in user_ans.lower())
                if matches >= max(1, len(key_words) // 3):
                    score += 1

            is_correct = not st.session_state.get("quiz_skipped", False) and user_ans.strip() and \
                         sum(1 for kw in [w.lower() for w in correct.split() if len(w) > 4]
                             if kw in user_ans.lower()) >= max(1, len([w for w in correct.split() if len(w) > 4]) // 3)
            icon = "✅" if is_correct else "📝"

            st.markdown(f"""
            <div class="quiz-block">
                <strong>{icon} Q{i + 1}:</strong> {question}<br>
                <span style="color: #93c5fd;">Your answer:</span> {user_ans if user_ans else '<em>skipped</em>'}<br>
                <span style="color: #34d399;">Correct answer:</span> {correct}
            </div>
            """, unsafe_allow_html=True)

        if not st.session_state.get("quiz_skipped", False):
            pct = int((score / total) * 100) if total > 0 else 0
            emoji = "🏆" if pct >= 80 else "👏" if pct >= 60 else "💪" if pct >= 40 else "📚"
            st.markdown(f"""
            <div class="quiz-score-card">
                <div class="score-big">{score}/{total}</div>
                <div style="font-size: 1.5rem; margin: 0.5rem 0;">{emoji}</div>
                <div style="color: rgba(255,255,255,0.7);">{pct}% — {'Excellent!' if pct >= 80 else 'Good job!' if pct >= 60 else 'Keep studying!'}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(pct / 100)
            # Save best score
            if "best_score" not in st.session_state:
                st.session_state.best_score = 0
            st.session_state.best_score = max(st.session_state.best_score, pct)

        if st.button("🔄 Retake Quiz", type="primary"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_skipped = False
            st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POMODORO TIMER — Study timer in the sidebar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_pomodoro_timer():
    """Render a Pomodoro study timer in the sidebar."""
    if "pomo_running" not in st.session_state:
        st.session_state.pomo_running = False
    if "pomo_seconds" not in st.session_state:
        st.session_state.pomo_seconds = 25 * 60  # 25 minutes
    if "pomo_is_break" not in st.session_state:
        st.session_state.pomo_is_break = False
    if "pomo_sessions" not in st.session_state:
        st.session_state.pomo_sessions = 0

    st.markdown("### ⏱️ Pomodoro Timer")

    mins = st.session_state.pomo_seconds // 60
    secs = st.session_state.pomo_seconds % 60
    timer_class = "timer-break" if st.session_state.pomo_is_break else (
        "timer-study" if st.session_state.pomo_running else "timer-idle"
    )
    label = "☕ Break" if st.session_state.pomo_is_break else "📖 Study"

    st.markdown(f"""
    <div class="pomodoro-display">
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-bottom: 0.25rem;">{label}</div>
        <div class="timer-text {timer_class}">{mins:02d}:{secs:02d}</div>
        <div class="session-count">🔥 Sessions completed: {st.session_state.pomo_sessions}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️" if not st.session_state.pomo_running else "⏸️", key="pomo_toggle", use_container_width=True):
            st.session_state.pomo_running = not st.session_state.pomo_running
    with col2:
        if st.button("🔄", key="pomo_reset", use_container_width=True):
            st.session_state.pomo_running = False
            st.session_state.pomo_seconds = 25 * 60
            st.session_state.pomo_is_break = False
            st.rerun()
    with col3:
        if st.button("⏭️", key="pomo_skip", use_container_width=True):
            if st.session_state.pomo_is_break:
                st.session_state.pomo_seconds = 25 * 60
                st.session_state.pomo_is_break = False
            else:
                st.session_state.pomo_seconds = 5 * 60
                st.session_state.pomo_is_break = True
                st.session_state.pomo_sessions += 1
            st.session_state.pomo_running = False
            st.rerun()

    # Auto-countdown
    if st.session_state.pomo_running and st.session_state.pomo_seconds > 0:
        time.sleep(1)
        st.session_state.pomo_seconds -= 1
        if st.session_state.pomo_seconds <= 0:
            if st.session_state.pomo_is_break:
                st.session_state.pomo_seconds = 25 * 60
                st.session_state.pomo_is_break = False
            else:
                st.session_state.pomo_sessions += 1
                st.session_state.pomo_seconds = 5 * 60
                st.session_state.pomo_is_break = True
            st.session_state.pomo_running = False
            st.toast("⏰ Timer finished!" if not st.session_state.pomo_is_break else "☕ Break time!")
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROGRESS DASHBOARD — Track study statistics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_progress_dashboard():
    """Render study progress metrics above the results."""
    notes_count = st.session_state.get("notes_count", 0)
    words_processed = st.session_state.get("words_processed", 0)
    quizzes_taken = st.session_state.get("total_quizzes", 0)
    best_score = st.session_state.get("best_score", 0)

    st.markdown("""
    <div class="glass-card" style="padding: 1rem 1.5rem;">
        <div class="card-title" style="color: #c084fc;">📊 Study Progress</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">📝</div>
            <div class="metric-value">{notes_count}</div>
            <div class="metric-label">Notes Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">📖</div>
            <div class="metric-value">{words_processed:,}</div>
            <div class="metric-label">Words Processed</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">🎮</div>
            <div class="metric-value">{quizzes_taken}</div>
            <div class="metric-label">Quizzes Taken</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">🏆</div>
            <div class="metric-value">{best_score}%</div>
            <div class="metric-label">Best Quiz Score</div>
        </div>
        """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PDF EXPORT — Generate downloadable PDF of results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_pdf_report(results: dict) -> bytes:
    """Generate a styled PDF report from the study results."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "AI Study Notes Summary", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True, align="C")
    pdf.ln(10)

    # Summary
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, results.get("summary", "N/A"))
    pdf.ln(5)

    # Key Points
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Points", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for pt in results.get("key_points", []):
        pdf.multi_cell(0, 7, f"  * {pt}")
    pdf.ln(5)

    # Important Terms
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Important Terms", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, ", ".join(results.get("terms", [])))
    pdf.ln(5)

    # Quiz Questions
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Quiz Questions", ln=True)
    for i, q in enumerate(results.get("quiz", []), 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7, f"Q{i}: {q.get('question', '')}")
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, f"A: {q.get('answer', '')}")
        pdf.ln(3)

    # Flashcards
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Flashcards", ln=True)
    for i, fc in enumerate(results.get("flashcards", []), 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7, f"Card {i}: {fc.get('front', '')}")
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, f"Answer: {fc.get('back', '')}")
        pdf.ln(3)

    return pdf.output()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GEMINI HELPER — Sends notes to Google AI and parses results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_ai_summary(notes: str) -> dict:
    """
    Send the user's study notes to Google Gemini and get back structured results.
    Returns a dictionary with: summary, key_points, terms, quiz, flashcards.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """You are an expert academic study assistant.
When given study notes, you MUST return a valid JSON object with these exact keys:

{
  "summary": "A concise, easy-to-understand summary (3-5 sentences)",
  "key_points": ["point 1", "point 2", ...],
  "terms": ["term 1", "term 2", ...],
  "quiz": [
    {"question": "...", "answer": "..."}
  ],
  "flashcards": [
    {"front": "...", "back": "..."}
  ]
}

Rules:
- 5-7 key points
- 8-12 important terms
- 5 quiz questions with answers
- 5 flashcards
- Keep it student-friendly
- Return ONLY valid JSON, no extra text or markdown code fences

Here are my study notes:

""" + notes

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            response_mime_type="application/json",
        ),
    )

    result = json.loads(response.text)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RENDER FUNCTIONS — Display each result section as a styled card
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_summary_card(summary: str):
    """Render the summary section with a purple-themed card."""
    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title card-summary">📝 Summary</div>
        <div class="card-content">{summary}</div>
    </div>
    """, unsafe_allow_html=True)


def render_keypoints_card(points: list):
    """Render the key points section with a green-themed card."""
    bullets = "".join(f"<li>{point}</li>" for point in points)
    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title card-keypoints">🎯 Key Points</div>
        <div class="card-content"><ul>{bullets}</ul></div>
    </div>
    """, unsafe_allow_html=True)


def render_terms_card(terms: list):
    """Render the important terms section with pill-shaped badges."""
    badges = "".join(f'<span class="term-badge">{term}</span>' for term in terms)
    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title card-terms">🔑 Important Terms</div>
        <div class="card-content">{badges}</div>
    </div>
    """, unsafe_allow_html=True)


def render_quiz_card(quiz: list):
    """Render quiz questions — each item rendered separately to avoid HTML truncation."""
    st.markdown("""
    <div class="glass-card" style="padding-bottom: 0.5rem;">
        <div class="card-title card-quiz">❓ Quiz Questions</div>
    """, unsafe_allow_html=True)
    for i, q in enumerate(quiz, 1):
        question = q.get("question", "")
        answer = q.get("answer", "")
        st.markdown(f"""
        <div class="quiz-block">
            <strong>Q{i}:</strong> {question}<br>
            <details style="margin-top: 0.5rem; cursor: pointer;">
                <summary style="color: #fca5a5; font-weight: 500;">💡 Show Answer</summary>
                <p style="margin-top: 0.5rem; padding-left: 0.5rem;">{answer}</p>
            </details>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_flashcards(flashcards: list):
    """Render flashcards — each card rendered separately to avoid HTML truncation."""
    st.markdown("""
    <div class="glass-card" style="padding-bottom: 0.5rem;">
        <div class="card-title card-flashcards">🃏 Flashcards</div>
    """, unsafe_allow_html=True)
    for i, fc in enumerate(flashcards, 1):
        front = fc.get("front", "")
        back = fc.get("back", "")
        st.markdown(f"""
        <div class="flashcard-block">
            <div class="flashcard-q">📄 Card {i}: {front}</div>
            <details style="cursor: pointer;">
                <summary style="color: #93c5fd; font-weight: 500;">Flip Card →</summary>
                <div class="flashcard-a" style="margin-top: 0.5rem;">{back}</div>
            </details>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def build_copy_text(results: dict) -> str:
    """Build a plain-text version of all results for easy copying."""
    text = "📚 AI STUDY NOTES SUMMARY\n"
    text += "=" * 40 + "\n\n"

    text += "📝 SUMMARY\n"
    text += results.get("summary", "") + "\n\n"

    text += "🎯 KEY POINTS\n"
    for pt in results.get("key_points", []):
        text += f"  • {pt}\n"
    text += "\n"

    text += "🔑 IMPORTANT TERMS\n"
    text += ", ".join(results.get("terms", [])) + "\n\n"

    text += "❓ QUIZ QUESTIONS\n"
    for i, q in enumerate(results.get("quiz", []), 1):
        text += f"  Q{i}: {q.get('question', '')}\n"
        text += f"  A{i}: {q.get('answer', '')}\n\n"

    text += "🃏 FLASHCARDS\n"
    for i, fc in enumerate(results.get("flashcards", []), 1):
        text += f"  Card {i} — Q: {fc.get('front', '')}\n"
        text += f"           A: {fc.get('back', '')}\n\n"

    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_sidebar():
    """Render the sidebar with app info, features, and instructions."""
    with st.sidebar:
        st.markdown("## 🧠 Study Summarizer")
        st.markdown(
            "<p style='color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-top: -10px;'>"
            "Powered by AI</p>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Mode indicator ──
        api_available = has_api_key()
        if api_available:
            st.markdown(
                '<div style="background: rgba(52, 211, 153, 0.15); border: 1px solid rgba(52, 211, 153, 0.3); '
                'border-radius: 10px; padding: 0.6rem 1rem; text-align: center; margin-bottom: 1rem;">'
                '🟢 <strong style="color: #34d399;">AI Mode Active</strong><br>'
                '<span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Using Google Gemini (Free)</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background: rgba(251, 191, 36, 0.12); border: 1px solid rgba(251, 191, 36, 0.3); '
                'border-radius: 10px; padding: 0.6rem 1rem; text-align: center; margin-bottom: 1rem;">'
                '🟡 <strong style="color: #fbbf24;">Demo Mode</strong><br>'
                '<span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">'
                'No API key needed · Works instantly</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown("### ✨ Features")
        features = [
            "📝 Concise summaries",
            "🎯 Key points extraction",
            "🔑 Important terms & keywords",
            "❓ Quiz questions for revision",
            "🃏 Flashcards for quick study",
            "📄 PDF/DOCX/TXT upload",
            "🎮 Interactive quiz mode",
            "📥 PDF export",
        ]
        for f in features:
            st.markdown(
                f'<div class="feature-item">{f}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown("### 📖 How to Use")
        st.markdown("""
        1. **Paste** your study notes into the text area
        2. Click **"✨ Summarize Notes"**
        3. Review the AI-generated results
        4. Use **quiz questions** and **flashcards** to study!
        """)

        st.markdown("---")

        st.markdown("### 💡 Tips")
        st.markdown("""
        - Paste at least **100 words** for best results
        - Works with any subject — science, history, CS, etc.
        - Use the **Copy Results** section to save your output
        """)

        if not api_available:
            st.markdown("---")
            st.markdown("### 🔑 Enable AI Mode (Free!)")
            st.markdown("""
            To use real AI summarization:
            1. Go to [aistudio.google.com](https://aistudio.google.com/apikey)
            2. Click **"Create API Key"** (it's free!)
            3. Create a `.env` file in the project folder
            4. Add: `GOOGLE_API_KEY=your_key_here`
            5. Restart the app
            """)

        st.markdown("---")

        # ── Pomodoro Timer ──
        render_pomodoro_timer()

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: rgba(255,255,255,0.3); font-size: 0.75rem;'>"
            "v2.0 · Made with ❤️ for students</p>",
            unsafe_allow_html=True,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Main function that runs the Streamlit app."""

    # ── Inject CSS & render sidebar ──
    inject_custom_css()
    render_sidebar()

    # ── Hero Header ──
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">🧠 AI Study Notes Summarizer</h1>
        <p class="hero-subtitle">
            Turn long notes into summaries, key points, and practice questions instantly
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Initialize session state for storing results ──
    if "results" not in st.session_state:
        st.session_state.results = None
    if "notes_input" not in st.session_state:
        st.session_state.notes_input = ""
    if "notes_count" not in st.session_state:
        st.session_state.notes_count = 0
    if "words_processed" not in st.session_state:
        st.session_state.words_processed = 0

    # ── Progress Dashboard ──
    render_progress_dashboard()
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Notes Input Section ──
    st.markdown(
        '<p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; font-weight: 600; '
        'margin-bottom: 0.5rem;">📋 Paste your study notes or upload a file</p>',
        unsafe_allow_html=True,
    )

    # ── File Upload ──
    uploaded_file = st.file_uploader(
        "Upload study notes",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        help="Upload a PDF, Word document, or text file",
    )

    file_text = ""
    if uploaded_file is not None:
        file_text = extract_text_from_file(uploaded_file)
        if file_text:
            st.success(f"✅ Extracted {len(file_text.split())} words from **{uploaded_file.name}**")

    notes = st.text_area(
        label="Study Notes",
        height=200,
        value=file_text if file_text else "",
        placeholder="Paste your lecture notes, textbook excerpts, or study material here...",
        key="notes_area",
        label_visibility="collapsed",
    )

    # ── Word & Character Count ──
    if notes:
        word_count = len(notes.split())
        char_count = len(notes)
        st.markdown(f"""
        <div class="stats-bar">
            <span class="stat-badge">📊 {word_count} words</span>
            <span class="stat-badge">🔤 {char_count} characters</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Action Buttons ──
    col1, col2, col3 = st.columns([1.5, 1, 4])

    with col1:
        summarize_clicked = st.button("✨ Summarize Notes", type="primary", use_container_width=True)

    with col2:
        clear_clicked = st.button("🗑️ Clear", type="secondary", use_container_width=True)

    # ── Handle Clear ──
    if clear_clicked:
        st.session_state.results = None
        st.rerun()

    # ── Divider ──
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Handle Summarize ──
    if summarize_clicked:
        # Validate input
        if not notes or len(notes.strip()) < 30:
            st.warning("⚠️ Please paste at least a few sentences of study notes to summarize.")
        else:
            # Decide: Demo mode or AI mode
            use_ai = has_api_key()
            spinner_msg = (
                "🧠 AI is analyzing your notes... This may take a moment."
                if use_ai
                else "🧠 Processing your notes in demo mode..."
            )

            with st.spinner(spinner_msg):
                try:
                    if use_ai:
                        results = get_ai_summary(notes)
                    else:
                        results = get_demo_results(notes)

                    st.session_state.results = results

                    # Track progress stats
                    st.session_state.notes_count += 1
                    st.session_state.words_processed += len(notes.split())

                    if use_ai:
                        st.success("✅ Your notes have been summarized using AI!")
                    else:
                        st.success("✅ Demo results generated! Add a free Google API key for real AI summaries.")

                except json.JSONDecodeError:
                    st.error("❌ The AI returned an unexpected format. Please try again.")
                except Exception as e:
                    st.error(f"❌ Something went wrong: {str(e)}")

    # ── Display Results ──
    if st.session_state.results:
        results = st.session_state.results

        # ── Tabbed Results View ──
        tab1, tab2, tab3 = st.tabs(["📝 Results", "🎮 Interactive Quiz", "📥 Export"])

        with tab1:
            # ── Summary & Key Points — side by side ──
            left, right = st.columns(2)
            with left:
                render_summary_card(results.get("summary", "No summary available."))
            with right:
                render_keypoints_card(results.get("key_points", []))

            # ── Important Terms ──
            render_terms_card(results.get("terms", []))

            # ── Quiz & Flashcards — side by side ──
            left2, right2 = st.columns(2)
            with left2:
                render_quiz_card(results.get("quiz", []))
            with right2:
                render_flashcards(results.get("flashcards", []))

        with tab2:
            # ── Interactive Quiz Mode ──
            render_interactive_quiz(results.get("quiz", []))

        with tab3:
            # ── PDF Export ──
            st.markdown("""
            <div class="glass-card">
                <div class="card-title" style="color: #60a5fa;">📥 Export Your Study Notes</div>
                <div class="card-content">
                    Download a formatted PDF with all your summarized notes, key points, quiz questions, and flashcards.
                </div>
            </div>
            """, unsafe_allow_html=True)

            pdf_bytes = generate_pdf_report(results)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"study_notes_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

            # ── Copy Results Section ──
            with st.expander("📋 Copy All Results (Plain Text)", expanded=False):
                copy_text = build_copy_text(results)
                st.code(copy_text, language=None)

    # ── Footer ──
    st.markdown("""
    <div class="app-footer">
        🧠 AI Study Notes Summarizer · Built for students using AI<br>
        <span style="font-size: 0.75rem;">Powered by Google Gemini · Made with Streamlit</span>
    </div>
    """, unsafe_allow_html=True)


# ── Run the app ──
if __name__ == "__main__":
    main()
