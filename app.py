"""
StudyMate — Learn Anything  (Phase 3: Q&A, Export, Session History)

Main Streamlit entry point. Features:
  - Multi-source content extraction (YouTube, PDF, Word, Text)
  - AI summary and smart notes via Gemini 1.5 Flash
  - Interactive quiz generator with scoring
  - Export to TXT / Markdown / HTML study sheet
  - Session history with restore

Run with:
    streamlit run app.py
"""

import re
from datetime import datetime

import streamlit as st

from utils.file_handler import route_input
from utils.exporter import export_to_txt, export_to_md, export_to_pdf_html
from ai.gemini_client import AIClient, PROVIDERS, PROVIDER_NAMES
from ai.processors import ContentProcessor

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyMate — Learn Anything",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Session state initialisation ─────────────────────────────────────
if "history" not in st.session_state:
    st.session_state["history"] = []
if "quiz_answers" not in st.session_state:
    st.session_state["quiz_answers"] = {}
if "quiz_submitted" not in st.session_state:
    st.session_state["quiz_submitted"] = {}
if "quiz_current" not in st.session_state:
    st.session_state["quiz_current"] = 0

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: #ffffff;
    }
    .hero-header h1 { margin: 0 0 0.25rem 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.5px; }
    .hero-header p  { margin: 0; font-size: 1.05rem; opacity: 0.9; }

    .success-card {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 1.2rem 1.5rem; border-radius: 12px;
        color: #fff; font-weight: 600; font-size: 1.05rem; margin: 1rem 0;
    }

    .section-card {
        background: #fff;
        border-radius: 14px;
        padding: 20px 24px;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #e8eaf0;
    }

    .ai-section-header {
        background: linear-gradient(135deg, #4e54c8 0%, #8f94fb 100%);
        padding: 1rem 1.5rem; border-radius: 12px; color: #fff;
        text-align: center; font-weight: 700; font-size: 1.15rem;
        margin: 2rem 0 1rem 0; letter-spacing: -0.3px;
    }
    .export-section-header {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem 1.5rem; border-radius: 12px; color: #fff;
        text-align: center; font-weight: 700; font-size: 1.1rem;
        margin: 2rem 0 1rem 0;
    }

    /* Source type badges */
    .badge-youtube { background:#ef4444; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
    .badge-pdf     { background:#3b82f6; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
    .badge-word    { background:#0d9488; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
    .badge-text    { background:#6b7280; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }

    /* Quiz */
    .quiz-correct   { background:#dcfce7; border-left:4px solid #16a34a; border-radius:0 8px 8px 0; padding:10px 16px; margin-top:8px; color:#15803d; font-weight:600; }
    .quiz-incorrect { background:#fee2e2; border-left:4px solid #dc2626; border-radius:0 8px 8px 0; padding:10px 16px; margin-top:8px; color:#b91c1c; font-weight:600; }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff; border-radius: 16px; padding: 2rem;
        text-align: center; margin: 1rem 0;
    }
    .score-card h2 { font-size: 2rem; margin-bottom: 0.5rem; }
    .score-card p  { font-size: 1.1rem; opacity: 0.9; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e2f 0%, #2d2d44 100%);
    }
    section[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

    .rate-limit-note {
        background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px; padding: 0.6rem 0.9rem;
        font-size: 0.82rem; margin-top: 0.5rem; opacity: 0.85;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"]      { border-radius: 8px 8px 0 0; font-weight: 600; }

    button[kind="primary"] { transition: transform 0.15s ease, box-shadow 0.15s ease; }
    button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helper: source type badge ─────────────────────────────────────────
def _source_badge(source_type: str) -> str:
    """Return an HTML badge span for the given source type."""
    labels = {"youtube": "YouTube", "pdf": "PDF", "word": "Word", "text": "Text"}
    label = labels.get(source_type, source_type.upper())
    return f'<span class="badge-{source_type}">{label}</span>'


# ── Helper: get or create ContentProcessor ───────────────────────────
def _make_processor() -> ContentProcessor:
    """Build a ContentProcessor from the session API key and provider."""
    provider = st.session_state.get("ai_provider", PROVIDER_NAMES[0])
    return ContentProcessor(AIClient(st.session_state["api_key"], provider_name=provider))


# ── Helper: run AI call with progress bar ────────────────────────────
def _run_with_progress(label: str, fn, *args):
    """Run fn(*args) inside a spinner+progress bar, return result."""
    provider = st.session_state.get("ai_provider", PROVIDER_NAMES[0])
    with st.spinner(f"🧠 AI is thinking… ({label})"):
        bar = st.progress(0, text="Initializing AI…")
        bar.progress(20, text="Preparing content…")
        bar.progress(40, text=f"Sending to {provider}…")
        result = fn(*args)
        bar.progress(90, text="Formatting results…")
        bar.progress(100, text="Done!")
    return result


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://em-content.zobj.net/source/twitter/376/books_1f4da.png", width=72)
    st.markdown("## StudyMate")
    st.markdown(
        "Your all-in-one content extraction & AI study tool. "
        "Extract text, generate summaries, notes, and quizzes — all free."
    )
    st.divider()

    # AI Configuration
    st.markdown("### 🔐 AI Configuration")

    # Provider selector
    selected_provider = st.selectbox(
        "🤖 AI Provider",
        options=PROVIDER_NAMES,
        index=0,
        key="ai_provider",
        help="Groq is recommended — free, fast, works globally.",
    )
    provider_info = PROVIDERS[selected_provider]
    key_url = provider_info["key_url"]

    # API Key input
    api_key_input = st.text_input(
        "🔑 API Key",
        type="password",
        help=f"Get a free key at {key_url}",
        key="api_key_input",
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.markdown('<span style="color:#00c853;font-weight:600;">✅ API key entered</span>', unsafe_allow_html=True)
    else:
        st.session_state.pop("api_key", None)
        st.markdown('<span style="color:#ff5252;font-weight:600;">❌ No API key</span>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="rate-limit-note">ℹ️ {provider_info["note"]} '
        f'<a href="{key_url}" style="color:#8f94fb;" target="_blank">'
        f'Get a free key →</a></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # How to use
    st.markdown("### 📖 How to use")
    st.markdown(
        "1. Select a provider and enter your API key.\n"
        "2. Choose a source tab and extract content.\n"
        "3. Generate Summary, Notes, or a Quiz.\n"
        "4. Export everything as a study sheet.\n"
    )
    st.divider()

    # Session History
    history = st.session_state.get("history", [])
    with st.expander(f"📂 Session History ({len(history)})"):
        if not history:
            st.caption("No history yet. Extract content to begin.")
        else:
            for i, item in enumerate(reversed(history)):
                idx = len(history) - 1 - i
                label = f"{item['source_type'].upper()} · {item['title'][:26]}"
                if st.button(f"📄 {label}", key=f"hist_{idx}", help=item.get("timestamp", "")):
                    st.session_state["extracted_content"] = {
                        "title": item["title"],
                        "content": item.get("content", ""),
                        "source_type": item["source_type"],
                        "word_count": item.get("word_count", 0),
                    }
                    if item.get("summary"):
                        st.session_state["summary"] = {"summary": item["summary"], "token_estimate": 0}
                    if item.get("notes"):
                        st.session_state["notes"] = {"notes": item["notes"]}
                    if item.get("qna"):
                        st.session_state["quiz"] = {"qna": item["qna"], "quiz_title": item.get("quiz_title", "Quiz")}
                        st.session_state["quiz_answers"] = {}
                        st.session_state["quiz_submitted"] = {}
                        st.session_state["quiz_current"] = 0
                    st.rerun()
    st.divider()

    # About
    with st.expander("ℹ️ About StudyMate"):
        st.markdown(
            "**Version:** 1.0.0  \n"
            "**Free APIs:** Gemini 1.5 Flash  \n"
            "**GitHub:** [github.com/your-username/studymate](#)  \n"
            "Built with ❤️ using Streamlit"
        )

# ── Hero header ───────────────────────────────────────────────────────
st.markdown(
    '<div class="hero-header">'
    "<h1>📚 StudyMate</h1>"
    "<p>Extract · Summarize · Quiz · Export — Powered by Gemini 1.5 Flash (free)</p>"
    "</div>",
    unsafe_allow_html=True,
)


# ── Helper: show extraction results ──────────────────────────────────
def _show_results(result: dict) -> None:
    """
    Store extraction in session state, render success card, content
    preview, and clear any prior AI outputs.
    """
    st.session_state["extracted_content"] = result
    for key in ("summary", "notes", "quiz"):
        st.session_state.pop(key, None)
    st.session_state["quiz_answers"]   = {}
    st.session_state["quiz_submitted"] = {}
    st.session_state["quiz_current"]   = 0

    badge = _source_badge(result["source_type"])
    st.markdown(
        f'<div class="success-card">✅ Extracted <strong>{result["word_count"]:,}</strong> words '
        f'from <em>{result["title"]}</em> &nbsp;{badge}</div>',
        unsafe_allow_html=True,
    )
    if result["word_count"] > 12000:
        st.warning("⚠️ Content is long — AI will analyze the first ~12,000 words.")

    with st.expander("📋 Extracted Content Preview", expanded=True):
        preview = result["content"][:1000]
        if len(result["content"]) > 1000:
            preview += "\n\n… (truncated)"
        st.text(preview)

    st.toast("✅ Content extracted successfully!")


# ── Source Extraction Tabs ────────────────────────────────────────────
tab_yt, tab_pdf, tab_word, tab_txt = st.tabs(
    ["🎥 YouTube", "📄 PDF", "📝 Word Doc", "🔤 Text File"]
)

with tab_yt:
    st.subheader("Extract transcript from a YouTube video")
    yt_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        key="yt_url_input",
    )
    if st.button("Extract", key="yt_extract_btn", type="primary"):
        if not yt_url.strip():
            st.error("Please enter a YouTube URL before clicking Extract.")
        else:
            with st.spinner("Fetching transcript…"):
                try:
                    _show_results(route_input("youtube", yt_url.strip()))
                except (ValueError, RuntimeError) as exc:
                    msg = str(exc)
                    if "transcript" in msg.lower():
                        st.error(f"❌ {msg}\n\n💡 Tip: Try a different video or paste the transcript manually in the Text File tab.")
                    else:
                        st.error(f"❌ {msg}")

with tab_pdf:
    st.subheader("Upload a PDF document")
    pdf_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_uploader")
    if pdf_file is not None:
        with st.spinner("Extracting text from PDF…"):
            try:
                _show_results(route_input("pdf", pdf_file))
            except (ValueError, RuntimeError) as exc:
                st.error(f"❌ {exc}")

with tab_word:
    st.subheader("Upload a Word document")
    word_file = st.file_uploader("Choose a .docx file", type=["docx"], key="word_uploader")
    if word_file is not None:
        with st.spinner("Extracting text from Word document…"):
            try:
                _show_results(route_input("word", word_file))
            except (ValueError, RuntimeError) as exc:
                st.error(f"❌ {exc}")

with tab_txt:
    st.subheader("Upload a plain-text file")
    txt_file = st.file_uploader("Choose a .txt file", type=["txt"], key="txt_uploader")
    if txt_file is not None:
        with st.spinner("Reading text file…"):
            try:
                _show_results(route_input("text", txt_file))
            except (ValueError, RuntimeError) as exc:
                st.error(f"❌ {exc}")


# ═══════════════════════════════════════════════════════════════
# HELPER: update session history
# ═══════════════════════════════════════════════════════════════
def _update_history(
    extracted: dict,
    summary: str = "",
    notes: str = "",
    qna: list = None,
    quiz_title: str = "",
) -> None:
    """
    Upsert the current extraction into st.session_state["history"].
    If an entry with the same title already exists, update it in place;
    otherwise append a new record.

    Args:
        extracted:  The current extracted_content dict.
        summary:    AI summary string (optional).
        notes:      AI notes string (optional).
        qna:        List of Q&A dicts (optional).
        quiz_title: Title of the quiz (optional).
    """
    hist = st.session_state.setdefault("history", [])
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Find existing entry by title to avoid duplicates
    for entry in hist:
        if entry["title"] == extracted["title"]:
            if summary:
                entry["summary"]    = summary
            if notes:
                entry["notes"]      = notes
            if qna is not None:
                entry["qna"]        = qna
                entry["quiz_title"] = quiz_title
            entry["timestamp"] = ts
            return

    # New entry
    hist.append({
        "title":      extracted["title"],
        "source_type": extracted["source_type"],
        "content":    extracted.get("content", ""),
        "word_count": extracted.get("word_count", 0),
        "timestamp":  ts,
        "summary":    summary,
        "notes":      notes,
        "qna":        qna or [],
        "quiz_title": quiz_title,
    })


# ═══════════════════════════════════════════════════════════════
# AI ANALYSIS SECTION — only shown after content is extracted
# ═══════════════════════════════════════════════════════════════
if "extracted_content" in st.session_state:
    extracted   = st.session_state["extracted_content"]
    has_api_key = bool(st.session_state.get("api_key"))

    st.markdown('<div class="ai-section-header">🤖 AI Analysis</div>', unsafe_allow_html=True)

    if not has_api_key:
        st.info("🔑 Enter your Gemini API key in the sidebar to unlock AI features.")

    # ── Three action buttons ──────────────────────────────────────────
    col_s, col_n, col_q = st.columns(3)
    with col_s:
        btn_summary = st.button("📋 Generate Summary", key="btn_summary",
                                type="primary", disabled=not has_api_key,
                                use_container_width=True)
    with col_n:
        btn_notes = st.button("📝 Generate Notes", key="btn_notes",
                              type="primary", disabled=not has_api_key,
                              use_container_width=True)
    with col_q:
        btn_quiz = st.button("🎯 Generate Quiz", key="btn_quiz",
                             type="primary", disabled=not has_api_key,
                             use_container_width=True)

    # ── Quiz controls (shown when quiz button is about to be clicked) ─
    if has_api_key:
        with st.expander("⚙️ Quiz Settings", expanded=False):
            qc1, qc2 = st.columns(2)
            with qc1:
                quiz_difficulty = st.select_slider(
                    "Difficulty",
                    options=["Easy", "Medium", "Hard", "Mixed"],
                    value="Mixed",
                    key="quiz_difficulty",
                )
            with qc2:
                quiz_num_q = st.radio(
                    "Number of questions",
                    options=[5, 10, 15],
                    horizontal=True,
                    key="quiz_num_q",
                )

    # ── Generate Summary ──────────────────────────────────────────────
    if btn_summary and has_api_key:
        try:
            processor = _make_processor()
            result = _run_with_progress(
                "Summary",
                processor.summarize,
                extracted["content"],
                extracted["source_type"],
            )
            st.session_state["summary"] = result
            # Update history
            _update_history(extracted, summary=result["summary"])
            st.toast("🧠 Summary generated!")
        except (ValueError, RuntimeError) as exc:
            st.error(f"❌ AI Error: {exc}")
        except Exception as exc:
            if "timeout" in str(exc).lower():
                st.error("⏱ Request timed out. Please try again.")
            else:
                st.error(f"❌ Unexpected error: {exc}")

    # ── Generate Notes ────────────────────────────────────────────────
    if btn_notes and has_api_key:
        try:
            processor = _make_processor()
            result = _run_with_progress(
                "Notes",
                processor.generate_notes,
                extracted["content"],
                extracted["source_type"],
            )
            st.session_state["notes"] = result
            _update_history(extracted, notes=result["notes"])
            st.toast("📝 Notes ready!")
        except (ValueError, RuntimeError) as exc:
            st.error(f"❌ AI Error: {exc}")
        except Exception as exc:
            if "timeout" in str(exc).lower():
                st.error("⏱ Request timed out. Please try again.")
            else:
                st.error(f"❌ Unexpected error: {exc}")

    # ── Generate Quiz ─────────────────────────────────────────────────
    if btn_quiz and has_api_key:
        difficulty = st.session_state.get("quiz_difficulty", "Mixed")
        num_q      = st.session_state.get("quiz_num_q", 5)
        try:
            processor = _make_processor()
            result = _run_with_progress(
                "Quiz",
                processor.generate_qna,
                extracted["content"],
                extracted["source_type"],
                difficulty,
                num_q,
            )
            st.session_state["quiz"]           = result
            st.session_state["quiz_answers"]   = {}
            st.session_state["quiz_submitted"] = {}
            st.session_state["quiz_current"]   = 0
            _update_history(extracted, qna=result["qna"], quiz_title=result["quiz_title"])
            st.toast("🎯 Quiz created!")
        except (ValueError, RuntimeError) as exc:
            st.error(f"❌ AI Error: {exc}")
        except Exception as exc:
            if "timeout" in str(exc).lower():
                st.error("⏱ Request timed out. Please try again.")
            else:
                st.error(f"❌ Unexpected error: {exc}")

    # ── Display results in tabs ───────────────────────────────────────
    has_summary = "summary" in st.session_state
    has_notes   = "notes"   in st.session_state
    has_quiz    = "quiz"    in st.session_state

    if has_summary or has_notes or has_quiz:
        ai_tab_s, ai_tab_n, ai_tab_q = st.tabs(["📋 Summary", "📝 Smart Notes", "🎯 Quiz Me"])

        # ── Summary tab ───────────────────────────────────────────────
        with ai_tab_s:
            if has_summary:
                sdata = st.session_state["summary"]
                st.markdown(sdata["summary"])
                st.caption(f"📊 Estimated input tokens: ~{sdata['token_estimate']:,}")
                st.download_button(
                    "⬇️ Download Summary",
                    data=sdata["summary"],
                    file_name=f"studymate_summary_{extracted['title']}.txt",
                    mime="text/plain",
                    key="dl_summary",
                )
            else:
                st.info("Click **Generate Summary** above to create an AI summary.")

        # ── Notes tab ─────────────────────────────────────────────────
        with ai_tab_n:
            if has_notes:
                ndata = st.session_state["notes"]
                st.markdown(ndata["notes"])
                st.download_button(
                    "⬇️ Download Notes",
                    data=ndata["notes"],
                    file_name=f"studymate_notes_{extracted['title']}.txt",
                    mime="text/plain",
                    key="dl_notes",
                )
            else:
                st.info("Click **Generate Notes** above to create AI study notes.")

        # ── Quiz tab ──────────────────────────────────────────────────
        with ai_tab_q:
            if not has_quiz:
                st.info("Click **Generate Quiz** above, then set difficulty and question count.")
            else:
                quiz_data  = st.session_state["quiz"]
                questions  = quiz_data["qna"]
                quiz_title = quiz_data["quiz_title"]
                total      = len(questions)
                answers    = st.session_state["quiz_answers"]
                submitted  = st.session_state["quiz_submitted"]

                st.markdown(f"### 🎯 {quiz_title}")

                # ── Score card (when all answered) ───────────────────
                if len(submitted) == total and total > 0:
                    # Calculate score with better matching
                    results = []
                    for qid_i in range(total):
                        q_item = questions[qid_i]
                        user_a = answers.get(qid_i, "").strip()
                        correct_a = q_item["correct_answer"].strip()
                        # For MCQ: match the option letter/text
                        if q_item.get("type") == "mcq":
                            is_right = (
                                user_a.lower() == correct_a.lower()
                                or user_a.lower().startswith(correct_a[:2].lower())
                                or correct_a.lower().startswith(user_a[:2].lower())
                            )
                        else:
                            # Short answer: check if key words match
                            is_right = user_a.lower() in correct_a.lower() or correct_a.lower() in user_a.lower()
                        results.append({
                            "question": q_item["question"],
                            "type": q_item.get("type", "mcq"),
                            "user_answer": user_a,
                            "correct_answer": correct_a,
                            "explanation": q_item.get("explanation", ""),
                            "is_correct": is_right,
                        })

                    score = sum(1 for r in results if r["is_correct"])
                    pct = score / total
                    grade = (
                        "🏆 Excellent!" if pct >= 0.9 else
                        "👍 Good job!" if pct >= 0.7 else
                        "📖 Keep Studying" if pct >= 0.5 else
                        "💪 Review the material"
                    )

                    # Score card header
                    st.markdown(
                        f'<div class="score-card">'
                        f'<h2>You scored {score}/{total}</h2>'
                        f'<p>{grade} &nbsp;·&nbsp; {pct*100:.0f}%</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Detailed question-by-question report
                    st.markdown("### 📊 Detailed Quiz Report")
                    st.markdown("---")

                    for idx_r, r in enumerate(results):
                        icon = "✅" if r["is_correct"] else "❌"
                        q_type_label = "MCQ" if r["type"] == "mcq" else "Short Answer"

                        st.markdown(f"**{icon} Q{idx_r+1}: {r['question']}**")
                        st.markdown(f"*Type: {q_type_label}*")

                        col_your, col_correct = st.columns(2)
                        with col_your:
                            if r["is_correct"]:
                                st.success(f"Your answer: {r['user_answer']}")
                            else:
                                st.error(f"Your answer: {r['user_answer']}")
                        with col_correct:
                            st.info(f"Correct answer: {r['correct_answer']}")

                        if r["explanation"]:
                            st.caption(f"💬 Explanation: {r['explanation']}")
                        st.markdown("---")

                    # Summary stats
                    correct_count = sum(1 for r in results if r["is_correct"])
                    wrong_count = total - correct_count

                    stat_cols = st.columns(4)
                    with stat_cols[0]:
                        st.metric("Total Questions", total)
                    with stat_cols[1]:
                        st.metric("✅ Correct", correct_count)
                    with stat_cols[2]:
                        st.metric("❌ Wrong", wrong_count)
                    with stat_cols[3]:
                        st.metric("Score %", f"{pct*100:.0f}%")

                    # Wrong answers summary
                    wrong_questions = [r for r in results if not r["is_correct"]]
                    if wrong_questions:
                        st.markdown("### 📝 Topics to Review")
                        st.warning(
                            "Focus on these questions you got wrong:\n\n" +
                            "\n".join(
                                f"- **Q{results.index(r)+1}**: {r['question']}"
                                for r in wrong_questions
                            )
                        )

                    # Action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("🔄 Retake Quiz", key="retake_quiz", type="primary", use_container_width=True):
                            st.session_state["quiz_answers"] = {}
                            st.session_state["quiz_submitted"] = {}
                            st.session_state["quiz_current"] = 0
                            st.rerun()
                    with btn_col2:
                        if st.button("🆕 New Quiz", key="new_quiz", use_container_width=True):
                            st.session_state.pop("quiz", None)
                            st.session_state["quiz_answers"] = {}
                            st.session_state["quiz_submitted"] = {}
                            st.session_state["quiz_current"] = 0
                            st.rerun()

                else:
                    # Progress bar
                    done = len(submitted)
                    st.progress(done / total if total else 0,
                                text=f"Question {done + 1} of {total}")

                    # Current question
                    cur_idx = st.session_state.get("quiz_current", 0)
                    if cur_idx >= total:
                        cur_idx = total - 1
                    q = questions[cur_idx]
                    qid = cur_idx

                    # Navigation pills
                    nav_cols = st.columns(min(total, 10))
                    for ni in range(total):
                        status = "✅" if ni in submitted else ("▶" if ni == cur_idx else "○")
                        with nav_cols[ni % 10]:
                            if st.button(status, key=f"nav_{ni}", help=f"Q{ni+1}"):
                                st.session_state["quiz_current"] = ni
                                st.rerun()

                    st.divider()
                    q_type_display = "🔵 MCQ" if q["type"] == "mcq" else "✏️ Short Answer"
                    st.markdown(f"**Q{cur_idx+1}/{total}: {q['question']}** &nbsp; *({q_type_display})*")

                    already_submitted = qid in submitted

                    if q["type"] == "mcq" and q.get("options"):
                        user_ans = st.radio(
                            "Select your answer:",
                            options=q["options"],
                            key=f"ans_{qid}",
                            disabled=already_submitted,
                        )
                    else:
                        user_ans = st.text_area(
                            "Your answer:",
                            key=f"ans_{qid}",
                            height=100,
                            disabled=already_submitted,
                        )

                    if not already_submitted:
                        sub_col1, sub_col2 = st.columns([1, 3])
                        with sub_col1:
                            if st.button("Submit Answer", key=f"submit_{qid}", type="primary"):
                                answers[qid] = user_ans or ""
                                submitted[qid] = True
                                st.session_state["quiz_answers"] = answers
                                st.session_state["quiz_submitted"] = submitted
                                # Auto-advance to next question
                                if cur_idx < total - 1:
                                    st.session_state["quiz_current"] = cur_idx + 1
                                st.rerun()
                    else:
                        correct_ans = q["correct_answer"]
                        user_a_check = answers.get(qid, "").strip().lower()
                        correct_a_check = correct_ans.strip().lower()
                        if q["type"] == "mcq":
                            is_correct = (
                                user_a_check == correct_a_check
                                or user_a_check.startswith(correct_a_check[:2])
                                or correct_a_check.startswith(user_a_check[:2])
                            )
                        else:
                            is_correct = user_a_check in correct_a_check or correct_a_check in user_a_check

                        if is_correct:
                            st.markdown(
                                f'<div class="quiz-correct">✅ Correct! &nbsp; {correct_ans}</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div class="quiz-incorrect">❌ Incorrect. '
                                f'Correct answer: {correct_ans}</div>',
                                unsafe_allow_html=True,
                            )
                        st.info(f"💬 {q.get('explanation', '')}")

                        # Next button
                        remaining = total - len(submitted)
                        if cur_idx < total - 1:
                            if st.button(f"Next Question → ({remaining} remaining)", key=f"next_{qid}"):
                                st.session_state["quiz_current"] = cur_idx + 1
                                st.rerun()
                        elif remaining == 0:
                            st.success("🎉 All questions answered! Scroll up to see your detailed report.")
                            if st.button("📊 View Full Report", key="view_score", type="primary"):
                                st.rerun()


# ═══════════════════════════════════════════════════════════════
# EXPORT SECTION — shown only when all three AI outputs exist
# ═══════════════════════════════════════════════════════════════
if (
    "extracted_content" in st.session_state
    and "summary" in st.session_state
    and "notes"   in st.session_state
    and "quiz"    in st.session_state
):
    extracted  = st.session_state["extracted_content"]
    title      = extracted["title"]
    summary    = st.session_state["summary"]["summary"]
    notes      = st.session_state["notes"]["notes"]
    qna        = st.session_state["quiz"]["qna"]
    date_slug  = datetime.now().strftime("%Y%m%d")

    st.markdown(
        '<div class="export-section-header">📥 Export Everything</div>',
        unsafe_allow_html=True,
    )

    ex_col1, ex_col2, ex_col3 = st.columns(3)

    with ex_col1:
        st.download_button(
            label="⬇️ Download .TXT",
            data=export_to_txt(title, summary, notes, qna),
            file_name=f"studymate_{title}_{date_slug}.txt",
            mime="text/plain",
            key="dl_export_txt",
            use_container_width=True,
        )

    with ex_col2:
        st.download_button(
            label="⬇️ Download .MD",
            data=export_to_md(title, summary, notes, qna),
            file_name=f"studymate_{title}_{date_slug}.md",
            mime="text/markdown",
            key="dl_export_md",
            use_container_width=True,
        )

    with ex_col3:
        html_content = export_to_pdf_html(title, summary, notes, qna)
        st.download_button(
            label="⬇️ Download Study Sheet (HTML)",
            data=html_content.encode("utf-8"),
            file_name=f"studymate_{title}_{date_slug}.html",
            mime="text/html",
            key="dl_export_html",
            use_container_width=True,
        )

    st.caption(
        "💡 Open the HTML file in your browser and use **File → Print → Save as PDF** "
        "to generate a PDF study sheet."
    )
