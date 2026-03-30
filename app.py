import streamlit as st
import os
import pandas as pd
import numpy as np
import re
import io

from extraction import extract_exam_questions
from processing import process_lecture
from database import load_model, init_db, store_lecture
from scoring import (
    calculate_topic_importance, 
    calculate_gap_analysis, 
    calculate_year_over_year_trends
)
from visualization import (
    create_bar_chart, 
    create_pie_chart,
    create_gap_analysis_chart,
    create_year_over_year_heatmap,
    create_similarity_distribution_chart,
    create_confidence_scatter,
    create_topic_ranking_sunburst,
    create_file_contribution_bar,
    create_topic_card
)

try:
    from fpdf import FPDF
    PDF_EXPORT_AVAILABLE = True
except ImportError:
    FPDF = None
    PDF_EXPORT_AVAILABLE = False


STOP_WORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "your", "their", "are",
    "was", "were", "have", "has", "had", "will", "would", "could", "should", "about", "which",
    "when", "where", "what", "why", "how", "all", "any", "can", "each", "more", "less", "than",
    "using", "used", "use", "based", "over", "under", "between", "topic", "topics", "system", "data"
}


def _normalize_topic(topic_text):
    cleaned = re.sub(r"\s+", " ", str(topic_text or "")).strip()
    return cleaned[:120]


def _topic_keywords(topic_text, max_keywords=3):
    words = re.findall(r"[A-Za-z]{4,}", str(topic_text or "").lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    if not filtered:
        return ["concept", "application"]

    # Keep order but remove duplicates.
    seen = set()
    unique = []
    for token in filtered:
        if token not in seen:
            seen.add(token)
            unique.append(token)
    return unique[:max_keywords]


def build_topic_intelligence(results_df):
    if results_df.empty:
        return {}

    avg_similarity = float(results_df["Similarity"].mean())
    high_count = int((results_df["Similarity"] >= 0.7).sum())
    medium_count = int(((results_df["Similarity"] >= 0.45) & (results_df["Similarity"] < 0.7)).sum())
    low_count = int((results_df["Similarity"] < 0.45).sum())

    top_row = results_df.iloc[0]
    top_topic = _normalize_topic(top_row["Lecture Topic"])
    top_file = top_row["File"]

    recommendations = []
    for idx, row in results_df.head(8).iterrows():
        sim = float(row["Similarity"])
        if sim >= 0.75:
            action = "Master first"
        elif sim >= 0.55:
            action = "Revise with PYQs"
        else:
            action = "Quick revision"

        recommendations.append({
            "Rank": idx + 1,
            "Topic": _normalize_topic(row["Lecture Topic"]),
            "Similarity": round(sim, 3),
            "Action": action
        })

    return {
        "avg_similarity": round(avg_similarity, 3),
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "top_topic": top_topic,
        "top_file": top_file,
        "recommendations": pd.DataFrame(recommendations)
    }


def generate_question_paper(results_df, exam_questions, paper_type="mid"):
    ranked = results_df.sort_values(by=["Similarity", "Relevance Score"], ascending=False).reset_index(drop=True)
    question_bank = [q.strip() for q in exam_questions if q and len(q.strip()) > 15]

    if paper_type == "mid":
        title = "MID TERM EXAMINATION"
        duration = "1.5 Hours"
        max_marks = 30
        section_a_count = 6
        section_a_marks = 2
        section_b_count = 3
        section_b_marks = 6
    else:
        title = "END TERM EXAMINATION"
        duration = "3 Hours"
        max_marks = 70
        section_a_count = 10
        section_a_marks = 2
        section_b_count = 5
        section_b_marks = 10

    def pick_topic(index):
        if ranked.empty:
            return "Core Topic", 0.5
        row = ranked.iloc[index % len(ranked)]
        return _normalize_topic(row["Lecture Topic"]), float(row["Similarity"])

    def difficulty_label(similarity):
        if similarity >= 0.75:
            return "Easy"
        if similarity >= 0.55:
            return "Moderate"
        return "Challenging"

    def pick_seed_question(topic):
        if not question_bank:
            return ""
        keywords = _topic_keywords(topic)
        for candidate in question_bank:
            lc = candidate.lower()
            if any(k in lc for k in keywords):
                return candidate
        return ""

    paper_meta = {
        "title": title,
        "duration": duration,
        "max_marks": max_marks,
        "avg_similarity": round(float(ranked["Similarity"].mean()) if not ranked.empty else 0.0, 3),
        "high_priority_topics": int((ranked["Similarity"] >= 0.7).sum()) if not ranked.empty else 0,
        "section_a": [],
        "section_b": []
    }

    for i in range(section_a_count):
        topic, sim = pick_topic(i)
        kw = _topic_keywords(topic)
        q_text = f"Explain {kw[0]} in {topic.lower()} with one real-world example."
        paper_meta["section_a"].append({
            "number": i + 1,
            "topic": topic,
            "difficulty": difficulty_label(sim),
            "marks": section_a_marks,
            "text": q_text
        })

    for i in range(section_b_count):
        topic, sim = pick_topic(i + section_a_count)
        seed = pick_seed_question(topic)
        if seed:
            q_text = seed
        else:
            kw = _topic_keywords(topic)
            q_text = (
                f"Analyze {topic.lower()} with focus on {kw[0]} and {kw[-1]}. "
                "Present architecture, workflow, and practical implications."
            )
        paper_meta["section_b"].append({
            "number": section_a_count + i + 1,
            "topic": topic,
            "difficulty": difficulty_label(sim),
            "marks": section_b_marks,
            "text": q_text
        })

    lines = [
        paper_meta["title"],
        "Course: Topic Intelligence Based Paper",
        f"Duration: {paper_meta['duration']}",
        f"Maximum Marks: {paper_meta['max_marks']}",
        "",
        "Generation Metrics:",
        f"- Average Similarity: {paper_meta['avg_similarity']}",
        f"- High Priority Topics: {paper_meta['high_priority_topics']}",
        "",
        "Instructions:",
        "1. Read all questions carefully.",
        "2. Use diagrams and examples where needed.",
        "3. Follow marks-based depth in answers.",
        "",
        "SECTION A - Short Answer"
    ]

    for q in paper_meta["section_a"]:
        lines.append(f"Q{q['number']}. {q['text']} [{q['marks']} marks]")

    lines.append("")
    lines.append("SECTION B - Long Answer")
    for q in paper_meta["section_b"]:
        lines.append(f"Q{q['number']}. {q['text']} [{q['marks']} marks]")

    return "\n".join(lines), paper_meta


def generate_paper_pdf_bytes(paper_text, paper_meta):
    if not PDF_EXPORT_AVAILABLE:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, paper_meta.get("title", "Question Paper"), ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Duration: {paper_meta.get('duration', '-')}", ln=True)
    pdf.cell(0, 8, f"Maximum Marks: {paper_meta.get('max_marks', '-')}", ln=True)
    pdf.cell(0, 8, f"Average Similarity: {paper_meta.get('avg_similarity', '-')}", ln=True)
    pdf.ln(2)

    for line in paper_text.splitlines():
        safe_line = line.encode("latin-1", "ignore").decode("latin-1")
        if not safe_line.strip():
            pdf.ln(3)
        else:
            pdf.multi_cell(0, 7, safe_line)

    raw = pdf.output(dest="S")
    if isinstance(raw, bytes):
        return raw
    if isinstance(raw, bytearray):
        return bytes(raw)
    return raw.encode("latin-1", "ignore")

st.set_page_config(
    page_title="Lecture-to-Exam Mapper", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    :root {
        --bg-base: #f4f7fb;
        --bg-panel: #ffffff;
        --ink-main: #10263f;
        --ink-soft: #5f7288;
        --accent: #0f766e;
        --accent-strong: #0b5f58;
        --accent-alt: #f59e0b;
        --line: #d8e1ec;
    }
    .main { background: var(--bg-base); color: var(--ink-main); }
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 8% 0%, #e8f6f4 0%, var(--bg-base) 42%), var(--bg-base);
    }
    [data-testid="stSidebar"] { display: none; }
    .stMetric {
        background: var(--bg-panel);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(16, 38, 63, 0.08);
        border-left: 4px solid var(--accent);
        color: var(--ink-main);
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 18px;
        background: linear-gradient(120deg, var(--accent) 0%, var(--accent-strong) 100%);
        color: white;
        border: none;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        background: #eef3fa;
        border: 1px solid var(--line);
        padding: 4px 12px;
        height: 42px;
    }
    .stTabs [aria-selected="true"] {
        background: #e2f4f2 !important;
        color: #0b5f58 !important;
        border: 1px solid #b8e4de !important;
    }
    [data-testid="stWidgetLabel"] p {
        color: var(--ink-main) !important;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: var(--ink-main) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #1e2333;
        border: 1px solid #384155;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #e4ebf7 !important;
    }
    [data-testid="stSlider"] [data-testid="stMarkdownContainer"] p {
        color: var(--ink-main) !important;
    }
    .header-title { font-size: 2.5em; color: var(--ink-main); font-weight: 800; text-align: center; margin-bottom: 20px; }
    .info-box {
        background: linear-gradient(130deg, #e6f7f5 0%, #f0f9ff 100%);
        color: var(--ink-main);
        padding: 18px;
        border-radius: 12px;
        margin: 10px 0;
        border: 1px solid #cce8e4;
    }
    .how-it-works-container { display: flex; justify-content: space-around; align-items: center; margin: 30px 0; padding: 26px; background: var(--bg-panel); border-radius: 16px; border: 1px solid var(--line); box-shadow: 0 10px 22px rgba(16, 38, 63, 0.08); }
    .step-card { text-align: center; flex: 1; padding: 20px; }
    .step-icon { font-size: 42px; margin-bottom: 15px; background: linear-gradient(135deg, #0f766e 0%, #0e7490 100%); width: 76px; height: 76px; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; color: white; }
    .step-title { font-size: 18px; font-weight: 700; color: var(--ink-main); margin-bottom: 10px; }
    .step-description { font-size: 14px; color: var(--ink-soft); }
    .step-arrow { font-size: 30px; color: var(--accent); align-self: center; }

    .control-panel {
        margin: 20px 0 26px;
        background: var(--bg-panel);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 12px 24px rgba(16, 38, 63, 0.08);
    }
    .panel-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--ink-main);
        margin-bottom: 4px;
    }
    .panel-subtitle {
        color: var(--ink-soft);
        margin-bottom: 16px;
    }
    .section-card {
        background: var(--bg-panel);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 6px 16px rgba(16, 38, 63, 0.06);
    }
    .hint-badge {
        background: #fff7e6;
        color: #7a4a00;
        border: 1px solid #ffe1ad;
        border-radius: 12px;
        padding: 10px 12px;
        margin-top: 10px;
        font-size: 0.9rem;
    }

    .topic-preview-wrap {
        margin: 20px 0 30px;
        background: var(--bg-panel);
        border-radius: 18px;
        padding: 26px;
        position: relative;
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: 0 10px 20px rgba(16, 38, 63, 0.08);
    }
    .topic-preview-tabs {
        display: flex;
        justify-content: center;
        gap: 38px;
        margin-bottom: 20px;
        font-size: 19px;
        font-weight: 600;
    }
    .topic-preview-tabs .active {
        color: var(--ink-main);
        border-bottom: 3px solid var(--accent);
        padding-bottom: 8px;
    }
    .topic-preview-tabs .muted {
        color: #88a;
        padding-bottom: 8px;
    }
    .topic-preview-card {
        max-width: 900px;
        margin: 0 auto;
        background: #fbfdff;
        border-radius: 24px;
        border: 1px solid #dde7f2;
        padding: 34px 34px 30px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);
        position: relative;
        z-index: 2;
    }
    .preview-title {
        color: var(--ink-main);
        font-size: 46px;
        font-weight: 700;
        margin-bottom: 18px;
    }
    .preview-row {
        margin: 22px 0;
    }
    .preview-row-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 8px;
    }
    .preview-topic {
        font-size: 36px;
        color: var(--ink-main);
        font-weight: 500;
    }
    .preview-pct {
        font-size: 48px;
        color: var(--ink-main);
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    .preview-track {
        height: 9px;
        background: #d7e3ef;
        border-radius: 999px;
        overflow: hidden;
    }
    .preview-fill {
        height: 100%;
        background: linear-gradient(90deg, #0ea5a0 0%, #0e7490 100%);
        border-radius: 999px;
    }
    .preview-note {
        margin-top: 22px;
        color: var(--ink-soft);
        font-size: 24px;
    }

    .doodle {
        position: absolute;
        pointer-events: none;
        opacity: 0.95;
        z-index: 1;
    }
    .doodle-circle {
        width: 130px;
        height: 130px;
        border: 3px dashed rgba(15, 118, 110, 0.4);
        border-radius: 50%;
        right: -20px;
        top: 16px;
    }
    .doodle-wave {
        width: 180px;
        height: 60px;
        left: 14px;
        bottom: 14px;
        background:
            radial-gradient(circle at 10% 60%, rgba(14,139,255,0.55) 0 7px, transparent 8px),
            radial-gradient(circle at 30% 35%, rgba(14,139,255,0.55) 0 7px, transparent 8px),
            radial-gradient(circle at 50% 62%, rgba(14,139,255,0.55) 0 7px, transparent 8px),
            radial-gradient(circle at 70% 36%, rgba(14,139,255,0.55) 0 7px, transparent 8px),
            radial-gradient(circle at 90% 60%, rgba(14,139,255,0.55) 0 7px, transparent 8px);
    }
    .doodle-scribble {
        width: 120px;
        height: 120px;
        right: 24px;
        bottom: 18px;
        border-right: 4px solid rgba(14, 116, 144, 0.4);
        border-top: 4px solid rgba(14, 116, 144, 0.4);
        border-radius: 18px 56px 12px 80px;
        transform: rotate(12deg);
    }

    @media (max-width: 900px) {
        .topic-preview-tabs { gap: 18px; font-size: 15px; }
        .topic-preview-card { padding: 22px 18px; }
        .preview-title { font-size: 30px; }
        .preview-topic { font-size: 24px; }
        .preview-pct { font-size: 32px; }
        .preview-note { font-size: 18px; }
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-title">Lecture-to-Exam Topic Mapping System</div>', unsafe_allow_html=True)

# How it Works Section
st.markdown("""
<div class="how-it-works-container">
    <div class="step-card">
        <div class="step-icon">📤</div>
        <div class="step-title">Choose Your Subject</div>
        <div class="step-description">Select from available subjects or upload your college papers</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-card">
        <div class="step-icon">⚡</div>
        <div class="step-title">AI Analyzes Patterns</div>
        <div class="step-description">Advanced algorithms identify what actually appears in exams</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step-card">
        <div class="step-icon">📊</div>
        <div class="step-title">Get Topic Insights</div>
        <div class="step-description">See exactly what to focus on for maximum impact</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topic-preview-wrap">
    <div class="panel-title">Sample Insights Preview</div>
    <div class="panel-subtitle">This is an example of what your analyzed results will look like.</div>
</div>
""", unsafe_allow_html=True)

preview_col1, preview_col2 = st.columns([1.7, 1])
with preview_col1:
    st.markdown("#### Operating Systems - Top Topics")
    st.write("Memory Management")
    st.progress(0.32)
    st.write("Process Scheduling")
    st.progress(0.21)
    st.write("File Systems")
    st.progress(0.18)
    st.caption("Based on analysis of 87 exam papers (2019-2024)")

with preview_col2:
    st.markdown("#### Quick Snapshot")
    st.metric("Likely High-Yield Topics", "12")
    st.metric("Avg Similarity (Sample)", "0.71")
    st.metric("Coverage Confidence", "High")

st.markdown("---")

st.markdown("""
<div class="control-panel">
    <div class="panel-title">Control Center</div>
    <div class="panel-subtitle">Upload your files, tune confidence, and run analysis from one place.</div>
</div>
""", unsafe_allow_html=True)

input_col, settings_col = st.columns([2, 1])

with input_col:
    lecture_files = st.file_uploader(
        "📚 Upload Lecture Notes (PDF)",
        type="pdf",
        accept_multiple_files=True,
        help="Upload one or more lecture PDFs to analyze"
    )

    exam_file = st.file_uploader(
        "📝 Upload Previous Exam (PDF)",
        type="pdf",
        help="Upload exam PDF to identify which lecture topics appear"
    )

with settings_col:
    st.markdown("### ⚙️ Analysis Settings")
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Only show matches with similarity above this threshold. Higher = stricter matching."
    )

    threshold_color = "🟢" if confidence_threshold < 0.4 else "🟡" if confidence_threshold < 0.7 else "🔴"
    st.metric("Current Threshold", f"{threshold_color} {confidence_threshold:.2f}")
    st.caption("🟢 Low: More results")
    st.caption("🟡 Medium: Balanced")
    st.caption("🔴 High: Strict matching")

    process_btn = st.button(
        "🚀 Analyze & Map Topics",
        use_container_width=True,
        type="primary"
    )

st.markdown("""
<div class="info-box">
<b>💡 How it works:</b><br>
Upload lecture files, map exam questions to the most relevant topics, and get a ranked study plan with trend insights.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hint-badge">Tip: Use 0.30-0.50 confidence for first pass, then increase threshold to focus on high-certainty topics.</div>', unsafe_allow_html=True)

if process_btn:
    if lecture_files and exam_file:
        with st.spinner("⏳ Processing documents and running AI... This may take a moment."):
            model = load_model()
            collection = init_db()
            
            # Loop through every uploaded lecture file
            progress_bar = st.progress(0)
            for idx, lf in enumerate(lecture_files):
                temp_filename = f"temp_{lf.name}"
                with open(temp_filename, "wb") as f: 
                    f.write(lf.getbuffer())
                
                store_lecture(process_lecture(temp_filename), lf.name, collection, model)
                os.remove(temp_filename)
                progress_bar.progress((idx + 1) / len(lecture_files))
            
            # Process Exam
            with open("temp_exam.pdf", "wb") as f: f.write(exam_file.getbuffer())
            exam_questions = extract_exam_questions("temp_exam.pdf")
            os.remove("temp_exam.pdf")
            
            # Calculate results with confidence threshold
            results_df = calculate_topic_importance(exam_questions, collection, model, 
                                                    similarity_threshold=confidence_threshold)

            fallback_used = False
            if results_df.empty and confidence_threshold > 0:
                retry_df = calculate_topic_importance(
                    exam_questions,
                    collection,
                    model,
                    similarity_threshold=0.0
                )
                if not retry_df.empty:
                    results_df = retry_df
                    fallback_used = True
        
        if not results_df.empty:
            st.success("✅ Analysis Complete!")
            if fallback_used:
                st.info(
                    "No topics matched at your selected threshold. Showing best available matches "
                    "using adaptive fallback so you can continue with topic insights and paper generation."
                )
            st.markdown("---")
            
            # Display key metrics in columns
            metric_cols = st.columns(5)
            with metric_cols[0]:
                st.metric("📊 Topics Found", len(results_df))
            with metric_cols[1]:
                st.metric("📈 Avg Similarity", f"{results_df['Similarity'].mean():.3f}")
            with metric_cols[2]:
                st.metric("⭐ Max Similarity", f"{results_df['Similarity'].max():.3f}")
            with metric_cols[3]:
                st.metric("❓ Exam Questions", len(exam_questions))
            with metric_cols[4]:
                st.metric("📚 Lectures Analyzed", len(lecture_files))

            st.markdown("---")
            st.markdown("### 🧠 Topic Intelligence")
            topic_info = build_topic_intelligence(results_df)
            info_col1, info_col2, info_col3 = st.columns(3)
            with info_col1:
                st.metric("Top Priority Topic", topic_info["top_topic"][:32] + ("..." if len(topic_info["top_topic"]) > 32 else ""))
            with info_col2:
                st.metric("Avg Confidence", topic_info["avg_similarity"])
            with info_col3:
                st.metric("High Priority Topics", topic_info["high_count"])

            mix_col1, mix_col2 = st.columns([1.2, 1.8])
            with mix_col1:
                st.markdown('<div class="section-card"><b>Coverage Mix</b><br><br>'
                            f'High: {topic_info["high_count"]}<br>'
                            f'Medium: {topic_info["medium_count"]}<br>'
                            f'Low: {topic_info["low_count"]}<br><br>'
                            f'Strongest source file: {topic_info["top_file"]}'
                            '</div>', unsafe_allow_html=True)
            with mix_col2:
                st.markdown("#### Recommended Study Order")
                st.dataframe(topic_info["recommendations"], use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### 📝 Generate Question Paper")
            gen_col1, gen_col2, gen_col3 = st.columns([1.2, 1.2, 1])
            with gen_col1:
                paper_mode = st.radio(
                    "Select Paper Type",
                    ["Mid Term Paper", "End Term Paper"],
                    horizontal=False
                )
            with gen_col2:
                st.markdown('<div class="section-card"><b>Paper Blueprint</b><br><br>'
                            'Mid Term: 1.5 hrs, short + long mix<br>'
                            'End Term: 3 hrs, deeper analytical set<br><br>'
                            'Questions are generated from your identified important topics and extracted exam patterns.'
                            '</div>', unsafe_allow_html=True)
            with gen_col3:
                generate_btn = st.button(
                    "Generate Mid Term Paper" if paper_mode == "Mid Term Paper" else "Generate End Term Paper",
                    use_container_width=True,
                    type="primary"
                )

            if generate_btn:
                paper_type = "mid" if paper_mode == "Mid Term Paper" else "end"
                generated_paper, generated_meta = generate_question_paper(results_df, exam_questions, paper_type=paper_type)
                st.session_state["generated_paper_text"] = generated_paper
                st.session_state["generated_paper_meta"] = generated_meta
                st.session_state["generated_paper_name_txt"] = "mid_term_paper.txt" if paper_type == "mid" else "end_term_paper.txt"
                st.session_state["generated_paper_name_pdf"] = "mid_term_paper.pdf" if paper_type == "mid" else "end_term_paper.pdf"
                st.session_state["generated_paper_pdf"] = generate_paper_pdf_bytes(generated_paper, generated_meta)

            if "generated_paper_text" in st.session_state:
                st.markdown("#### Generated Paper Preview")
                meta = st.session_state.get("generated_paper_meta", {})
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Paper Marks", meta.get("max_marks", "-"))
                with m2:
                    st.metric("Avg Similarity Used", meta.get("avg_similarity", "-"))
                with m3:
                    st.metric("High Priority Topics Used", meta.get("high_priority_topics", "-"))
                st.text_area(
                    "Preview",
                    st.session_state["generated_paper_text"],
                    height=360,
                    label_visibility="collapsed"
                )
                down_col1, down_col2 = st.columns(2)
                with down_col1:
                    st.download_button(
                        label="Download Paper (TXT)",
                        data=st.session_state["generated_paper_text"],
                        file_name=st.session_state.get("generated_paper_name_txt", "question_paper.txt"),
                        mime="text/plain"
                    )
                with down_col2:
                    if st.session_state.get("generated_paper_pdf"):
                        st.download_button(
                            label="Download Paper (PDF)",
                            data=st.session_state["generated_paper_pdf"],
                            file_name=st.session_state.get("generated_paper_name_pdf", "question_paper.pdf"),
                            mime="application/pdf"
                        )
                    else:
                        st.warning("PDF export library not installed. Install fpdf2 for PDF downloads.")
            
            st.markdown("---")
            
            # Tab layout for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["Overview", "Gap Analysis", "Distribution", "Rankings", "Details"]
            )
            
            # ===== TAB 1: OVERVIEW =====
            with tab1:
                st.markdown("### 📊 Exam Topic Analysis Overview")
                st.markdown("Below are the lecture topics most likely to appear on exams, ranked by relevance.")
                
                col1, col2 = st.columns([2, 1.5])
                with col1:
                    chart1 = create_bar_chart(results_df)
                    if chart1:
                        st.plotly_chart(chart1, use_container_width=True)
                
                with col2:
                    chart2 = create_pie_chart(results_df)
                    if chart2:
                        st.plotly_chart(chart2, use_container_width=True)
                
                # Top 5 topics summary
                st.markdown("#### 🏆 Top 5 Exam-Focused Topics")
                for idx, row in results_df.head(5).iterrows():
                    st.markdown(
                        create_topic_card(
                            row['Topic Snippet'], 
                            row['Similarity'], 
                            row['Relevance Score'],
                            row['Max Similarity']
                        ), 
                        unsafe_allow_html=True
                    )
            
            # ===== TAB 2: GAP ANALYSIS =====
            with tab2:
                st.markdown("### 🚫 Gap Analysis: Low-Coverage Topics")
                st.info(
                    "📢 **Study Strategy:** Topics with very low coverage in past exams may be deprioritized "
                    "unless they're emphasized in course guidelines."
                )
                
                gap_df = calculate_gap_analysis(results_df, None, model)
                
                if not gap_df.empty:
                    st.write(f"Found **{len(gap_df)} low-coverage topics** to potentially skip")
                    col1, col2 = st.columns([2.5, 1.5])
                    with col1:
                        chart = create_gap_analysis_chart(gap_df)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                    with col2:
                        st.markdown("#### 📋 Skip These Topics")
                        for idx, row in gap_df.head(10).iterrows():
                            coverage = row['Coverage_Pct']
                            bullet = "🔴" if coverage < 2 else "🟡"
                            st.write(f"{bullet} {row['Topic Snippet'][:60]}...")
                else:
                    st.success("✅ Excellent! All lecture topics have solid exam coverage!")
            
            # ===== TAB 3: DISTRIBUTION & TRENDS =====
            with tab3:
                st.markdown("### 📊 Score Distribution & Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    chart = create_similarity_distribution_chart(results_df)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
                with col2:
                    chart = create_confidence_scatter(results_df)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
                # Year-over-year trends if available
                st.markdown("---")
                st.markdown("### 📅 Year-over-Year Trends")
                year_trends = calculate_year_over_year_trends(results_df)
                if not year_trends.empty and len(year_trends.columns) > 1:
                    st.info(
                        "🔥 **Hot Topics:** The heatmap shows topics that consistently appear in recent exams. "
                        "Bright red = heavily tested, Light = rarely tested."
                    )
                    heatmap = create_year_over_year_heatmap(year_trends)
                    if heatmap:
                        st.plotly_chart(heatmap, use_container_width=True)
                else:
                    st.info(
                        "💡 **Tip:** Upload exams from multiple years (e.g., `exam_2021.pdf`, `exam_2023.pdf`) "
                        "to see year-over-year trends and identify consistently tested topics."
                    )
            
            # ===== TAB 4: RANKINGS & SUNBURST =====
            with tab4:
                st.markdown("### 🌟 Topic Priority Rankings")
                st.markdown("Visual hierarchy of topics by importance and exam relevance.")
                
                sunburst = create_topic_ranking_sunburst(results_df)
                if sunburst:
                    st.plotly_chart(sunburst, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📚 Lecture File Contributions")
                st.markdown("Which lecture files contribute most to exam-relevant topics?")
                
                file_chart = create_file_contribution_bar(results_df)
                if file_chart:
                    st.plotly_chart(file_chart, use_container_width=True)
            
            # ===== TAB 5: DETAILED RESULTS =====
            with tab5:
                st.markdown("### 📋 Complete Topic Breakdown")
                st.write(f"Displaying {len(results_df)} topics (Threshold: {confidence_threshold:.2f})")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    sort_by = st.selectbox(
                        "Sort by:", 
                        ["Similarity", "Relevance Score", "File"],
                        help="Change the sorting order of results"
                    )
                with col2:
                    show_rows = st.selectbox(
                        "Show rows:", 
                        [10, 25, 50, 100, "All"],
                        help="Control how many results to display"
                    )
                
                results_sorted = results_df.sort_values(by=sort_by, ascending=False)
                display_rows = results_sorted if show_rows == "All" else results_sorted.head(show_rows)
                
                st.dataframe(
                    display_rows[["Topic Snippet", "Similarity", "Relevance Score", "Max Similarity", "File", "Page", "Year"]],
                    use_container_width=True,
                    height=600
                )
                
                # Export options
                st.markdown("---")
                st.markdown("### 💾 Export Results")
                col1, col2 = st.columns(2)
                with col1:
                    csv = results_sorted.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="exam_analysis.csv",
                        mime="text/csv"
                    )
                with col2:
                    json_data = results_sorted.to_json(orient="records", indent=2)
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json_data,
                        file_name="exam_analysis.json",
                        mime="application/json"
                    )
        else:
            st.warning("⚠️ No matching topics found. Try lowering the confidence threshold.")
    else:
        st.warning("⚠️ Please upload at least one lecture PDF and an exam PDF to begin analysis.")