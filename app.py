# app.py
import io
import time
import requests
import streamlit as st
from pathlib import Path

# === PDF Q&A deps ===
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# === Groq API ===
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# Page setup & global CSS
# -----------------------------
st.set_page_config(page_title="ELISA", layout="wide", page_icon="💬")

st.markdown(
    """
<style>
.main .block-container {padding-bottom: 7rem;}
#chat-footer { 
  position: fixed; 
  left: 0; right: 0; bottom: 0; 
  padding: 0.6rem 1rem; 
  background: var(--background-color);
  border-top: 1px solid rgba(128,128,128,0.2);
  z-index: 999;
}
.footer-inner {
  max-width: 1100px; 
  margin: 0 auto; 
  display: grid; 
  grid-template-columns: 1fr auto; 
  gap: .5rem; 
  align-items: center;
}
.chat-bubble-user{
  background: rgba(59,130,246,.12);
  border: 1px solid rgba(59,130,246,.25);
  padding: .75rem 1rem;
  border-radius: 1rem;
  margin: .25rem 0;
}
.chat-bubble-bot{
  background: rgba(16,185,129,.12);
  border: 1px solid rgba(16,185,129,.25);
  padding: .75rem 1rem;
  border-radius: 1rem;
  margin: .25rem 0;
}
.subtitle{
  opacity: .85;
  font-size: .95rem;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("💬 ELISA: i am always with you")

# -----------------------------
# Utils
# -----------------------------
def type_out(text: str, speed: float = 0.01):
    """Typing animation effect (renders into the page)."""
    ph = st.empty()
    out = ""
    for ch in text:
        out += ch
        ph.markdown(out + "▌")
        time.sleep(speed)
    ph.markdown(out)
    return ph


def elisa_response(prompt: str, context: str = "") -> str:
    """Call Groq LLM API and return text content (safe access)."""
    try:
        # Combine context and prompt properly
        full_prompt = f"{context}\n\n{prompt}" if context and context.strip() else prompt

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are ELISA, a helpful, empathetic AI assistant."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Correct access to message text (dot attribute)
        content = response.choices[0].message.content
        return content if content else "I'm sorry — I couldn't generate a response."
    except Exception as exc:
        # Show a clean message in-app and return a fallback string
        st.error(f"API Error: {str(exc)}")
        return "I'm experiencing technical difficulties. Please try again later."


# -----------------------------
# PDF Q&A utils
# -----------------------------
def pdf_to_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n".join(pages)


def chunk_text(text: str, chunk_size=1200, overlap=150):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + chunk_size])
        i += chunk_size - overlap
    return chunks


def retrieve_relevant_chunks(chunks, question, top_k=3):
    vect = TfidfVectorizer(stop_words="english")
    docs = chunks + [question]
    X = vect.fit_transform(docs)
    sims = cosine_similarity(X[-1], X[:-1]).flatten()
    idxs = sims.argsort()[::-1][:top_k]
    return [chunks[i] for i in idxs]


def answer_about_pdf(chunks, question: str) -> str:
    ctx_chunks = retrieve_relevant_chunks(chunks, question, top_k=3)
    context = "\n\n".join(ctx_chunks)
    prompt = f"Use the context to answer concisely. If the context doesn't contain the answer, say you don't know.\n\nQuestion: {question}\nAnswer:"
    return elisa_response(prompt, context=context)


# -----------------------------
# Session state init
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role","content"}

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# -----------------------------
# UI Tabs
# -----------------------------
tabs = st.tabs(["Chat", "PDF Q&A", "Web Search", "Image", "Tasks", "Fun"])

# =====================================
# 1) CHAT TAB
# =====================================
with tabs[0]:
    st.caption("Chat with ELISA — type below and press the arrow. Responses come with a typing animation.")

    # Show chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-bot'><b>ELISA:</b> {msg['content']}</div>", unsafe_allow_html=True)

    # Sticky footer: use a form so input clearing is handled safely
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([0.95, 0.05])
        with cols[0]:
            user_text = st.text_input("", key="chat_input", label_visibility="collapsed", placeholder="Message ELISA...")
        with cols[1]:
            submit = st.form_submit_button("➡️")

    if submit and user_text and user_text.strip():
        user_text = user_text.strip()
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_text})

        # Call LLM and show typing animation
        with st.spinner("ELISA is thinking..."):
            reply = elisa_response(user_text)
        st.markdown("<div class='subtitle'>ELISA is typing…</div>", unsafe_allow_html=True)
        type_out(reply, speed=0.01)

        # Save assistant reply
        st.session_state.messages.append({"role": "assistant", "content": reply})

        # ensure UI re-renders and shows the latest messages
        st.rerun()


# =====================================
# 2) PDF Q&A TAB
# =====================================
with tabs[1]:
    st.caption("Upload a PDF, get a summary or ask questions about the document.")

    uploaded = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=False)
    if uploaded:
        text = pdf_to_text(uploaded)
        st.session_state.pdf_text = text
        st.session_state.pdf_chunks = chunk_text(text)
        st.success(f"Loaded PDF — {len(st.session_state.pdf_text)} characters, {len(st.session_state.pdf_chunks)} chunks.")

    if st.session_state.pdf_chunks:
        # Summarize button
        if st.button("📑 Summarize PDF"):
            with st.spinner("Summarizing..."):
                summary = elisa_response("Summarize this document in simple bullet points.", context=st.session_state.pdf_text)
            st.subheader("📌 PDF Summary")
            st.write(summary)

        # Ask about the PDF using a form (clears input after submit)
        with st.form("pdf_qa_form", clear_on_submit=True):
            q_col, btn_col = st.columns([0.85, 0.15])
            with q_col:
                pdf_question = st.text_input("Ask about this PDF…", key="pdf_q_input", label_visibility="collapsed", placeholder="Type your question here")
            with btn_col:
                ask = st.form_submit_button("➡️ Ask")

        if ask and pdf_question and pdf_question.strip():
            with st.spinner("ELISA is reading your document…"):
                ans = answer_about_pdf(st.session_state.pdf_chunks, pdf_question.strip())
            st.write("")
            st.markdown(f"**You:** {pdf_question.strip()}")
            st.markdown("<div class='subtitle'>ELISA is answering…</div>", unsafe_allow_html=True)
            type_out(ans, speed=0.01)
            st.session_state.messages.append({"role": "assistant", "content": f"[PDF QA] {ans}"})

# =====================================
# 3) WEB SEARCH TAB
# =====================================
with tabs[2]:
    st.caption("Quick web quote lookup demo.")
    if st.button("Random Quote"):
        try:
            r = requests.get("https://api.quotable.io/random", timeout=10)
            if r.status_code == 200:
                data = r.json()
                quote = f"“{data['content']}” — {data['author']}"
                st.success(quote)
            else:
                st.warning("Could not fetch quote right now.")
        except Exception as e:
            st.error(f"Quote error: {e}")

# =====================================
# 4) IMAGE TAB
# =====================================
with tabs[3]:
    st.caption("Upload an image. (Vision model integration is a future extension.)")
    img = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    if img:
        st.image(img, use_column_width=True)
        # Placeholder description — replace with your image model call
        desc = "This looks interesting — (plug an image model to describe in detail)."
        type_out(desc)

# =====================================
# 5) TASKS TAB
# =====================================
with tabs[4]:
    st.caption("Simple local task manager (saved in session only).")
    with st.form("task_form", clear_on_submit=True):
        new_task = st.text_input("New task", key="task_input", label_visibility="visible")
        add = st.form_submit_button("➕ Add Task")
    if add and new_task and new_task.strip():
        st.session_state.tasks.append({"task": new_task.strip(), "done": False})
        st.rerun()


    if st.button("🗑️ Clear All Tasks"):
        st.session_state.tasks = []
        st.rerun()


    for i, task in enumerate(st.session_state.tasks):
        cols = st.columns([0.1, 6])
        with cols[0]:
            done = st.checkbox("", value=task["done"], key=f"task_{i}")
            st.session_state.tasks[i]["done"] = done
        with cols[1]:
            st.markdown(f"- {'✅' if task['done'] else '⬜'} {task['task']}")

# =====================================
# 6) FUN TAB
# =====================================
# ============================
# 6) FUN TAB
# ============================
with tabs[5]:
    st.caption("Fun utilities")

    # Create a sub-tab system inside Fun
    fun_tabs = st.tabs(["🎲 Quick Quiz", "🎵 Music", "😂 Jokes"])

    # ============================
    # QUIZ SUB-TAB
    # ============================
    with fun_tabs[0]:
        import pandas as pd
        import random

        # Load quiz CSV
        quiz_df = pd.read_csv("quiz_questions.csv")

        # Pick a random question
        row = quiz_df.sample().iloc[0]
        question = row["question"]
        options = [row["option1"], row["option2"], row["option3"], row["option4"]]
        answer = row["answer"]

        st.write(f"**Question:** {question}")
        choice = st.radio("Choose your answer:", options, key="quiz_choice")

        if st.button("Submit Answer", key="quiz_submit"):
            if choice == answer:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong! The correct answer is {answer}")
# c:\Users\sanja\OneDrive\Desktop\elisa_project\.venv\Scripts\streamlit run app.py
#cd C:\Users\sanja\OneDrive\Desktop\elisa_project