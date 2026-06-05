import streamlit as st
import groq
import PyPDF2
import requests
import io

st.set_page_config(page_title="RITES PMC Chatbot", page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Ask questions about GCC, SOP and PMC Guidelines")

client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])

GITHUB_RAW = "https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"

PDF_FILES = [
    "Guidelines on Procurement of Works, Goods and Services, July 2023.pdf",
    "SOP Updated as on 01.07.2025.pdf",
    "RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf",
    "Correction_Slip_3_GCC_Works_pdf-2026-Jan-20-16-25-46.pdf"
]

@st.cache_resource
def load_documents():
    all_chunks = []
    for filename in PDF_FILES:
        try:
            url = GITHUB_RAW + requests.utils.quote(filename)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                reader = PyPDF2.PdfReader(io.BytesIO(response.content))
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        all_chunks.append({
                            "text": text[:1000],
                            "source": filename,
                            "page": i+1
                        })
        except Exception as e:
            st.warning(f"Could not load: {filename}")
    return all_chunks

def find_relevant(chunks, question, max_chunks=3):
    question_words = question.lower().split()
    scored = []
    for chunk in chunks:
        score = sum(1 for word in question_words 
                   if word in chunk["text"].lower())
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_chunks]]

with st.spinner("📚 Loading documents..."):
    chunks = load_documents()

if chunks:
    st.success(f"✅ Documents loaded! ({len(chunks)} sections)")
else:
    st.error("❌ Could not load documents.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask your question here..."):
    st.session_state.messages.append(
        {"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    relevant = find_relevant(chunks, prompt)
    context = ""
    sources = []
    for chunk in relevant:
        context += f"\n---\n{chunk['text']}"
        sources.append(f"{chunk['source']} (Page {chunk['page']})")

    system_msg = """You are an expert on RITES PMC Guidelines, GCC and SOP.
Answer only from the provided document sections.
If not found say: 'Not found in the provided documents.'
Always mention clause numbers if available."""

    full_prompt = f"""Document sections:
{context}

Question: {prompt}"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role":"system","content":system_msg},
                {"role":"user","content":full_prompt}
            ],
            max_tokens=1000
        )
        answer = response.choices[0].message.content
        if sources:
            answer += f"\n\n📄 **Sources:** {', '.join(set(sources))}"
    except Exception as e:
        answer = "Error getting response. Please try again."

    st.session_state.messages.append(
        {"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
