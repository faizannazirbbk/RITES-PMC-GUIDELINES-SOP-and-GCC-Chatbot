import streamlit as st
import groq
import PyPDF2
import os

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🚆")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Ask questions about GCC, SOP and PMC Guidelines")

client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])

uploaded_files = st.file_uploader(
    "📂 Upload PDF Documents",
    type="pdf",
    accept_multiple_files=True
)

pdf_text = ""
if uploaded_files:
    for pdf in uploaded_files:
        reader = PyPDF2.PdfReader(pdf)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n"
    st.success(f"✅ {len(uploaded_files)} document(s) loaded!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask your question here..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_msg = """You are an expert on RITES PMC Guidelines, GCC and SOP documents.
Answer only from the provided documents.
If answer is not found, say 'This information is not available in the provided documents.'
Be precise and mention clause numbers where possible."""

    if pdf_text:
        context = pdf_text[:8000]
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

