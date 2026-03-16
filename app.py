import streamlit as st
import os

st.set_page_config(page_title="Lecture-to-Exam Mapper", layout="wide")
st.title("Lecture-to-Exam Topic Mapping System")
with st.sidebar:
    st.header("Upload Documents")
    lecture_file = st.file_uploader("Upload Lecture Notes (PDF)", type="pdf")
    exam_file = st.file_uploader("Upload Previous Exam (PDF)", type="pdf")
    process_btn = st.button("Analyze & Map Topics")