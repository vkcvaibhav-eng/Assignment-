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

RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# ==========================================
# 2. LOGIC FUNCTIONS
# ==========================================

def calculate_ai_status(ai_percent):
    """
    AI Rules:
    - >30%: Reject
    - >20%: -4 Marks
    - >10%: -2 Marks
    """
    if ai_percent <= 10.0:
        return "Safe", 0.0, False, "success"
    elif ai_percent <= 20.0:
        return "Warning (-2 Marks)", 2.0, False, "warning"
    elif ai_percent <= 30.0:
        return "Critical (-4 Marks)", 4.0, False, "error"
    else:
        return "REJECTED (AI > 30%)", 0.0, True, "error"

def calculate_relevance_status(rel_percent):
    """
    Relevance Rules (NEW):
    - < 5%: Reject (0 Marks) -> Likely wrong file
    - < 15%: -2 Marks -> Poorly covered topic
    - >= 15%: Safe
    """
    if rel_percent >= 15.0:
        return "Safe", 0.0, False, "success"
    elif rel_percent >= 5.0:
        return "Low Relevance (-2 Marks)", 2.0, False, "warning"
    else:
        return "Irrelevant Content (< 5%)", 0.0, True, "error"

def calculate_final_grade(scores, ai_penalty, rel_penalty, is_rejected):
    """
    Formula: Quality - AI Penalty - Relevance Penalty
    """
    raw_quality = sum(scores.values())  # Max 10.0
    
    if is_rejected:
        final_score = 0.0
    else:
        # Subtract both penalties
        total_penalty = ai_penalty + rel_penalty
        final_score = max(0.0, raw_quality - total_penalty)
        
    return raw_quality, final_score

def check_topic_relevance(doc_text, topic, must_cover):
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
# 3. MAIN APPLICATION
# ==========================================
st.set_page_config(page_title="Ph.D. Evaluation System", layout="wide", page_icon="🎓")
load_data()

with st.sidebar:
    st.title("🎓 Portal Access")
    mode = st.radio("Select Interface:", ["Student Simulator", "Examiner Console"])
    st.divider()
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Active")
    else:
        st.error("❌ Master List Missing")

# =======================================================
# MODE 1: STUDENT SIMULATOR (With Relevance Penalty)
# =======================================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Check")
    st.markdown("Check how **Relevance** and **AI Penalties** impact your grade.")
    
    col_login, col_info = st.columns([1, 2])
    with col_login:
        roll = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    if roll and st.session_state.master_list is not None:
        rec = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll.strip()]
        if not rec.empty:
            student_data = rec.iloc[0]
            with col_info:
                st.info(f"**Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Must Cover:** {student_data['Must Cover in Review Section']}")
        else:
            with col_info: st.warning("Roll number not found.")

    if student_data is not None:
        st.divider()
        graded = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll.strip()]
        
        if not graded.empty:
            last = graded.iloc[-1]
            st.subheader("🎉 Your Official Result")
            m1, m2, m3 = st.columns(3)
            m1.metric("Final Grade", f"{last['Final Score']}/10")
            m2.metric("AI Score", f"{last['AI %']}%")
            m3.metric("Relevance", f"{last['Relevance %']}%")
            st.write(f"**Examiner Remarks:** {last['Examiner Comments']}")
        else:
            # === SIMULATOR ===
            st.subheader("🛠️ Grade Simulator")
            
            c_left, c_right = st.columns(2)
            
            with c_left:
                st.write("#### 1. Content Relevance Check")
                up_file = st.file_uploader("Upload Draft", type=['pdf', 'docx'])
                rel_val = 0.0
                if up_file:
                    txt = extract_text(up_file)
                    rel_val = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                
                # Relevance Logic Visuals
                rel_msg, rel_pen, rel_rej, rel_col = calculate_relevance_status(rel_val)
                st.metric("Relevance Score", f"{rel_val:.1f}%")
                if rel_rej:
                    st.error(f"⛔ {rel_msg}")
                elif rel_pen > 0:
                    st.warning(f"⚠️ {rel_msg}")
                else:
                    st.success(f"✅ {rel_msg}")

                st.write("---")
                st.write("#### 2. AI Penalty Check")
                ai_val = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)
                ai_msg, ai_pen, ai_rej, _ = calculate_ai_status(ai_val)
                
                if ai_rej: st.error(f"⛔ {ai_msg}")
                elif ai_pen > 0: st.warning(f"⚠️ {ai_msg}")
                else: st.success(f"✅ {ai_msg}")

            with c_right:
                st.write("#### 3. Quality Self-Assessment")
                sim_scores = {}
                for key, label in RUBRIC_CRITERIA.items():
                    sim_scores[key] = st.slider(label, 0.0, 2.0, 1.0, 0.25, key=f"sim_{key}")
                
                raw_quality = sum(sim_scores.values())
            
            # Final Calculation
            st.markdown("---")
            is_rejected = ai_rej or rel_rej
            _, final_sim = calculate_final_grade(sim_scores, ai_pen, rel_pen, is_rejected)
            
            st.write(f"### 📊 Predicted Grade: :blue[{final_sim} / 10]")
            
            # Detailed Breakdown
            with st.expander("See Calculation Details"):
                st.write(f"**Base Quality Score:** {raw_quality} / 10")
                st.write(f"**- AI Penalty:** {ai_pen}")
                st.write(f"**- Relevance Penalty:** {rel_pen}")
                st.write(f"**= Final Score:** {final_sim}")
                if is_rejected:
                    st.error("Result: 0 (REJECTED due to critical AI or Low Relevance)")

# =======================================================
# MODE 2: EXAMINER CONSOLE (With Relevance Penalty)
# =======================================================
elif mode == "Examiner Console":
    st.title("🔒 Examiner Grading Portal")
    if st.sidebar.text_input("Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter Admin Password.")
        st.stop()
        
    tab1, tab2 = st.tabs(["📝 Grading", "⚙️ Data Management"])
    
    with tab2:
        st.header("1. Upload Class List")
        up_csv = st.file_uploader("Upload CSV", type=['csv'])
        if up_csv:
            if save_uploaded_file(up_csv):
                st.toast("List Saved!")
                st.cache_data.clear()
                if 'master_list' in st.session_state: del st.session_state['master_list']
                load_data()
                st.rerun()

        if st.session_state.master_list is not None:
            if st.button("🗑️ DELETE Master List"):
                try:
                    os.remove(MASTER_CSV_FILE)
                    st.session_state.master_list = None
                    st.cache_data.clear()
                    st.rerun()
                except: pass

        st.markdown("---")
        st.header("2. Manage Grades")
        if not st.session_state.gradebook.empty:
            st.dataframe(st.session_state.gradebook)
            opts = st.session_state.gradebook.apply(
                lambda x: f"{x['Roll Number']} - {x['Student Name']} ({x['Final Score']})", axis=1
            ).tolist()
            del_sel = st.selectbox("Select to Delete:", ["Select..."] + opts)
            if del_sel != "Select...":
                if st.button("❌ Delete Entry"):
                    r_del = del_sel.split(" - ")[0]
                    st.session_state.gradebook = st.session_state.gradebook[
                        st.session_state.gradebook['Roll Number'] != r_del
                    ]
                    st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                    st.success("Deleted.")
                    st.rerun()

    with tab1:
        if st.session_state.master_list is None:
            st.error("Upload CSV in Data Management tab first.")
        else:
            stu_opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
            sel_stu = st.selectbox("Select Student:", ["Select..."] + stu_opts)
            
            if sel_stu != "Select...":
                r_num = sel_stu.split(" - ")[0]
                s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                
                st.info(f"**Topic:** {s_row['Assigned Topic']}")
                with st.expander("Show Requirements"):
                    st.write(s_row['Must Cover in Review Section'])
                
                with st.form("grading_form"):
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.subheader("1. Penalties Check")
                        
                        # Relevance
                        st.write("**A. Content Relevance**")
                        f_up = st.file_uploader("Student File", type=['pdf', 'docx'])
                        rel_v = 0.0
                        if f_up:
                            txt = extract_text(f_up)
                            rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                        
                        rel_msg, rel_pen, rel_rej, _ = calculate_relevance_status(rel_v)
                        st.metric("Relevance %", f"{rel_v:.1f}%")
                        if rel_rej: st.error(f"⛔ {rel_msg}")
                        elif rel_pen > 0: st.warning(f"⚠️ {rel_msg}")
                        else: st.success("Safe")

                        # AI
                        st.write("**B. AI Integrity**")
                        ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)
                        ai_msg, ai_pen, ai_rej, _ = calculate_ai_status(ai_inp)
                        if ai_rej: st.error(f"⛔ {ai_msg}")
                        elif ai_pen > 0: st.warning(f"⚠️ {ai_msg}")
                        else: st.success("Safe")

                    with c2:
                        st.subheader("2. Quality Rubric")
                        st.caption("Rate from 0.0 to 2.0 per section.")
                        sc = {}
                        is_rejected = ai_rej or rel_rej
                        
                        for key, label in RUBRIC_CRITERIA.items():
                            sc[key] = st.slider(label, 0.0, 2.0, 1.0, 0.25, disabled=is_rejected, key=f"exam_{key}")
                    
                    remarks = st.text_area("Final Remarks", disabled=is_rejected)
                    
                    if st.form_submit_button("Finalize Grade"):
                        _, fin = calculate_final_grade(sc, ai_pen, rel_pen, is_rejected)
                        
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
                        
                        if not st.session_state.gradebook.empty:
                            st.session_state.gradebook = st.session_state.gradebook[
                                st.session_state.gradebook['Roll Number'] != r_num
                            ]
                        
                        st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_rec])], ignore_index=True)
                        st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                        st.success(f"Saved Grade: {fin}/10")

            st.divider()
            if not st.session_state.gradebook.empty:
                st.dataframe(st.session_state.gradebook)
                st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
