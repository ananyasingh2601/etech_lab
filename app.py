import streamlit as st
import os

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
    create_confidence_scatter
)

st.set_page_config(page_title="Lecture-to-Exam Mapper", layout="wide")
st.title("🎓 Advanced Lecture-to-Exam Topic Mapping System")

with st.sidebar:
    st.header("📁 Upload Documents")
    lecture_files = st.file_uploader("Upload Lecture Notes (PDF)", type="pdf", accept_multiple_files=True)
    exam_file = st.file_uploader("Upload Previous Exam (PDF)", type="pdf")
    
    st.divider()
    st.header("⚙️ Analysis Settings")
    
    # NEW: Confidence Threshold Slider
    confidence_threshold = st.slider(
        "Confidence Threshold (Similarity Score)",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Only show matches with similarity above this threshold. Higher = stricter matching."
    )
    
    # Show threshold info
    st.caption(f"📊 Current threshold: {confidence_threshold:.2f}")
    
    process_btn = st.button("🔍 Analyze & Map Topics", use_container_width=True)

if process_btn:
    if lecture_files and exam_file:
        with st.spinner("🤖 Processing documents and running AI... This may take a moment."):
            model = load_model()
            collection = init_db()
            
            # Loop through every uploaded lecture file
            for lf in lecture_files:
                temp_filename = f"temp_{lf.name}"
                with open(temp_filename, "wb") as f: 
                    f.write(lf.getbuffer())
                
                store_lecture(process_lecture(temp_filename), lf.name, collection, model)
                os.remove(temp_filename)
            
            # Process Exam
            with open("temp_exam.pdf", "wb") as f: f.write(exam_file.getbuffer())
            exam_questions = extract_exam_questions("temp_exam.pdf")
            os.remove("temp_exam.pdf")
            
            # Calculate results with confidence threshold
            results_df = calculate_topic_importance(exam_questions, collection, model, 
                                                    similarity_threshold=confidence_threshold)
            
        if not results_df.empty:
            st.success("✅ Analysis Complete!")
            
            # Tab layout for different views
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📈 Overview", "⏭️ Gap Analysis (Skip List)", "📊 Trends & Distribution", "📋 Detailed Results"]
            )
            
            # ===== TAB 1: OVERVIEW =====
            with tab1:
                st.subheader("Top Topic Matches")
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.plotly_chart(create_bar_chart(results_df), use_container_width=True)
                with col2:
                    st.plotly_chart(create_pie_chart(results_df), use_container_width=True)
                with col3:
                    st.metric("Topics Found", len(results_df))
                    st.metric("Avg Similarity", f"{results_df['Similarity'].mean():.3f}" if not results_df.empty else "N/A")
                    st.metric("Max Similarity", f"{results_df['Similarity'].max():.3f}" if not results_df.empty else "N/A")
            
            # ===== TAB 2: GAP ANALYSIS =====
            with tab2:
                st.subheader("🚫 Gap Analysis: Topics NOT Covered (The 'Skip List')")
                st.info(
                    "📢 **Pro Tip:** These topics have near-zero coverage in past exams. "
                    "You might want to deprioritize studying these unless they're highlighted as important."
                )
                
                # Add coverage percentage
                gap_df = calculate_gap_analysis(results_df, None, model)
                
                if not gap_df.empty:
                    st.write(f"Found **{len(gap_df)} low-coverage topics**")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.plotly_chart(create_gap_analysis_chart(gap_df), use_container_width=True)
                    with col2:
                        st.write("**Low Coverage Topics:**")
                        for idx, row in gap_df.head(10).iterrows():
                            st.write(f"• {row['Topic Snippet']}")
                else:
                    st.success("✅ All lecture topics have good exam coverage!")
            
            # ===== TAB 3: TRENDS & DISTRIBUTION =====
            with tab3:
                st.subheader("📊 Trends & Score Distribution")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_similarity_distribution_chart(results_df), use_container_width=True)
                with col2:
                    st.plotly_chart(create_confidence_scatter(results_df), use_container_width=True)
                
                # Year-over-year trends if multiple years detected
                year_trends = calculate_year_over_year_trends(results_df)
                if not year_trends.empty and len(year_trends.columns) > 1:
                    st.subheader("📅 Year-over-Year Topic Trends (Heatmap)")
                    st.info(
                        "🔥 This heatmap shows how topic focus has shifted across years. "
                        "Bright red = heavily tested, Light = rarely tested."
                    )
                    heatmap = create_year_over_year_heatmap(year_trends)
                    if heatmap:
                        st.plotly_chart(heatmap, use_container_width=True)
                else:
                    st.info("💡 Upload exams from multiple years to see year-over-year trends (e.g., exam_2021.pdf, exam_2023.pdf)")
            
            # ===== TAB 4: DETAILED RESULTS =====
            with tab4:
                st.subheader("📋 Detailed Topic Breakdown")
                st.write(f"Showing {len(results_df)} topics (Threshold: {confidence_threshold:.2f})")
                
                # Add sorting/filtering options
                sort_by = st.selectbox("Sort by:", ["Similarity", "Relevance Score", "File"])
                results_sorted = results_df.sort_values(by=sort_by, ascending=False)
                
                st.dataframe(
                    results_sorted[["Topic Snippet", "Similarity", "Relevance Score", "Max Similarity", "File", "Page", "Year"]],
                    use_container_width=True,
                    height=600
                )
                
                # Export option
                if st.button("📥 Export Results as CSV"):
                    csv = results_sorted.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="exam_analysis.csv",
                        mime="text/csv"
                    )
            
    else:
        st.warning("⚠️ Please upload at least one lecture PDF and an exam PDF.")