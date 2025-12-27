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
# The app will save the uploaded file to this specific name to "remember" it.
MASTER_CSV_FILE = "PhD_Review_Assignment_Distribution.csv"
GRADES_CSV_FILE = "grades.csv"

ADMIN_PASSWORD = "phd_admin_2025"  # <--- Change this if needed

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
    """Attempts to load the master list and gradebook from the disk."""
    # 1. Load Master List
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                # Clean header names
                df.columns = [c.strip() for c in df.columns]
                # Ensure Roll number is text
                if 'Roll number' in df.columns:
                    df['Roll number'] = df['Roll number'].astype(str)
                st.session_state.master_list = df
            except Exception as e:
                st.error(f"Error reading saved CSV: {e}")
                st.session_state.master_list = None
        else:
            st.session_state.master_list = None

    # 2. Load Gradebook
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
    """Saves the uploaded CSV to disk so it is remembered permanently."""
    try:
        with open(MASTER_CSV_FILE, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"Could not save file: {e}")
        return False

def extract_text(uploaded_file):
    """Extracts text from PDF/DOCX."""
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
    """Checks content relevance."""
    if not doc_text: return 0.0
    ref_text = f"{topic} {must_cover}".lower()
    clean_doc = doc_text.lower()
    try:
        tfidf = TfidfVectorizer(stop_words='english')
        matrix = tfidf.fit_transform([ref_text, clean_doc])
        return cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100
    except: return 0.0

def calculate_final_grade(scores, penalty, is_rejected):
    raw = sum(scores.values())
    return raw, (0.0 if is_rejected else max(0.0, raw - penalty))

# ==========================================
# MAIN APP INTERFACE
# ==========================================
st.set_page_config(page_title="Ph.D. Assessment System", layout="wide", page_icon="🎓")

# Auto-load data on launch
load_data()

# --- SIDEBAR NAV ---
with st.sidebar:
    st.title("🎓 Access Portal")
    mode = st.radio("Select Mode:", ["Student Portal", "Examiner Portal"])
    st.divider()
    
    # Status Indicators
    st.write("### System Status")
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Loaded ({len(st.session_state.master_list)} students)")
    else:
        st.error("❌ No Class List Found")
    
    if not st.session_state.gradebook.empty:
        st.info(f"📊 {len(st.session_state.gradebook)} assignments graded")

# ==========================================
# MODE 1: STUDENT PORTAL
# ==========================================
if mode == "Student Portal":
    st.title("Student Dashboard")
    st.markdown("Check your assignment details or view your result.")
    
    col_input, col_info = st.columns([1, 2])
    with col_input:
        roll_input = st.text_input("Enter Roll Number:", placeholder="e.g. 1")

    student_data = None
    
    if roll_input and st.session_state.master_list is not None:
        # Match Roll Number
        record = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll_input.strip()]
        if not record.empty:
            student_data = record.iloc[0]
            with col_info:
                st.success(f"**Identified:** {student_data['Student Name']}")
                st.caption(f"Topic: {student_data['Assigned Topic']}")
        else:
            with col_info:
                st.warning("Roll number not found.")
    elif st.session_state.master_list is None:
        st.warning("⚠️ The Examiner has not uploaded the assignment list yet.")

    # Student View Logic
    if student_data is not None:
        st.divider()
        # Check if graded
        graded_rec = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll_input.strip()]
        
        if not graded_rec.empty:
            # Show Result
            res = graded_rec.iloc[-1]
            st.subheader(f"🎉 Result: {res['Final Score']} / 10")
            st.progress(res['Final Score']/10)
            st.write(f"**Examiner Comments:** {res['Examiner Comments']}")
            st.info(f"AI Detected: {res['AI %']}% | Relevance: {res['Relevance %']}%")
        else:
            # Show Simulator
            st.subheader("Draft Simulator (Pre-Submission)")
            st.markdown(f"**Requirements:** {student_data['Must Cover in Review Section']}")
            
            up_test = st.file_uploader("Test your file (PDF/DOCX)", type=['pdf', 'docx'])
            if up_test:
                txt = extract_text(up_test)
                rel = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                st.metric("Relevance Score", f"{rel:.1f}%")
                if rel < 15: st.error("⚠️ Low relevance. Check 'Must Cover' points.")
                else: st.success("✅ Good match!")

# ==========================================
# MODE 2: EXAMINER PORTAL
# ==========================================
elif mode == "Examiner Portal":
    st.title("🔒 Examiner Control Panel")
    
    pwd = st.sidebar.text_input("Enter Password", type="password")
    
    if pwd == ADMIN_PASSWORD:
        
        # --- TABBED INTERFACE ---
        tab1, tab2, tab3 = st.tabs(["📤 Upload & Manage Data", "📝 Grading Console", "📊 View Records"])
        
        # --- TAB 1: DATA MANAGEMENT ---
        with tab1:
            st.header("Manage Assignment List")
            st.write("Upload the `PhD_Review_Assignment_Distribution.csv` file here. The system will **permanently remember** it.")
            
            uploaded_csv = st.file_uploader("Upload Master CSV", type=['csv'])
            
            if uploaded_csv:
                if save_uploaded_file(uploaded_csv):
                    st.toast("File Saved Permanently!", icon="💾")
                    # Reload data immediately
                    st.cache_data.clear()
                    if 'master_list' in st.session_state:
                        del st.session_state['master_list']
                    load_data()
                    st.rerun()

            st.divider()
            st.write("**Current Class List in Memory:**")
            if st.session_state.master_list is not None:
                st.dataframe(st.session_state.master_list)
            else:
                st.warning("No list loaded yet. Please upload CSV above.")

        # --- TAB 2: GRADING ---
        with tab2:
            if st.session_state.master_list is None:
                st.error("Please go to the 'Upload & Manage Data' tab and upload the CSV first.")
            else:
                st.header("Assessment Console")
                
                # Student Selector
                opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
                sel = st.selectbox("Select Student:", ["Select..."] + opts)
                
                if sel != "Select...":
                    r_num = sel.split(" - ")[0]
                    s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                    
                    st.info(f"**Topic:** {s_row['Assigned Topic']}")
                    with st.expander("View Required Content Details"):
                        st.write(s_row['Must Cover in Review Section'])
                    
                    # 1. File Analysis
                    st.write("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**1. Document Check**")
                        u_file = st.file_uploader("Upload Student PDF/DOCX", type=['pdf', 'docx'])
                        rel_v = 0.0
                        if u_file:
                            txt = extract_text(u_file)
                            rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                            st.metric("Relevance", f"{rel_v:.1f}%", delta_color="normal" if rel_v>15 else "inverse")
                    
                    with c2:
                        st.write("**2. AI Integrity**")
                        ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, step=0.1)
                        # Local penalty logic
                        pen_v = 0.0
                        rej = False
                        if ai_inp > 20: 
                            st.error("REJECTED (>20%)")
                            rej = True
                        elif ai_inp > 10:
                            st.warning("WARNING: -2 Marks")
                            pen_v = 2.0
                        else:
                            st.success("SAFE")

                    # 3. Rubric
                    st.write("---")
                    st.write("**3. Academic Rubric**")
                    with st.form("grade_form"):
                        sc = {}
                        dis = rej
                        
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            sc['scholarly_understanding'] = st.slider("Scholarly Understanding", 0.0, 2.0, 1.0, 0.25, disabled=dis)
                            sc['critical_analysis'] = st.slider("Critical Analysis", 0.0, 2.0, 1.0, 0.25, disabled=dis)
                            sc['logical_flow'] = st.slider("Logical Flow", 0.0, 2.0, 1.0, 0.25, disabled=dis)
                        with cc2:
                            sc['literature_usage'] = st.slider("Literature Usage", 0.0, 2.0, 1.0, 0.25, disabled=dis)
                            sc['writing_style'] = st.slider("Writing Style", 0.0, 2.0, 1.0, 0.25, disabled=dis)
                        
                        rem = st.text_area("Final Remarks", disabled=dis)
                        
                        if st.form_submit_button("Save Grade"):
                            _, fin = calculate_final_grade(sc, pen_v, rej)
                            
                            # Save
                            new_row = {
                                "Roll Number": r_num,
                                "Student Name": s_row['Student Name'],
                                "Subtopic": s_row['Assigned Topic'],
                                "Relevance %": round(rel_v, 1),
                                "AI %": ai_inp,
                                "Final Score": fin,
                                "Examiner Comments": rem,
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            new_df = pd.DataFrame([new_row])
                            st.session_state.gradebook = pd.concat([st.session_state.gradebook, new_df], ignore_index=True)
                            st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                            st.success("Grade Saved!")

        # --- TAB 3: RECORDS ---
        with tab3:
            st.header("Gradebook Records")
            if not st.session_state.gradebook.empty:
                st.dataframe(st.session_state.gradebook)
                st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
            else:
                st.info("No grades recorded yet.")
    
    else:
        if pwd: st.error("Incorrect Password")
