import streamlit as st
import PyPDF2
import requests
import io
from groq import Groq

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")

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
                    if t and len(t.strip()) > 30:
                        pages.append({
                            "file": filename[:30],
                            "page": i+1,
                            "text": t[:500]
                        })
        except:
            pass
    return pages

pages = load_docs()
if pages:
    st.success(f"✅ Loaded {len(pages)} pages")
else:
    st.error("Failed to load documents")

def search(query, pages, n=2):
    words = query.lower().split()
    scored = []
    for p in pages:
        s = sum(1 for w in words if w in p["text"].lower())
        scored.append((s, p))
    scored.sort(reverse=True)
    return scored[:n]

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask question..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    results = search(prompt, pages)
    context = ""
    for score, p in results:
        context += f"[{p['file']} p{p['page']}]: {p['text']}\n\n"

    msg = f"Documents:\n{context}\nQuestion: {prompt}\nAnswer briefly:"

    try:
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":msg}],
            max_tokens=200
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        answer = "Error: " + str(e)[:100]

    st.session_state.messages.append({"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
