import streamlit as st
import google.generativeai as genai
import json
from gtts import gTTS
import base64

# --- Page Configuration ---
st.set_page_config(page_title="Tamil Practice Master", layout="centered")

# --- Custom CSS for Tamil Readability ---
st.markdown("""
    <style>
    .tamil-text {
        font-size: 18px !important;
        font-family: 'Nirmala UI', 'Latha', sans-serif;
        line-height: 1.8;
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Step 1: Read & Extract Text\nStep 2: Generate Quiz")

# --- Helper Functions ---
def get_audio_html(text):
    """Generates an HTML audio player for Tamil text"""
    try:
        # Generate audio for first 1000 chars to keep it fast
        tts = gTTS(text=text[:1000], lang='ta')
        filename = "temp_audio.mp3"
        tts.save(filename)
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
        return f"""
            <audio controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
    except Exception as e:
        return f"Audio Error: {e}"

def extract_text_with_ai(file_bytes):
    """Uses Gemini Vision to OCR the Tamil PDF"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    You are an expert Tamil Transcriber. 
    Look at this PDF document. 
    1. Extract all the text content into clear, readable Tamil Unicode.
    2. Do NOT summarize. I need the full text for study.
    3. Ignore page numbers or headers.
    """
    try:
        response = model.generate_content([
            {'mime_type': 'application/pdf', 'data': file_bytes},
            prompt
        ])
        return response.text
    except Exception as e:
        st.error(f"Extraction Error: {e}")
        return None

def generate_quiz_from_text(text):
    """Generates JSON Quiz from the extracted text"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Based on the Tamil text provided below, create a Practice Test.
    Generate 5 Multiple Choice Questions in Tamil.
    
    Strictly follow this JSON format:
    [
        {{
            "question": "Question in Tamil",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The correct option content",
            "explanation": "Why it is correct (in Tamil)"
        }}
    ]

    TEXT:
    {text[:10000]}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "")
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"Quiz Generation Error: {e}")
        return None

# --- Main App Interface ---
st.title("📚 Tamil Study & Practice")

uploaded_file = st.file_uploader("Upload Tamil PDF", type="pdf")

if uploaded_file and api_key:
    
    # --- Step 1: Processing Button ---
    if st.button("🚀 Process PDF (Read & Analyze)"):
        with st.spinner("AI is reading the Tamil font..."):
            file_bytes = uploaded_file.getvalue()
            text = extract_text_with_ai(file_bytes)
            if text:
                st.session_state.extracted_text = text
                st.session_state.quiz_data = None # Reset quiz if new file
                st.success("PDF Read Successfully!")

    # --- Step 2: Display Content (Tabs) ---
    if st.session_state.extracted_text:
        
        tab1, tab2 = st.tabs(["📖 Read & Listen (படி)", "📝 Practice Quiz (பயிற்சி)"])
        
        # === TAB 1: READER ===
        with tab1:
            st.subheader("🔊 Audio Lesson")
            if st.button("▶️ Play Audio"):
                st.markdown(get_audio_html(st.session_state.extracted_text), unsafe_allow_html=True)
            
            st.subheader("📄 Document Text")
            st.markdown(f'<div class="tamil-text">{st.session_state.extracted_text}</div>', unsafe_allow_html=True)

        # === TAB 2: QUIZ ===
        with tab2:
            if st.session_state.quiz_data is None:
                st.write("Ready to practice?")
                if st.button("Generate Quiz Now"):
                    with st.spinner("Creating questions..."):
                        st.session_state.quiz_data = generate_quiz_from_text(st.session_state.extracted_text)
                        st.session_state.quiz_submitted = False
                        st.rerun()
            
            # Show Quiz if it exists
            if st.session_state.quiz_data:
                with st.form("quiz_form"):
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        st.radio("Select:", q['options'], key=f"q_{i}", label_visibility="collapsed")
                        st.markdown("---")
                    
                    if st.form_submit_button("Submit Answers"):
                        st.session_state.quiz_submitted = True
                
                # Show Results
                if st.session_state.quiz_submitted:
                    st.divider()
                    st.subheader("Results / முடிவுகள்")
                    score = 0
                    for i, q in enumerate(st.session_state.quiz_data):
                        user_val = st.session_state.get(f"q_{i}")
                        if user_val == q['answer']:
                            score += 1
                            st.success(f"Q{i+1} Correct!")
                        else:
                            st.error(f"Q{i+1} Wrong.")
                            st.write(f"Correct: {q['answer']}")
                            st.info(f"💡 {q['explanation']}")
                    st.metric("Score", f"{score}/{len(st.session_state.quiz_data)}")

elif uploaded_file and not api_key:
    st.warning("Please enter your API Key in the sidebar.")
