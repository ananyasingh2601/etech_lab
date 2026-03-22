import PyPDF2
import re

def extract_pages_from_pdf(pdf_path):
    """Returns a list of dictionaries containing text and page numbers."""
    pages = []
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text: 
                    pages.append({"text": text, "page": i + 1})
    except Exception as e: 
        print(f"Error reading {pdf_path}: {e}")
    return pages

def extract_exam_questions(pdf_path):
    """Joins pages back together to extract exam questions."""
    pages = extract_pages_from_pdf(pdf_path)
    raw_text = "\n".join([p["text"] for p in pages])
    
    questions = re.split(r'\n(?=\d+\. |Q\d+ |[A-Z]\. )', raw_text)
    return [q.strip() for q in questions if len(q.strip()) > 10]