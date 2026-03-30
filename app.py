import streamlit as st
import os
import pandas as pd
import numpy as np

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
    .stTabs [data-baseweb="tab-list"] button { border-radius: 8px 8px 0 0; }
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
    <div class="doodle doodle-circle"></div>
    <div class="doodle doodle-wave"></div>
    <div class="doodle doodle-scribble"></div>

    <div class="topic-preview-tabs">
        <div class="active">Overview</div>
        <div class="muted">Topic Breakdown</div>
        <div class="muted">Trends</div>
    </div>

    <div class="topic-preview-card">
        <div class="preview-title">Operating Systems</div>

        <div class="preview-row">
            <div class="preview-row-head">
                <div class="preview-topic">Memory Management</div>
                <div class="preview-pct">32%</div>
            </div>
            <div class="preview-track"><div class="preview-fill" style="width: 32%;"></div></div>
        </div>

        <div class="preview-row">
            <div class="preview-row-head">
                <div class="preview-topic">Process Scheduling</div>
                <div class="preview-pct">21%</div>
            </div>
            <div class="preview-track"><div class="preview-fill" style="width: 21%;"></div></div>
        </div>

        <div class="preview-row">
            <div class="preview-row-head">
                <div class="preview-topic">File Systems</div>
                <div class="preview-pct">18%</div>
            </div>
            <div class="preview-track"><div class="preview-fill" style="width: 18%;"></div></div>
        </div>

        <div class="preview-note">Based on analysis of 87 exam papers (2019-2024)</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
        
        if not results_df.empty:
            st.success("✅ Analysis Complete!")
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
            
            # Tab layout for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["📈 Overview", "⏭️ Gap Analysis", "📊 Distribution", "🌟 Rankings", "📋 Details"]
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