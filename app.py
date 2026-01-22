import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re

st.set_page_config(page_title="Tamil PDF Practice App")

st.title("📘 Tamil PDF Practice App")
st.write("Upload Tamil PDF (Text or Scanned)")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

# ---------- TEXT PDF ----------
def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

# ---------- OCR PDF ----------
def extract_text_ocr(file):
    images = convert_from_bytes(file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="tam") + "\n"
    return text

# ---------- QUESTION EXTRACTION ----------
def extract_questions(text):
    lines = text.split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        # Tamil question patterns
        if re.search(r"(என்ன|எது|யார்|எப்போது|எங்கே|\?)", line):
            questions.append(line)
    return questions

if uploaded_file:
    with st.spinner("Processing PDF..."):
        text = extract_text_pdf(uploaded_file)

        # If text is too small → assume scanned PDF
        if len(text.strip()) < 50:
            uploaded_file.seek(0)
            text = extract_text_ocr(uploaded_file)

    st.success("Text Extracted Successfully")

    questions = extract_questions(text)

    if questions:
        st.header("📝 Practice Questions")
        for i, q in enumerate(questions, 1):
            st.write(f"{i}. {q}")
            st.text_input("Your Answer", key=i)
    else:
        st.warning("No questions detected. Try a clearer PDF.")
