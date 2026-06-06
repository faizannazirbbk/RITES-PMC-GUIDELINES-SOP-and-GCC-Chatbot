import streamlit as st
import PyPDF2
import requests
import io
from groq import Groq
from docx import Document

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Powered by Groq AI")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

GITHUB_RAW = "https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"

FILES = [
    {"name": "Guidelines on Procurement of Works, Goods and Services, July 2023.pdf", "type": "pdf"},
    {"name": "RITES_SOP_2025_Formatted.docx", "type": "docx"},
    {"name": "RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf", "type": "pdf"},
    {"name": "Correction_Slip_3_GCC_Works.docx", "type": "docx"}
]

@st.cache_resource
def load_docs():
    pages = []
    for file in FILES:
        try:
            url = GITHUB_RAW + requests.utils.quote(file["name"])
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                if file["type"] == "pdf":
                    reader = PyPDF2.PdfReader(io.BytesIO(r.content))
                    for i, page in enumerate(reader.pages):
                        t = page.extract_text()
                        if t and len(t.strip()) > 20:
                            pages.append({
                                "source": file["name"][:40],
                                "page": i+1,
                                "text": t
                            })
                elif file["type"] == "docx":
                    doc = Document(io.BytesIO(r.content))
                    full_text = ""
                    for para in doc.paragraphs:
                        if para.text.strip():
                            full_text += para.text + "\n"
                    chunk_size = 1000
                    for i in range(0, len(full_text), chunk_size):
                        chunk = full_text[i:i+chunk_size]
                        if chunk.strip():
                            pages.append({
                                "source": file["name"][:40],
                                "page": i//chunk_size + 1,
                                "text": chunk
                            })
        except Exception as e:
            st.warning(f"Could not load: {file['name'][:30]}")
    return pages

with st.spinner("📚 Loading all documents..."):
    pages = load_docs()

if pages:
    st.success(f"✅ {len(pages)} sections loaded from 4 documents!")
else:
    st.error("❌ Failed to load documents")

def smart_search(query, pages, top_n=5):
    keywords = query.lower().split()
    scored = []
    for p in pages:
        text_lower = p["text"].lower()
        score = sum(text_lower.count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_n]]

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask your question..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt
