from extraction import extract_exam_questions
from processing import process_lecture
from database import load_model, init_db, store_lecture
from scoring import calculate_topic_importance
import streamlit as st
import os

st.set_page_config(page_title="Lecture-to-Exam Mapper", layout="wide")
st.title("Lecture-to-Exam Topic Mapping System")
with st.sidebar:
    st.header("Upload Documents")
    lecture_file = st.file_uploader("Upload Lecture Notes (PDF)", type="pdf")
    exam_file = st.file_uploader("Upload Previous Exam (PDF)", type="pdf")
    process_btn = st.button("Analyze & Map Topics")
    if process_btn and lecture_file and exam_file:
        with open("temp_lecture.pdf", "wb") as f: f.write(lecture_file.getbuffer())
        with open("temp_exam.pdf", "wb") as f: f.write(exam_file.getbuffer())
    
        model, collection = load_model(), init_db()
        store_lecture(process_lecture("temp_lecture.pdf"), lecture_file.name, collection, model)
        exam_questions = extract_exam_questions("temp_exam.pdf")
results_df = calculate_topic_importance(exam_questions, collection, model)
os.remove("temp_lecture.pdf")
os.remove("temp_exam.pdf")
if not results_df.empty:
        st.success("Analysis Complete!")
        st.subheader("📋 Detailed Topic Breakdown")
        st.dataframe(results_df[["Topic Snippet", "Relevance Score"]], use_container_width=True)