import streamlit as st
import pdfplumber
import google.generativeai as genai
import json
import os

# --- Configuration ---
st.set_page_config(page_title="PDF Practice Pal", layout="centered")

# --- Sidebar for API Key ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    st.markdown("[Get a Free Key Here](https://aistudio.google.com/app/apikey)")
    st.info("Your key is not saved permanently.")

# --- Helper Functions ---
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def generate_quiz(text_content, num_questions=5):
    # Configure the AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # The Prompt (Instruction to the AI)
    prompt = f"""
    You are a strict teacher. Create a specialized practice test based ONLY on the text below.
    Generate {num_questions} multiple-choice questions.
    
    Return the response in this strict JSON format:
    [
        {{
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The correct option text",
            "explanation": "Why this is correct"
        }}
    ]

    TEXT TO STUDY:
    {text_content[:8000]} 
    """
    # Note: text[:8000] limits text to avoid token errors.

    try:
        response = model.generate_content(prompt)
        # Clean up json formatting if the AI adds markdown backticks
        json_text = response.text.replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return []

# --- Main App Interface ---
st.title("📱 PDF Practice App")
st.write("Upload a PDF to generate a practice test instantly.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Session State (Keeps data alive while you click buttons)
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if uploaded_file and api_key:
    if st.button("Generate Quiz"):
        with st.spinner("Analyzing your document..."):
            text = extract_text_from_pdf(uploaded_file)
            if len(text) > 100:
                st.session_state.quiz = generate_quiz(text)
                st.session_state.answers = {}
                st.session_state.submitted = False
            else:
                st.error("Could not read enough text from this PDF.")

# --- Quiz Display ---
if st.session_state.quiz:
    st.divider()
    
    # Form to hold the inputs
    with st.form("quiz_form"):
        for i, q in enumerate(st.session_state.quiz):
            st.subheader(f"{i + 1}. {q['question']}")
            
            # Radio button for options
            selection = st.radio(
                "Select an answer:",
                q['options'],
                key=f"q_{i}",
                index=None
            )
        
        submit_btn = st.form_submit_button("Submit Answers")
        
        if submit_btn:
            st.session_state.submitted = True

    # --- Results Section ---
    if st.session_state.submitted:
        st.divider()
        st.header("📊 Results")
        score = 0
        total = len(st.session_state.quiz)
        
        for i, q in enumerate(st.session_state.quiz):
            user_ans = st.session_state.get(f"q_{i}")
            correct_ans = q['answer']
            
            if user_ans == correct_ans:
                score += 1
                st.success(f"Q{i+1}: Correct!")
            else:
                st.error(f"Q{i+1}: Wrong.")
                st.markdown(f"**Your Answer:** {user_ans}")
                st.markdown(f"**Correct Answer:** {correct_ans}")
                st.info(f"ℹ️ {q['explanation']}")
        
        st.subheader(f"Final Score: {score} / {total}")
        if score == total:
            st.balloons()

elif uploaded_file and not api_key:
    st.warning("⚠️ Please enter your API Key in the sidebar to start.")
