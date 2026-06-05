import streamlit as st
import PyPDF2
import requests
import io
from groq import Groq

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Powered by Groq AI")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

GITHUB_RAW = "https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"

PDF_FILES = [
    "Guidelines on Procurement of Works, Goods and Services, July 2023.pdf",
    "SOP Updated as on 01.07.2025.pdf",
    "RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf",
    "Correction_Slip_3_GCC_Works_pdf-2026-Jan-20-16-25-46.pdf"
]

@st.cache_resource
def load_docs():
    pages = []
    for filename in PDF_FILES:
        try:
            url = GITHUB_RAW + requests.utils.quote(filename)
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                reader = PyPDF2.PdfReader(io.BytesIO(r.content))
                for i, page in enumerate(reader.pages):
                    t = page.extract_text()
                    if t and len(t.strip()) > 20:
                        pages.append({
                            "source": filename,
                            "page": i+1,
                            "text": t
                        })
        except:
            pass
    return pages

with st.spinner("📚 Loading documents..."):
    pages = load_docs()

if pages:
    st.success(f"✅ {len(pages)} pages loaded from 4 documents!")
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
        st.markdown(prompt)

    relevant = smart_search(prompt, pages)

    if relevant:
        context = ""
        for p in relevant:
            context += f"\n[{p['source'][:40]} - Page {p['page']}]\n{p['text'][:800]}\n"
    else:
        context = "\n".join([p["text"][:300] for p in pages[:5]])

    full_prompt = f"""You are an expert assistant for RITES PMC Guidelines, GCC and SOP documents.
Answer accurately and in detail from the document sections below.
Always mention source document name and clause/page number.
If not found say clearly: 'This topic is not covered in the provided documents.'

RELEVANT DOCUMENT SECTIONS:
{context}

QUESTION: {prompt}

DETAILED ANSWER:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":full_prompt}],
            max_tokens=600
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = "Error: " + str(e)[:200]

    st.session_state.messages.append({"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
