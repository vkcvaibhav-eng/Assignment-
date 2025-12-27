import streamlit as st
import pandas as pd
import os
from datetime import datetime
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. CONFIGURATION
# ==========================================
MASTER_CSV_FILE = "PhD_Review_Assignment_Distribution.csv"
GRADES_CSV_FILE = "grades.csv"
ADMIN_PASSWORD = "phd_admin_2025"
STARTING_SCORE = 1.0  # Default value for all sliders

RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# ==========================================
# 2. CALCULATION ENGINE
# ==========================================
def calculate_penalties(ai_percent, rel_percent):
    # AI Rules
    if ai_percent > 30.0:
        ai_pen = 10.0; ai_msg = "REJECTED (AI > 30%)"; ai_rej = True
    elif ai_percent > 20.0:
        ai_pen = 4.0; ai_msg = "Critical (-4 Marks)"; ai_rej = False
    elif ai_percent > 10.0:
        ai_pen = 2.0; ai_msg = "Warning (-2 Marks)"; ai_rej = False
    else:
        ai_pen = 0.0; ai_msg = "Safe"; ai_rej = False

    # Relevance Rules
    if rel_percent < 5.0:
        rel_pen = 10.0; rel_msg = "IRRELEVANT (<5%)"; rel_rej = True
    elif rel_percent < 15.0:
        rel_pen = 2.0; rel_msg = "Weak Match (-2 Marks)"; rel_rej = False
    else:
        rel_pen = 0.0; rel_msg = "Safe"; rel_rej = False

    return ai_pen, ai_msg, rel_pen, rel_msg, (ai_rej or rel_rej)

def calculate_final_score(rubric_scores, ai_pct, rel_pct):
    raw = sum(rubric_scores.values())
    ai_p, ai_m, rel_p, rel_m, is_rej = calculate_penalties(ai_pct, rel_pct)
    
    if is_rej:
        final = 0.0
    else:
        final = max(0.0, raw - ai_p - rel_p)
        
    return {
        "raw": raw, "final": final, 
        "ai_pen": ai_p, "ai_msg": ai_m, 
        "rel_pen": rel_p, "rel_msg": rel_m, 
        "rejected": is_rej
    }

def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                t = page.extract_text()
                if t: text += t + " "
        else:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + " "
    except: return ""
    return text.strip()

def check_topic_relevance(doc_text, topic, must_cover):
    if not doc_text: return 0.0
    ref = f"{str(topic)} {str(must_cover)}".lower()
    try:
        tfidf = TfidfVectorizer(stop_words='english')
        matrix = tfidf.fit_transform([ref, doc_text.lower()])
        return cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100
    except: return 0.0

def load_data():
    # 1. Master List
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                df.columns = [c.strip() for c in df.columns]
                df['Roll number'] = df['Roll number'].astype(str).str.strip()
                st.session_state.master_list = df
            except: st.session_state.master_list = None
        else: st.session_state.master_list = None

    # 2. Gradebook (Force Load with ALL Rubric Columns)
    if 'gradebook' not in st.session_state:
        base_cols = ["Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"]
        rubric_cols = list(RUBRIC_CRITERIA.keys())
        all_cols = base_cols + rubric_cols
        
        if os.path.exists(GRADES_CSV_FILE):
            try:
                gb = pd.read_csv(GRADES_CSV_FILE)
                gb['Roll Number'] = gb['Roll Number'].astype(str).str.strip()
                
                # Check for missing columns (Old file format fix)
                for col in rubric_cols:
                    if col not in gb.columns:
                        gb[col] = STARTING_SCORE # Default if missing
                        
                st.session_state.gradebook = gb
            except:
                st.session_state.gradebook = pd.DataFrame(columns=all_cols)
        else:
            st.session_state.gradebook = pd.DataFrame(columns
