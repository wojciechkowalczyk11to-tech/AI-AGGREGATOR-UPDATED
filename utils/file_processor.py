from __future__ import annotations
import os, PyPDF2, docx
def process_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        res = ""
        with open(filepath, "rb") as f:
            r = PyPDF2.PdfReader(f)
            for p in r.pages: res += p.extract_text() + "\n"
        return res
    elif ext == ".docx":
        d = docx.Document(filepath)
        return "\n".join([p.text for p in d.paragraphs])
    else:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f: return f.read()
