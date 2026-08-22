import pdfplumber, docx

def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    if path.lower().endswith(".docx"):
        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    raise ValueError("Unsupported file type (PDF/DOCX only)")
