import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    """Reads a PDF and returns all text as a single string."""
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def extract_exam_questions(pdf_path):
    """Attempts to split an exam paper into individual questions."""
    raw_text = extract_text_from_pdf(pdf_path)
    questions = re.split(r'\n(?=\d+\. |Q\d+ |[A-Z]\. )', raw_text)
    questions = [q.strip() for q in questions if len(q.strip()) > 10]
    return questions