import re

def clean_text(raw_text):
    cleaned = re.sub(r'\s+', ' ', raw_text)
    return re.sub(r'[^\x00-\x7F]+', ' ', cleaned).strip()

def chunk_page_text(pages_data, chunk_size=150, overlap=20):
    """Chunks text while keeping track of the page number it came from."""
    chunks_with_meta = []
    for page in pages_data:
        text = clean_text(page["text"])
        words = text.split()
        if not words: continue
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks_with_meta.append({"chunk": chunk, "page": page["page"]})
            
    return chunks_with_meta

def process_lecture(pdf_path):
    from extraction import extract_pages_from_pdf
    pages = extract_pages_from_pdf(pdf_path)
    return chunk_page_text(pages)

