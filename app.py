import streamlit as st
import groq
import PyPDF2
import os
import requests

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Ask questions about GCC, SOP and PMC Guidelines")

client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Auto-load PDFs from GitHub ─────────────────────
GITHUB_RAW = "https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"

PDF_FILES = [
    "Guidelines on Procurement of Works, Goods and Services, July 2023.pdf",
    "SOP Updated as on 01.07.2025.pdf",
    "RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf",
    "Correction_Slip_3_GCC_Works_pdf-2026-Jan-20-16-25-46.pdf"
]

@st.cache_resource
def load_documents():
    pdf_text = ""
    loaded = []
    for filename in PDF_FILES:
        try:
            url = GITHUB_RAW + requests.utils.quote(filename)
            response = requests.get(url)
            if response.status_code == 200:
                import io
                reader = PyPDF2.PdfReader(io.BytesIO(response.content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text + "\n"
                loaded.append(filename)
        except:
            pass
    return pdf_text, loaded

with st.spinner("📚 Loading documents..."):
    pdf_text, loaded_files = load_documents()

if loaded_files:
    st.success(f"✅ {len(loaded_files)} documents loaded automatically!")
else:
    st.error("❌ Could not load documents. Please check repository.")

# ── Chat History ───────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── User Input ─────────────────────────────────────
if prompt := st.chat_input("Ask your question here..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_msg = """You are an expert on RITES PMC Guidelines, GCC and SOP documents.
Answer only from the provided documents.
If answer is not found, say 'This information is not available in the provided documents.'
Be precise and mention clause numbers where possible."""

    if pdf_text:
        context = pdf_text[:4000]
        full_prompt = f"Documents:\n{context}\n\nQuestion: {prompt}"
    else:
        full_prompt = prompt

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role":"system","content":system_msg},
            {"role":"user","content":full_prompt}
        ]
    )

    answer = response.choices[0].message.content
    st.session_state.messages.append({"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
