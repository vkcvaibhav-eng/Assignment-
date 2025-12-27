import streamlit as st
import pandas as pd
import os
from datetime import datetime
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# CONFIGURATION
# ==========================================
MASTER_CSV_FILE = "PhD_Review_Assignment_Distribution.csv"
GRADES_CSV_FILE = "grades.csv"
ADMIN_PASSWORD = "phd_admin_2025"

RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def calculate_ai_status(ai_percent):
    """
    New Rules:
    0-10%  : Safe (0 penalty)
    10-20% : -2 Marks
    20-30% : -4 Marks
    >30%   : Rejected
    """
    if ai_percent <= 10.0:
        return "Safe (≤10%)", 0.0, False, "success"
    elif ai_percent <= 20.0:
        return "Warning (10-20%)", 2.0, False, "warning"
    elif ai_percent <= 30.0:
        return "Critical Warning (20-30%)", 4.0, False, "error"
    else:
        return "REJECTED (>30%)", 0.0, True, "error"

def calculate_final_grade(scores, penalty, is_rejected):
    raw = sum(scores.values())
    final = 0.0 if is_rejected else max(0.0, raw - penalty)
    return raw, final

def load_data():
    """Loads Master List and Gradebook from disk."""
    # 1. Master List
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                df.columns = [c.strip() for c in df.columns]
                if 'Roll number' in df.columns:
                    df['Roll number'] = df['Roll number'].astype(str)
                st.session_state.master_list = df
            except: st.session_state.master_list = None
        else: st.session_state.master_list = None

    # 2. Gradebook
    if 'gradebook' not in st.session_state:
        if os.path.exists(GRADES_CSV_FILE):
            try:
                gb = pd.read_csv(GRADES_CSV_FILE)
                gb['Roll Number'] = gb['Roll Number'].astype(str)
                st.session_state.gradebook = gb
            except:
                st.session_state.gradebook = pd.DataFrame(columns=[
                    "Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"
                ])
        else:
            st.session_state.gradebook = pd.DataFrame(columns=[
                "Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"
            ])

def save_uploaded_file(uploaded_file):
    try:
        with open(MASTER_CSV_FILE, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except: return False

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                t = page.extract_text()
                if t: text += t + " "
        elif "wordprocessingml" in uploaded_file.type:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + " "
    except: return ""
    return text.strip()

def check_topic_relevance(doc_text, topic, must_cover):
    if not doc_text: return 0.0
    ref_text = f"{topic} {must_cover}".lower()
    clean_doc = doc_text.lower()
    try:
        tfidf = TfidfVectorizer(stop_words='english')
        matrix = tfidf.fit_transform([ref_text, clean_doc])
        return cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100
    except: return 0.0

# ==========================================
# MAIN APP
# ==========================================
st.set_page_config(page_title="Ph.D. Assessment System", layout="wide", page_icon="🎓")
load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 Portal Access")
    mode = st.radio("Select Interface:", ["Student Dashboard", "Examiner Console"])
    st.divider()
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Active ({len(st.session_state.master_list)} students)")
    else:
        st.error("❌ No Class List Found")

# ==========================================
# MODE 1: STUDENT DASHBOARD
# ==========================================
if mode == "Student Dashboard":
    st.title("🎓 Student Assessment Hub")
    st.markdown("Enter your Roll Number to access your personalized topic and **Pre-Submission Simulator**.")
    
    col_in, col_det = st.columns([1, 2])
    with col_in:
        roll = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    if roll and st.session_state.master_list is not None:
        rec = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll.strip()]
        if not rec.empty:
            student_data = rec.iloc[0]
            with col_det:
                st.success(f"**Welcome, {student_data['Student Name']}**")
                st.info(f"**Assigned Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Required Content:** {student_data['Must Cover in Review Section']}")
        else:
            with col_det: st.warning("Roll number not found.")
    
    if student_data is not None:
        st.divider()
        # Check if already graded
        graded = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll.strip()]
        
        if not graded.empty:
            # === OFFICIAL RESULT ===
            last_grade = graded.iloc[-1]
            st.subheader("🎉 Official Grade Report")
            c1, c2, c3 = st.columns(3)
            c1.metric("Final Score", f"{last_grade['Final Score']} / 10")
            c2.metric("AI Penalty", f"{last_grade['AI %']}%")
            c3.metric("Status", "Evaluated")
            st.write(f"**Examiner Remarks:** {last_grade['Examiner Comments']}")
        else:
            # === SIMULATOR ===
            st.subheader("🛠️ Grade Simulator")
            st.markdown("See exactly how StealthWriter scores affect your mark.")
            
            # 1. Relevance Check
            st.write("#### Step 1: Content Relevance")
            test_file = st.file_uploader("Upload Draft to Check Topic Match", type=['pdf', 'docx'])
            if test_file:
                txt = extract_text(test_file)
                rel = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                st.metric("Relevance Score", f"{rel:.1f}%")
                if rel < 15: st.error("⚠️ Your content is off-topic. Please include the required keywords.")
                else: st.success("✅ Content looks relevant.")
            
            # 2. AI & Mark Calculator
            st.write("---")
            st.write("#### Step 2: AI Penalty Calculator")
            
            col_calc1, col_calc2 = st.columns([1, 1])
            
            with col_calc1:
                st.markdown("**StealthWriter Score Input**")
                sim_ai = st.number_input("Enter AI % from report:", 0.0, 100.0, 5.0, step=0.1)
                
                # Visual Bar logic
                bar_val = min(sim_ai / 100.0, 1.0)
                msg, pen, rej, color = calculate_ai_status(sim_ai)
                
                # Display Progress Bar with color context
                if rej
