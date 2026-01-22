import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import google.generativeai as genai
import json, re, time

# ---------- CONFIG ----------
st.set_page_config("Tamil PDF Practice App")
st.title("📘 Tamil PDF Practice App")

# ---------- API KEY ----------
api_key = st.text_input("Gemini API Key", type="password")
if api_key:
    genai.configure(api_key=api_key)

# ---------- FILE UPLOAD ----------
pdf = st.file_uploader("Upload Tamil PDF", type="pdf")

# ---------- FUNCTIONS ----------
def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages:
            if p.extract_text():
                text += p.extract_text() + "\n"
    return text

def extract_text_ocr(file):
    images = convert_from_bytes(file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="tam")
    return text

def extract_questions(text):
    qs = []
    for line in text.split("\n"):
        if re.search(r"(என்ன|எது|யார்|எப்போது|எங்கே|\?)", line):
            qs.append(line.strip())
    return qs

def generate_mcqs(questions):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Convert the following Tamil questions into MCQs.
    Return STRICT JSON.

    [
      {{
        "question": "",
        "options": ["", "", "", ""],
        "answer": ""
      }}
    ]

    Questions:
    {questions[:10]}
    """
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json","").replace("```",""))

# ---------- SESSION ----------
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# ---------- PROCESS ----------
if pdf and api_key:
    if st.button("Generate Practice Test"):
        with st.spinner("Processing PDF..."):
            text = extract_text_pdf(pdf)
            if len(text.strip()) < 50:
                pdf.seek(0)
                text = extract_text_ocr(pdf)

            qs = extract_questions(text)
            st.session_state.mcqs = generate_mcqs(qs)
            st.session_state.start_time = time.time()
            st.success("Test Generated")

# ---------- EXAM MODE ----------
if st.session_state.mcqs:
    duration = 30 * 60  # 30 minutes
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, duration - elapsed)

    st.subheader(f"⏱ Time Left: {remaining//60}:{remaining%60:02}")

    for i, q in enumerate(st.session_state.mcqs):
        st.write(f"{i+1}. {q['question']}")
        st.session_state.answers[i] = st.radio(
            "Choose answer",
            q["options"],
            key=i
        )

    if st.button("Submit Exam"):
        score = 0
        st.divider()
        st.header("📊 Result")

        for i, q in enumerate(st.session_state.mcqs):
            user = st.session_state.answers.get(i)
            correct = q["answer"]
            if user == correct:
                score += 1
                st.success(q["question"])
            else:
                st.error(q["question"])
                st.write("Your:", user)
                st.write("Correct:", correct)

        st.subheader(f"Final Score: {score}/{len(st.session_state.mcqs)}") 
