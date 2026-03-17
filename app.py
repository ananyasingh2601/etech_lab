import streamlit as st
import os

from extraction import extract_exam_questions
from processing import process_lecture
from database import load_model, init_db, store_lecture
from scoring import calculate_topic_importance
from visualization import create_bar_chart, create_pie_chart

# UI Setup
st.set_page_config(page_title="Lecture-to-Exam Mapper", layout="wide")
st.title("Lecture-to-Exam Topic Mapping System")

with st.sidebar:
    st.header("Upload Documents")
    lecture_file = st.file_uploader("Upload Lecture Notes (PDF)", type="pdf")
    exam_file = st.file_uploader("Upload Previous Exam (PDF)", type="pdf")
    process_btn = st.button("Analyze & Map Topics")

# Everything below must only happen IF the button is clicked and files are present
if process_btn:
    if lecture_file and exam_file:
        with st.spinner("Processing documents and running AI... This may take a moment."):
            # 1. Save files temporarily
            with open("temp_lecture.pdf", "wb") as f: f.write(lecture_file.getbuffer())
            with open("temp_exam.pdf", "wb") as f: f.write(exam_file.getbuffer())
            
            # 2. Load AI and DB
            model = load_model()
            collection = init_db()
            
            # 3. Process Lecture
            store_lecture(process_lecture("temp_lecture.pdf"), lecture_file.name, collection, model)
            
            # 4. Process Exam
            exam_questions = extract_exam_questions("temp_exam.pdf")
            
            # 5. Calculate Scores
            results_df = calculate_topic_importance(exam_questions, collection, model)
            
            # Clean up files
            os.remove("temp_lecture.pdf")
            os.remove("temp_exam.pdf")
            
        # 6. Display Results
        if not results_df.empty:
            st.success("Analysis Complete!")
            
            col1, col2 = st.columns(2)
            with col1: st.plotly_chart(create_bar_chart(results_df), use_container_width=True)
            with col2: st.plotly_chart(create_pie_chart(results_df), use_container_width=True)

            st.subheader("Detailed Topic Breakdown")
            st.dataframe(results_df[["Topic Snippet", "Relevance Score"]], use_container_width=True)
            
    else:
        st.warning("Please upload both a lecture PDF and an exam PDF before analyzing.")