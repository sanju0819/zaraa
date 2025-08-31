import PyPDF2
from chat_core import get_response

def summarize_pdf(file):
    text = extract_text(file)
    if not text:
        return "⚠️ Could not extract text from file."
    summary_prompt = f"Summarize the following document:\n\n{text[:3000]}"
    return get_response([{"role": "user", "content": summary_prompt}])

def qa_over_pdf(file, question):
    text = extract_text(file)
    if not text:
        return "⚠️ Could not extract text from file."
    prompt = f"Answer the question based on the document:\n\nDocument:\n{text[:4000]}\n\nQuestion: {question}"
    return get_response([{"role": "user", "content": prompt}])

def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
    elif file.name.endswith(".docx"):
        import docx
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
    return text
