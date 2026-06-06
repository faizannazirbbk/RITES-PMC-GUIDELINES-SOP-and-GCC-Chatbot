import streamlit as st
import PyPDF2
import requests
import io
from groq import Groq

st.set_page_config(page_title="RITES PMC Chatbot",page_icon="🏗️")
st.title("🏗️ RITES PMC Guidelines Chatbot")
st.caption("Powered by Groq AI")
client=Groq(api_key=st.secrets["GROQ_API_KEY"])
GITHUB_RAW="https://raw.githubusercontent.com/faizannazirbbk/RITES-PMC-GUIDELINES-SOP-and-GCC-Chatbot/main/"
FILES=[
{"name":"Guidelines on Procurement of Works, Goods and Services, July 2023.pdf","type":"pdf"},
{"name":"RITES_SOP_2025_Formatted.pdf","type":"pdf"},
{"name":"RITES_GCC_for_Works,_February_2023_pdf-2023-Feb-25-11-14-35.pdf","type":"pdf"},
{"name":"Correction_Slip_3_GCC_Works.pdf","type":"pdf"}
]
@st.cache_resource
def load_docs():
    pages=[]
    for file in FILES:
        try:
            url=GITHUB_RAW+requests.utils.quote(file["name"])
            r=requests.get(url,timeout=30)
            if r.status_code==200:
                if file["type"]=="pdf":
                    reader=PyPDF2.PdfReader(io.BytesIO(r.content))
                    for i,page in enumerate(reader.pages):
                        t=page.extract_text()
                        if t and len(t.strip())>20:
                            pages.append({"source":file["name"][:40],"page":i+1,"text":t})
                elif file["type"]=="docx":
                    doc=Document(io.BytesIO(r.content))
                    text="\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    for i in range(0,len(text),1000):
                        chunk=text[i:i+1000]
                        if chunk.strip():
                            pages.append({"source":file["name"][:40],"page":i//1000+1,"text":chunk})
        except:
            pass
    return pages
with st.spinner("Loading documents..."):
    pages=load_docs()
if pages:
    st.success(f"✅ {len(pages)} sections loaded!")
else:
    st.error("❌ Failed to load")
def search(query,pages,n=5):
    kw=query.lower().split()
    scored=[(sum(p["text"].lower().count(k) for k in kw),p) for p in pages]
    scored=[x for x in scored if x[0]>0]
    scored.sort(key=lambda x:x[0],reverse=True)
    return [p for _,p in scored[:n]] if scored else pages[:3]
if "messages" not in st.session_state:
    st.session_state.messages=[]
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
if prompt:=st.chat_input("Ask your question..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    relevant=search(prompt,pages)
    context="".join([f"\n[{p['source']} Sec {p['page']}]\n{p['text'][:600]}\n" for p in relevant])
    msg=f"You are RITES PMC expert. Answer from documents only. Mention source and clause.\n\nDOCS:{context}\n\nQ:{prompt}\n\nANSWER:"
    try:
        resp=client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"user","content":msg}],max_tokens=600)
        answer=resp.choices[0].message.content
    except Exception as e:
        answer="Error: "+str(e)[:200]
    st.session_state.messages.append({"role":"assistant","content":answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
