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
# CORE LOGIC (SHARED)
# ==========================================
def calculate_ai_status(ai_percent):
    """
    Unified AI Penalty Logic
    """
    if ai_percent <= 10.0:
        return "Safe (≤10%)", 0.0, False, "success"
    elif ai_percent <= 20.0:
        return "Warning (-2 Marks)", 2.0, False, "warning"
    elif ai_percent <= 30.0:
        return "Critical (-4 Marks)", 4.0, False, "error"
    else:
        return "REJECTED (>30%)", 0.0, True, "error"

def calculate_relevance_status(rel_percent):
    """
    Unified Relevance Penalty Logic
    """
    if rel_percent >= 15.0:
        return "Safe Match (≥15%)", 0.0, False, "success"
    elif rel_percent >= 5.0:
        return "Weak Match (-2 Marks)", 2.0, False, "warning"
    else:
        return "Irrelevant (<5%)", 0.0, True, "error"

def calculate_final_grade(scores, ai_penalty, rel_penalty, is_rejected):
    """
    Final Score = (Sum of Rubric) - Penalties
    """
    raw_quality = sum(scores.values())  # Max 10.0
    
    if is_rejected:
        final_score = 0.0
    else:
        total_pen = ai_penalty + rel_penalty
        final_score = max(0.0, raw_quality - total_pen)
        
    return raw_quality, final_score

def check_topic_relevance(doc_text, topic, must_cover):
    if not doc_text: return 0.0
    
    # Ensure inputs are strings
    t = str(topic) if pd.notna(topic) else ""
    m = str(must_cover) if pd.notna(must_cover) else ""
    
    ref_text = f"{t} {m}".lower()
    clean_doc = doc_text.lower()
    
    try:
        tfidf = TfidfVectorizer(stop_words='english')
        matrix = tfidf.fit_transform([ref_text, clean_doc])
        return cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100
    except:
        return 0.0

def load_data():
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                # Normalize columns
                df.columns = [c.strip() for c in df.columns]
                # Clean Data
                df['Roll number'] = df['Roll number'].astype(str)
                df.fillna("", inplace=True) 
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
# MAIN APP
# ==========================================
st.set_page_config(page_title="Ph.D. Evaluation", layout="wide", page_icon="🎓")
load_data()

with st.sidebar:
    st.title("🎓 Portal Access")
    mode = st.radio("Select Mode:", ["Student Simulator", "Examiner Console"])
    st.divider()
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Loaded ({len(st.session_state.master_list)} Students)")
    else:
        st.error("❌ No Class List Found")

# =========================================================
# MODE 1: STUDENT SIMULATOR (Self Check)
# =========================================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Simulator")
    st.markdown("Use this tool to verify your content relevance and estimate your grade.")

    col_id, col_info = st.columns([1, 2])
    with col_id:
        roll = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    if roll and st.session_state.master_list is not None:
        rec = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll.strip()]
        if not rec.empty:
            student_data = rec.iloc[0]
            with col_info:
                st.info(f"**Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Requirements:** {student_data['Must Cover in Review Section']}")
        else:
            with col_info: st.warning("Roll number not found.")

    if student_data is not None:
        st.divider()
        # Check Gradebook
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
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.write("**1. Penalties Check**")
                # Relevance
                st.caption("Upload your draft to check keywords match.")
                up_file = st.file_uploader("Upload Draft", type=['pdf', 'docx'])
                rel_val = 0.0
                if up_file:
                    txt = extract_text(up_file)
                    rel_val = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                
                rel_msg, rel_pen, rel_rej, _ = calculate_relevance_status(rel_val)
                st.metric("Relevance", f"{rel_val:.1f}%")
                if rel_rej: st.error(rel_msg)
                elif rel_pen > 0: st.warning(rel_msg)
                else: st.success(rel_msg)

                st.write("---")
                # AI
                st.caption("Enter estimated AI score.")
                ai_val = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)
                ai_msg, ai_pen, ai_rej, _ = calculate_ai_status(ai_val)
                if ai_rej: st.error(ai_msg)
                elif ai_pen > 0: st.warning(ai_msg)
                else: st.success(ai_msg)

            with c2:
                st.write("**2. Quality Self-Assessment**")
                st.caption("Rate your writing quality (0.0 - 2.0 per section).")
                
                sim_scores = {}
                for key, label in RUBRIC_CRITERIA.items():
                    sim_scores[key] = st.slider(label, 0.0, 2.0, 1.5, 0.25, key=f"sim_{key}")
                
                raw_q = sum(sim_scores.values())
            
            # Result
            st.markdown("---")
            is_rej = rel_rej or ai_rej
            _, fin_sim = calculate_final_grade(sim_scores, ai_pen, rel_pen, is_rej)
            
            st.write(f"### 📊 Predicted Grade: :blue[{fin_sim} / 10]")
            st.caption(f"Math: (Quality {raw_q}) - (AI {ai_pen}) - (Relevance {rel_pen}) = {fin_sim}")

# =========================================================
# MODE 2: EXAMINER CONSOLE (Correction applied)
# =========================================================
elif mode == "Examiner Console":
    st.title("🔒 Examiner Grading Portal")
    if st.sidebar.text_input("Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter Password.")
        st.stop()
    
    tab1, tab2 = st.tabs(["📝 Grading", "⚙️ Data Management"])
    
    # --- DATA MANAGEMENT ---
    with tab2:
        st.write("**Upload Class List**")
        up_csv = st.file_uploader("Upload CSV", type=['csv'])
        if up_csv:
            if save_uploaded_file(up_csv):
                st.toast("Saved!")
                st.cache_data.clear()
                if 'master_list' in st.session_state: del st.session_state['master_list']
                load_data()
                st.rerun()
        
        if st.session_state.master_list is not None:
             if st.button("🗑️ DELETE List"):
                try: 
                    os.remove(MASTER_CSV_FILE)
                    st.session_state.master_list = None
                    st.rerun()
                except: pass

        st.markdown("---")
        st.write("**Manage Grades**")
        if not st.session_state.gradebook.empty:
            st.dataframe(st.session_state.gradebook)
            opts = st.session_state.gradebook.apply(
                lambda x: f"{x['Roll Number']} - {x['Student Name']} ({x['Final Score']})", axis=1
            ).tolist()
            d_sel = st.selectbox("Delete:", ["Select..."] + opts)
            if d_sel != "Select..." and st.button("❌ Delete Entry"):
                r_del = d_sel.split(" - ")[0]
                st.session_state.gradebook = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] != r_del]
                st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                st.success("Deleted")
                st.rerun()

    # --- GRADING ---
    with tab1:
        if st.session_state.master_list is None:
            st.error("Upload Data first.")
        else:
            # Dropdown
            stu_opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
            sel = st.selectbox("Select Student:", ["Select..."] + stu_opts)
            
            if sel != "Select...":
                r_num = sel.split(" - ")[0]
                s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                
                st.info(f"**Topic:** {s_row['Assigned Topic']}")
                with st.expander("Requirements"):
                    st.write(s_row['Must Cover in Review Section'])
                
                # Grading Form
                with st.form("exam_form"):
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.subheader("1. Penalties")
                        
                        # Relevance
                        st.write("**Content Match**")
                        f_up = st.file_uploader("Upload Submission", type=['pdf', 'docx'], key=f"up_{r_num}")
                        rel_v = 0.0
                        if f_up:
                            txt = extract_text(f_up)
                            rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                        
                        rel_msg, rel_pen, rel_rej, _ = calculate_relevance_status(rel_v)
                        st.metric("Relevance %", f"{rel_v:.1f}%")
                        if rel_rej: st.error(rel_msg)
                        elif rel_pen > 0: st.warning(rel_msg)
                        else: st.success(rel_msg)
                        
                        # AI
                        st.write("**AI Check**")
                        ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1, key=f"ai_{r_num}")
                        ai_msg, ai_pen, ai_rej, _ = calculate_ai_status(ai_inp)
                        if ai_rej: st.error(ai_msg)
                        elif ai_pen > 0: st.warning(ai_msg)
                        else: st.success(ai_msg)

                    with c2:
                        st.subheader("2. Quality Rubric")
                        st.info("ℹ️ Sliders default to 1.0 (Average). Adjust up for good work.")
                        
                        sc = {}
                        is_rej = ai_rej or rel_rej
                        
                        # Unique Keys per Student to prevent "ghosting"
                        for key, label in RUBRIC_CRITERIA.items():
                            sc[key] = st.slider(label, 0.0, 2.0, 1.0, 0.25, disabled=is_rej, key=f"ex_{r_num}_{key}")
                        
                        raw_q = sum(sc.values())
                        st.write(f"**Quality Score:** {raw_q} / 10")

                    rem = st.text_area("Remarks", disabled=is_rej, key=f"rem_{r_num}")
                    
                    if st.form_submit_button("Finalize Grade"):
                        _, fin = calculate_final_grade(sc, ai_pen, rel_pen, is_rej)
                        
                        new_rec = {
                            "Roll Number": r_num,
                            "Student Name": s_row['Student Name'],
                            "Subtopic": s_row['Assigned Topic'],
                            "Relevance %": round(rel_v, 1),
                            "AI %": ai_inp,
                            "Final Score": fin,
                            "Examiner Comments": rem,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        
                        # Remove old
                        if not st.session_state.gradebook.empty:
                            st.session_state.gradebook = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] != r_num]
                            
                        st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_rec])], ignore_index=True)
                        st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                        st.success(f"✅ Grade Saved: {fin}/10")

            st.divider()
            if not st.session_state.gradebook.empty:
                st.dataframe(st.session_state.gradebook)
                st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
