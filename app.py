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

# The 5 Quality Criteria (Total 10 Marks)
RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# ==========================================
# LOGIC FUNCTIONS
# ==========================================
def calculate_ai_status(ai_percent):
    """
    Returns: (Message, Penalty, Is_Rejected, Status_Color)
    Rules:
    - 0-10%  : Safe (0 Penalty)
    - 10-20% : -2 Marks
    - 20-30% : -4 Marks
    - >30%   : Rejected (0 Marks)
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
    """
    Formula: (Rubric Sum) - (AI Penalty)
    If Rejected: Score is 0.
    """
    raw_quality_score = sum(scores.values())  # Max 10
    
    if is_rejected:
        final_score = 0.0
    else:
        final_score = max(0.0, raw_quality_score - penalty)
        
    return raw_quality_score, final_score

def check_topic_relevance(doc_text, topic, must_cover):
    """Checks if the document matches the assigned keywords."""
    if not doc_text: return 0.0
    ref_text = f"{topic} {must_cover}".lower()
    clean_doc = doc_text.lower()
    try:
        tfidf = TfidfVectorizer(stop_words='english')
        matrix = tfidf.fit_transform([ref_text, clean_doc])
        return cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100
    except: return 0.0

def load_data():
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                df.columns = [c.strip() for c in df.columns]
                df['Roll number'] = df['Roll number'].astype(str)
                st.session_state.master_list = df
            except: st.session_state.master_list = None
        else: st.session_state.master_list = None

    if 'gradebook' not in st.session_state:
        if os.path.exists(GRADES_CSV_FILE):
            try:
                gb = pd.read_csv(GRADES_CSV_FILE)
                gb['Roll Number'] = gb['Roll Number'].astype(str)
                st.session_state.gradebook = gb
            except:
                st.session_state.gradebook = pd.DataFrame(columns=["Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"])
        else:
            st.session_state.gradebook = pd.DataFrame(columns=["Roll Number", "Student Name", "Subtopic", "Relevance %", "AI %", "Final Score", "Examiner Comments", "Timestamp"])

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

# ==========================================
# MAIN INTERFACE
# ==========================================
st.set_page_config(page_title="Ph.D. Evaluation System", layout="wide", page_icon="🎓")
load_data()

with st.sidebar:
    st.title("🎓 Portal Access")
    mode = st.radio("Select Mode:", ["Student Simulator", "Examiner Console"])
    st.divider()
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Active ({len(st.session_state.master_list)} students)")
    else:
        st.error("❌ No Class List Found")

# ==========================================
# 1. STUDENT SIMULATOR (Self-Check)
# ==========================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Check")
    st.markdown("""
    **Understanding Your Grade:**
    * **Baseline:** AI < 10% ensures no *penalty*.
    * **The Grade:** Your mark (0-10) comes from the **Quality Rubric** below.
    """)
    
    col_login, col_details = st.columns([1, 2])
    with col_login:
        roll = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    if roll and st.session_state.master_list is not None:
        rec = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll.strip()]
        if not rec.empty:
            student_data = rec.iloc[0]
            with col_details:
                st.info(f"**Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Must Cover:** {student_data['Must Cover in Review Section']}")
        else:
            with col_details: st.warning("Roll number not found.")

    if student_data is not None:
        st.divider()
        # Check if already graded
        graded = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll.strip()]
        
        if not graded.empty:
            last = graded.iloc[-1]
            st.subheader("🎉 Your Official Result")
            c1, c2, c3 = st.columns(3)
            c1.metric("Final Grade", f"{last['Final Score']}/10")
            c2.metric("AI Score", f"{last['AI %']}%")
            c3.metric("Status", "Graded")
            st.write(f"**Examiner Comments:** {last['Examiner Comments']}")
        else:
            # === SIMULATOR ===
            st.subheader("🛠️ Grade Simulator")
            
            # 1. Relevance
            st.write("#### Step 1: Content Relevance")
            up_file = st.file_uploader("Check Draft Relevance", type=['pdf', 'docx'])
            if up_file:
                txt = extract_text(up_file)
                rel = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                st.metric("Topic Match", f"{rel:.1f}%")
                if rel < 15: st.error("⚠️ Low relevance. You may lose marks on 'Scholarly Understanding'.")
                else: st.success("✅ Good topic match.")

            st.write("---")
            
            # 2. Rubric Self-Assessment (The "Reality Check")
            col_rubric, col_ai = st.columns([3, 2])
            
            with col_rubric:
                st.write("#### Step 2: Quality Self-Assessment (The Marks)")
                st.caption("Be honest. If your writing is average, you will get ~1.0 per section.")
                
                sim_scores = {}
                sim_scores['scholarly'] = st.slider("Scholarly Understanding (0-2)", 0.0, 2.0, 1.5, 0.25)
                sim_scores['critical'] = st.slider("Critical Analysis (0-2)", 0.0, 2.0, 1.0, 0.25)
                sim_scores['flow'] = st.slider("Logical Flow (0-2)", 0.0, 2.0, 1.0, 0.25)
                sim_scores['lit'] = st.slider("Literature Usage (0-2)", 0.0, 2.0, 1.5, 0.25)
                sim_scores['style'] = st.slider("Writing Style (0-2)", 0.0, 2.0, 1.0, 0.25)
                
                raw_quality = sum(sim_scores.values())
                st.info(f"📝 **Raw Quality Score:** {raw_quality} / 10")

            with col_ai:
                st.write("#### Step 3: AI Penalty Calculator")
                ai_val = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)
                msg, pen, rej, color = calculate_ai_status(ai_val)
                
                # Visual Bar
                st.progress(min(ai_val/100, 1.0))
                
                if rej:
                    st.error(f"⛔ {msg}")
                    st.metric("Penalty", "Total Rejection")
                elif pen > 0:
                    st.warning(f"⚠️ {msg}")
                    st.metric("Penalty", f"-{pen} Marks")
                else:
                    st.success(f"✅ {msg}")
                    st.metric("Penalty", "0 Marks")

            # 3. Final Prediction
            st.write("---")
            _, final_sim = calculate_final_grade(sim_scores, pen, rej)
            
            st.markdown(f"### 📊 Predicted Grade: :blue[{final_sim} / 10]")
            if pen > 0:
                st.caption(f"(Calculated as: Quality {raw_quality} - Penalty {pen} = {final_sim})")
            else:
                st.caption(f"(Calculated as: Quality {raw_quality} - Penalty 0 = {final_sim})")

# ==========================================
# 2. EXAMINER CONSOLE
# ==========================================
elif mode == "Examiner Console":
    st.title("🔒 Examiner Grading Portal")
    if st.sidebar.text_input("Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter Admin Password.")
        st.stop()
        
    tab1, tab2 = st.tabs(["📝 Grading", "⚙️ Upload Data"])
    
    with tab2:
        st.write("Upload 'PhD_Review_Assignment_Distribution.csv'")
        up_csv = st.file_uploader("Upload CSV", type=['csv'])
        if up_csv:
            if save_uploaded_file(up_csv):
                st.toast("Saved!")
                st.cache_data.clear()
                if 'master_list' in st.session_state: del st.session_state['master_list']
                load_data()
                st.rerun()

    with tab1:
        if st.session_state.master_list is None:
            st.error("Please upload student list in 'Upload Data' tab.")
        else:
            opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
            sel = st.selectbox("Select Student:", ["Select..."] + opts)
            
            if sel != "Select...":
                r_num = sel.split(" - ")[0]
                s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                
                st.info(f"**Assigned Topic:** {s_row['Assigned Topic']}")
                with st.expander("View Requirements"):
                    st.write(s_row['Must Cover in Review Section'])
                
                # Grading Area
                with st.form("grading_form"):
                    c1, c2 = st.columns(2)
                    
                    # Left: Analysis
                    with c1:
                        st.subheader("1. Checks")
                        f_up = st.file_uploader("Student File", type=['pdf', 'docx'])
                        rel_v = 0.0
                        if f_up:
                            txt = extract_text(f_up)
                            rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                            st.metric("Content Relevance", f"{rel_v:.1f}%")
                            if rel_v < 15: st.warning("⚠️ Low Relevance")
                        
                        ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, step=0.1)
                        msg, pen, rej, _ = calculate_ai_status(ai_inp)
                        if rej: st.error(f"REJECTED: {msg}")
                        elif pen > 0: st.warning(f"Penalty: -{pen} ({msg})")
                        else: st.success("Safe (No Penalty)")

                    # Right: Rubric
                    with c2:
                        st.subheader("2. Quality Rubric")
                        st.caption("Rate from 0.0 to 2.0 (Default is 1.0)")
                        sc = {}
                        disabled = rej
                        # Default set to 1.0 (Average)
                        for k, v in RUBRIC_CRITERIA.items():
                            sc[k] = st.slider(v, 0.0, 2.0, 1.0, 0.25, disabled=disabled)
                    
                    remarks = st.text_area("Final Remarks", disabled=disabled)
                    
                    if st.form_submit_button("Finalize Grade"):
                        _, fin = calculate_final_grade(sc, pen, rej)
                        new_rec = {
                            "Roll Number": r_num,
                            "Student Name": s_row['Student Name'],
                            "Subtopic": s_row['Assigned Topic'],
                            "Relevance %": round(rel_v, 1),
                            "AI %": ai_inp,
                            "Final Score": fin,
                            "Examiner Comments": remarks,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_rec])], ignore_index=True)
                        st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                        st.success(f"Saved Grade: {fin}/10")

            st.divider()
            if not st.session_state.gradebook.empty:
                st.dataframe(st.session_state.gradebook)
                st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
