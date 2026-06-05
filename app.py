import streamlit as st
import PyPDF2
import requests
import io
from groq import Groq

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Ask questions about GCC, SOP and PMC Guidelines")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Key error!")
    st.stop()

GITHUB_RAW = "https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"

PDF_FILES = [
    "Guidelines on Procurement of Works, Goods and Services, July 2023.pdf",
    "SOP Updated as on 01.07.2025.pdf",
    "RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf",
    "Correction_Slip_3_GCC_Works_pdf-2026-Jan-20-16-25-46.pdf"
]

@st.cache_resource
def load_documents():
    all_text = ""
    count = 0
    for filename in PDF_FILES:
        try:
            url = GITHUB_RAW + requests.utils.quote(filename)
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                reader = PyPDF2.PdfReader(io.BytesIO(r.content))
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        all_text += t + "\n"
                count += 1
        except:
            pass
    return all_text, count

with st.spinner("📚 Loading documents..."):
    pdf_text, count = load_documents()

if count > 0:
    st.success(f"✅ {count} documents loaded!")
else:
    st.warning("⚠️ Documents not loaded")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask your question here..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = pdf_text[:3000] if pdf_text else ""
    
    full_prompt = f"""You are an expert on RITES PMC Guidelines, GCC and SOP.
Use these document excerpts to answer:

{context}

Question: {prompt}

Answer clearly and mention clause numbers if found."""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":full_prompt}],
            max_tokens=500,
            temperature=0.1
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Error: {str(e)}"

    st.session_state.messages.append({"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer
