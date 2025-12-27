import streamlit as st
import pandas as pd
import os
from datetime import datetime
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# CONFIGURATION & FILE PATHS
# ==========================================
# The app will look for these files automatically
MASTER_CSV_FILE = "PhD_Review_Assignment_Distribution.csv"
GRADES_CSV_FILE = "grades.csv"

ADMIN_PASSWORD = "phd_admin_2025"  # <--- Change this password if needed

RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

AI_PENALTY_RULES = {
    "threshold_safe": 10.0,
    "threshold_warn": 20.0,
    "penalty_score": 2.0
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def load_data():
    """Loads master list and gradebook from local files."""
    # 1. Load Master Assignment List
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                # Clean up column names
                df.columns = [c.strip() for c in df.columns]
                # Ensure 'Roll number' is string for matching
                if 'Roll number' in df.columns:
                    df['Roll number'] = df['Roll number'].astype(str)
                st.session_state.master_list = df
            except Exception as e:
                st.error(f"Error loading Master CSV: {e}")
                st.session_state.master_list = None
        else:
            st.session_state.master_list = None

    # 2. Load Gradebook
    if 'gradebook' not in st.session_state:
        if os.path.exists(GRADES_CSV_FILE):
            try:
                st.session_state.gradebook = pd.read_csv(GRADES_CSV_FILE)
                # Ensure Roll Number is string
                st.session_state.gradebook['Roll Number'] = st.session_state.gradebook['Roll Number'].astype(str)
            except:
                st.session_state.gradebook = pd.DataFrame(columns=[
                    "Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"
                ])
        else:
            st.session_state.gradebook = pd.DataFrame(columns=[
                "Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"
            ])

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

def calculate_ai_status(ai_percent):
    if ai_percent <= AI_PENALTY_RULES['threshold_safe']:
        return "Safe (≤10%)", 0.0, False
    elif ai_percent <= AI_PENALTY_RULES['threshold_warn']:
        return "Warning (10-20%)", AI_PENALTY_RULES['penalty_score'], False
    else:
        return "REJECTED (>20%)", 0.0, True

def calculate_final_grade(scores, penalty, is_rejected):
    raw = sum(scores.values())
    return raw, (0.0 if is_rejected else max(0.0, raw - penalty))

# ==========================================
# MAIN APP INTERFACE
# ==========================================
st.set_page_config(page_title="Ph.D. Assessment Portal", layout="wide", page_icon="🎓")

# Load Data on Startup
load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 Access Portal")
    mode = st.radio("Select Mode:", ["Student Portal", "Examiner Portal"])
    
    st.divider()
    st.markdown("### 📂 Data Status")
    
    # Check Master File
    if st.session_state.master_list is not None:
        st.success("✅ Assignment List: Loaded")
    else:
        st.error(f"❌ '{MASTER_CSV_FILE}' not found.")
        st.info("Please ensure the CSV file is in the same folder as this script.")

    # Check Gradebook
    if not st.session_state.gradebook.empty:
        st.success(f"✅ Gradebook: {len(st.session_state.gradebook)} Records")
    else:
        st.info("ℹ️ Gradebook: Empty")

# ==========================================
# MODE 1: STUDENT PORTAL (View Grade OR Simulate)
# ==========================================
if mode == "Student Portal":
    st.title("🎓 Student Dashboard")
    st.markdown("Enter your Roll Number to view your assignment details or check your results.")
    
    col_input, col_info = st.columns([1, 2])
    
    with col_input:
        roll_input = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    
    # Identify Student
    if roll_input and st.session_state.master_list is not None:
        record = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll_input.strip()]
        
        if not record.empty:
            student_data = record.iloc[0]
            with col_info:
                st.subheader(f"Welcome, {student_data['Student Name']}")
                st.info(f"**Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Requirements:** {student_data['Must Cover in Review Section']}")
        else:
            with col_info:
                st.warning("Roll number not found.")

    # Show Grade OR Simulator
    if student_data is not None:
        st.divider()
        
        # CHECK IF GRADED
        graded_record = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll_input.strip()]
        
        if not graded_record.empty:
            # === VIEW OFFICIAL GRADE ===
            st.success("🎉 **Your Official Grade is Available**")
            result = graded_record.iloc[-1] # Get latest grade
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Final Score", f"{result['Final Score']} / 10")
            m2.metric("AI Detected", f"{result['AI %']}%")
            m3.metric("Status", "Pass" if result['Final Score'] >= 5 else "Review Needed")
            
            st.subheader("Examiner Feedback:")
            st.markdown(f"> {result['Examiner Comments']}")
            
        else:
            # === SHOW SIMULATOR (Not graded yet) ===
            st.warning("ℹ️ Your assignment has not been graded yet. Use the tool below to test your draft.")
            st.subheader("🛠️ Pre-Submission Simulator")
            
            # Simulator Logic
            up_file = st.file_uploader("Upload Draft to Test Relevance", type=['pdf', 'docx'])
            if up_file:
                txt = extract_text(up_file)
                rel = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                if rel > 15: st.success(f"✅ Relevance Check: {rel:.1f}% (Good Match)")
                else: st.error(f"⚠️ Relevance Check: {rel:.1f}% (Too Low - Check 'Must Cover' points)")
            
            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Penalty Checker**")
                s_ai = st.number_input("Est. AI %", 0, 100, 5)
                msg, pen, rej = calculate_ai_status(s_ai)
                if rej: st.error(msg)
                elif pen: st.warning(msg)
                else: st.success(msg)
            with c2:
                st.write("**Rubric Estimate**")
                s_score = st.slider("Est. Quality (0-10)", 0.0, 10.0, 7.0)
                _, s_final = calculate_final_grade({'t':s_score}, pen, rej)
                st.metric("Predicted Score", f"{s_final}/10")

# ==========================================
# MODE 2: EXAMINER PORTAL (Grading)
# ==========================================
elif mode == "Examiner Portal":
    st.title("🔒 Examiner Grading")
    
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Enter password to unlock.")
        st.stop()
    
    if st.session_state.master_list is None:
        st.error(f"Missing '{MASTER_CSV_FILE}'. Please put it in the app folder.")
        st.stop()
        
    st.subheader("Grade a Student")
    # Dropdown for selecting student instead of typing ID
    # Create list of "Roll - Name"
    student_options = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
    selected_stu = st.selectbox("Select Student:", ["Select..."] + student_options)
    
    if selected_stu != "Select...":
        roll_num = selected_stu.split(" - ")[0]
        stu_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll_num].iloc[0]
        
        st.info(f"**Topic:** {stu_row['Assigned Topic']}\n\n**Must Cover:** {stu_row['Must Cover in Review Section']}")
        
        # Grading Form
        with st.form("grading_form"):
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 1. Integrity Check")
                # Document Relevance
                ex_file = st.file_uploader("Upload Submission", type=['pdf', 'docx'])
                rel_val = 0.0
                if ex_file:
                    with st.spinner("Analyzing..."):
                        txt = extract_text(ex_file)
                        rel_val = check_topic_relevance(txt, stu_row['Assigned Topic'], stu_row['Must Cover in Review Section'])
                    st.metric("Content Relevance", f"{rel_val:.1f}%", delta_color="normal" if rel_val>15 else "inverse")
                
                # AI Check
                ai_val = st.number_input("StealthWriter AI %", 0.0, 100.0, step=0.1)
                stat_msg, pen_val, is_rej = calculate_ai_status(ai_val)
                if is_rej: st.error(f"⛔ {stat_msg}")
                elif pen_val > 0: st.warning(f"⚠️ {stat_msg}")
                else: st.success(f"✅ {stat_msg}")

            with col_right:
                st.markdown("#### 2. Rubric Evaluation")
                scores = {}
                disabled = is_rej
                for key, label in RUBRIC_CRITERIA.items():
                    scores[key] = st.slider(label, 0.0, 2.0, 1.0, 0.25, disabled=disabled)
            
            comments = st.text_area("Examiner Remarks", disabled=disabled)
            submit = st.form_submit_button("💾 Save & Publish Grade")
            
            if submit:
                raw_s, final_s = calculate_final_grade(scores, pen_val, is_rej)
                
                # New Record
                new_record = {
                    "Roll Number": roll_num,
                    "Student Name": stu_row['Student Name'],
                    "Subtopic": stu_row['Assigned Topic'],
                    "Relevance %": round(rel_val, 1),
                    "AI %": ai_val,
                    "Final Score": final_s,
                    "Examiner Comments": comments,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                
                # Update Session State
                new_df = pd.DataFrame([new_record])
                st.session_state.gradebook = pd.concat([st.session_state.gradebook, new_df], ignore_index=True)
                
                # SAVE TO DISK (Permanent)
                st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                
                st.success(f"✅ Grade Recorded for {stu_row['Student Name']}! (Saved to {GRADES_CSV_FILE})")

    # Show Database
    st.divider()
    with st.expander("View All Records (Gradebook)"):
        st.dataframe(st.session_state.gradebook)
        st.download_button("Download Gradebook CSV", st.session_state.gradebook.to_csv(index=False), "final_grades.csv")
