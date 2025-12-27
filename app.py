import streamlit as st
import pandas as pd
from datetime import datetime
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# CONFIGURATION
# ==========================================
RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

AI_PENALTY_RULES = {
    "threshold_safe": 10.0,   # 0-10%: Safe
    "threshold_warn": 20.0,   # 10-20%: Warning
    "penalty_score": 2.0      # Marks deducted in warning zone
}

ADMIN_PASSWORD = "phd_admin_2025"  # <--- CHANGE THIS PASSWORD

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def extract_text(uploaded_file):
    """Extracts raw text from PDF or DOCX files."""
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + " "
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""
    return text.strip()

def check_topic_relevance(doc_text, topic_text, must_cover_text):
    """
    Checks similarity against both the Topic AND the 'Must Cover' details.
    This provides a much stricter and accurate relevance check.
    """
    if not doc_text:
        return 0.0
    
    # Combine Topic + Details for a rich keyword source
    reference_text = f"{topic_text} {must_cover_text}".lower()
    clean_doc = doc_text.lower()
    
    documents = [reference_text, clean_doc]
    
    # Calculate Cosine Similarity
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return similarity[0][0] * 100
    except:
        return 0.0

def calculate_ai_status(ai_percent):
    if ai_percent <= AI_PENALTY_RULES['threshold_safe']:
        return "Safe (≤10%)", 0.0, False, "success"
    elif ai_percent <= AI_PENALTY_RULES['threshold_warn']:
        return "Warning (10-20%)", AI_PENALTY_RULES['penalty_score'], False, "warning"
    else:
        return "REJECTED (>20%)", 0.0, True, "error"

def calculate_final_grade(scores, penalty, is_rejected):
    raw_total = sum(scores.values())
    final_score = 0.0 if is_rejected else max(0.0, raw_total - penalty)
    return raw_total, final_score

# ==========================================
# MAIN APPLICATION
# ==========================================
st.set_page_config(page_title="Ph.D. Academic Assessment System", layout="wide", page_icon="🎓")

# Initialize Session State
if 'gradebook' not in st.session_state:
    st.session_state.gradebook = pd.DataFrame(columns=[
        "Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"
    ])
if 'master_list' not in st.session_state:
    st.session_state.master_list = None

# --- SIDEBAR: SETUP & NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2995/2995620.png", width=50)
    st.title("System Controls")
    
    mode = st.radio("Select Operation Mode:", ["Student Simulator", "Examiner Grading"])
    
    st.divider()
    st.subheader("📁 Master Data Setup")
    st.info("Upload 'PhD_Review_Assignment_Distribution.csv'")
    
    uploaded_master = st.file_uploader("Upload Assignment List (CSV)", type=['csv'])
    
    if uploaded_master:
        try:
            df = pd.read_csv(uploaded_master)
            # Normalize column names just in case
            df.columns = [c.strip() for c in df.columns]
            
            # Verify required columns exist
            required_cols = ["Roll number", "Student Name", "Assigned Topic", "Must Cover in Review Section"]
            if all(col in df.columns for col in required_cols):
                # Convert Roll number to string for easy searching
                df['Roll number'] = df['Roll number'].astype(str)
                st.session_state.master_list = df
                st.success(f"✅ Loaded {len(df)} student assignments.")
            else:
                st.error(f"CSV format error. Required columns: {required_cols}")
        except Exception as e:
            st.error(f"Error loading CSV: {e}")

# ==========================================
# MODE 1: STUDENT SIMULATOR
# ==========================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Simulator")
    st.markdown("Enter your Roll Number to see your specific requirements and test your draft.")
    st.divider()

    # Step 1: ID Check
    col_input, col_details = st.columns([1, 2])
    student_record = None
    
    with col_input:
        roll_input = st.text_input("Enter Roll Number:", placeholder="e.g., 1")
    
    if st.session_state.master_list is not None and roll_input:
        # Search by Roll Number
        record = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll_input.strip()]
        
        if not record.empty:
            student_record = record.iloc[0]
            
            with col_details:
                st.subheader(f"👋 Welcome, {student_record['Student Name']}")
                st.info(f"**Assigned Topic:** {student_record['Assigned Topic']}")
                st.warning(f"**📌 MUST COVER:** {student_record['Must Cover in Review Section']}")
        else:
            with col_details:
                st.error("Roll number not found.")
    elif st.session_state.master_list is None:
        st.warning("⚠️ System pending initialization by Examiner.")

    # Step 2: Relevance Check (Only if student identified)
    if student_record is not None:
        st.divider()
        st.subheader("1. Content Relevance Check")
        st.caption("The system checks if your draft actually covers the 'Must Cover' points.")
        
        student_file = st.file_uploader("Upload Draft (PDF/DOCX)", type=['pdf', 'docx'])
        
        if student_file:
            with st.spinner("Analyzing document content against your specific topic..."):
                text_content = extract_text(student_file)
                # Smart Check: Topic + Must Cover details
                rel_score = check_topic_relevance(
                    text_content, 
                    student_record['Assigned Topic'], 
                    student_record['Must Cover in Review Section']
                )
                
            col_score, col_advice = st.columns([1, 3])
            
            with col_score:
                st.metric("Relevance Score", f"{rel_score:.1f}%")
            
            with col_advice:
                if rel_score > 15.0:
                    st.success("✅ **Good Match:** Your content covers the assigned requirements well.")
                else:
                    st.error(f"⚠️ **Low Relevance:** Your draft is missing key terms from your 'Must Cover' section. Make sure you discuss: {student_record['Must Cover in Review Section'][:100]}...")

        # Step 3: Grade Prediction
        st.subheader("2. Grade Predictor")
        
        c1, c2 = st.columns(2)
        with c1:
            sim_ai = st.number_input("Enter your StealthWriter AI Score:", 0.0, 100.0, 5.0, step=0.5)
            status_msg, penalty, rejected, color = calculate_ai_status(sim_ai)
            
            if rejected:
                st.error(f"❌ Status: {status_msg}")
            elif penalty > 0:
                st.warning(f"⚠️ Status: {status_msg}")
            else:
                st.success(f"✅ Status: {status_msg}")

        with c2:
            st.markdown("**Self-Evaluation (Rubric Estimates)**")
            sim_raw = st.slider("Estimated Rubric Score (out of 10)", 0.0, 10.0, 7.5, 0.5)
            
        # Prediction Result
        _, final_sim = calculate_final_grade({'total': sim_raw}, penalty, rejected)
        
        st.metric("Predicted Final Grade", f"{final_sim} / 10")


# ==========================================
# MODE 2: EXAMINER GRADING
# ==========================================
elif mode == "Examiner Grading":
    st.title("🔒 Examiner Evaluation Portal")
    
    if st.sidebar.text_input("Enter Admin Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter password to access.")
        st.stop()

    if st.session_state.master_list is None:
        st.error("Upload Master CSV first.")
        st.stop()

    # Input ID
    exam_roll = st.text_input("Enter Student Roll Number to Grade:")
    
    if exam_roll:
        # Fetch Data
        record = st.session_state.master_list[st.session_state.master_list['Roll number'] == exam_roll.strip()]
        
        if not record.empty:
            stu_data = record.iloc[0]
            st.markdown(f"**Student:** {stu_data['Student Name']} | **Topic:** {stu_data['Assigned Topic']}")
            st.caption(f"**Requirements:** {stu_data['Must Cover in Review Section']}")
            
            # File Upload & Analysis
            exam_file = st.file_uploader("Upload Submission", type=['pdf', 'docx'], key="exam_upload")
            
            rel_score = 0.0
            if exam_file:
                doc_text = extract_text(exam_file)
                rel_score = check_topic_relevance(
                    doc_text, 
                    stu_data['Assigned Topic'], 
                    stu_data['Must Cover in Review Section']
                )
                
                # Metrics Dashboard
                m1, m2, m3 = st.columns(3)
                m1.metric("Content Relevance", f"{rel_score:.1f}%", delta_color="normal" if rel_score > 15 else "inverse")
                
                with st.form("grading_form"):
                    col_ai, col_rubric = st.columns([1, 2])
                    
                    with col_ai:
                        ai_input = st.number_input("StealthWriter AI %", 0.0, 100.0, step=0.1)
                        status_msg, penalty, rejected, _ = calculate_ai_status(ai_input)
                        if rejected: st.error("REJECTED");
                        elif penalty > 0: st.warning(f"Penalty: -{penalty}")
                    
                    with col_rubric:
                        scores = {k: st.slider(v, 0.0, 2.0, 1.0, 0.25, disabled=rejected) for k, v in RUBRIC_CRITERIA.items()}
                    
                    comments = st.text_area("Remarks", disabled=rejected)
                    
                    if st.form_submit_button("Save Grade"):
                        raw_tot, final_tot = calculate_final_grade(scores, penalty, rejected)
                        
                        new_entry = {
                            "Roll Number": exam_roll,
                            "Student Name": stu_data['Student Name'],
                            "Subtopic": stu_data['Assigned Topic'],
                            "Relevance %": round(rel_score, 1),
                            "AI %": ai_input,
                            "Final Score": final_tot,
                            "Examiner Comments": comments,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        
                        st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_entry])], ignore_index=True)
                        st.success("✅ Grade Saved!")

    # Show Records
    st.divider()
    if not st.session_state.gradebook.empty:
        st.dataframe(st.session_state.gradebook)
        st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
