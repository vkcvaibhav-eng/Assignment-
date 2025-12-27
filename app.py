import streamlit as st
import pandas as pd
import os
from datetime import datetime
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. CENTRAL CONFIGURATION
# ==========================================
MASTER_CSV_FILE = "PhD_Review_Assignment_Distribution.csv"
GRADES_CSV_FILE = "grades.csv"
ADMIN_PASSWORD = "phd_admin_2025"
STARTING_SCORE = 1.0

RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def calculate_penalties(ai_percent, rel_percent):
    """Calculates penalty values."""
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
    # Load Master List
    if 'master_list' not in st.session_state:
        if os.path.exists(MASTER_CSV_FILE):
            try:
                df = pd.read_csv(MASTER_CSV_FILE)
                # Cleanup Headers: Remove spaces, make consistent
                df.columns = [c.strip() for c in df.columns]
                # Force Roll number to String
                df['Roll number'] = df['Roll number'].astype(str).str.strip()
                st.session_state.master_list = df
            except: st.session_state.master_list = None
        else: st.session_state.master_list = None

    # Load Gradebook
    if 'gradebook' not in st.session_state:
        if os.path.exists(GRADES_CSV_FILE):
            try:
                gb = pd.read_csv(GRADES_CSV_FILE)
                gb['Roll Number'] = gb['Roll Number'].astype(str).str.strip()
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

# ==========================================
# 3. MAIN INTERFACE
# ==========================================
st.set_page_config(page_title="Ph.D. Evaluation System", layout="wide", page_icon="🎓")
load_data()

with st.sidebar:
    st.title("🎓 Portal Access")
    mode = st.radio("Select Interface:", ["Student Simulator", "Examiner Console"])
    st.divider()
    if st.session_state.master_list is not None:
        st.success(f"✅ Class List Loaded ({len(st.session_state.master_list)} Students)")
    else:
        st.error("❌ No Class List Found. Please upload CSV in Examiner Console.")

# ==========================================
# MODE 1: STUDENT SIMULATOR
# ==========================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Simulator")
    
    col_id, col_info = st.columns([1, 2])
    with col_id:
        roll_input = st.text_input("Enter Roll Number:", placeholder="e.g. 1")
    
    student_data = None
    
    # 1. Try to find student
    if roll_input and st.session_state.master_list is not None:
        # Strict String Matching
        roll_str = str(roll_input).strip()
        rec = st.session_state.master_list[st.session_state.master_list['Roll number'] == roll_str]
        
        if not rec.empty:
            student_data = rec.iloc[0]
            with col_info:
                st.info(f"**Topic:** {student_data['Assigned Topic']}")
                st.caption(f"**Must Cover:** {student_data['Must Cover in Review Section']}")
        else:
            with col_info: st.error("❌ Roll Number not found.")

    # 2. Display Logic
    if student_data is not None:
        st.divider()
        # Check Gradebook using strict string match
        graded = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == str(roll_input).strip()]
        
        if not graded.empty:
            # === SHOW OFFICIAL RESULT ===
            last = graded.iloc[-1]
            st.subheader("🎉 Official Assessment Result")
            m1, m2, m3 = st.columns(3)
            m1.metric("Final Grade", f"{last['Final Score']}/10")
            m2.metric("AI Score", f"{last['AI %']}%")
            m3.metric("Relevance", f"{last['Relevance %']}%")
            st.write(f"**Examiner Remarks:** {last['Examiner Comments']}")
        else:
            # === SHOW SIMULATOR ===
            st.subheader("🛠️ Grade Simulator")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**1. Integrity Checks**")
                up_file = st.file_uploader("Upload Draft", type=['pdf', 'docx'])
                rel_val = 0.0
                if up_file:
                    txt = extract_text(up_file)
                    rel_val = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                st.metric("Relevance %", f"{rel_val:.1f}%")
                
                ai_val = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)

            with c2:
                st.markdown("**2. Quality Self-Assessment**")
                sim_scores = {}
                for key, label in RUBRIC_CRITERIA.items():
                    sim_scores[key] = st.slider(label, 0.0, 2.0, STARTING_SCORE, 0.25, key=f"sim_{key}")

            # Calculate
            res = calculate_final_score(sim_scores, ai_val, rel_val)
            st.markdown("---")
            st.write(f"### 📊 Predicted Grade: :blue[{res['final']} / 10]")
            
            with st.expander("Show Calculation Details"):
                st.write(f"Base Quality: {res['raw']} / 10")
                st.write(f"AI Penalty: -{res['ai_pen']} ({res['ai_msg']})")
                st.write(f"Relevance Penalty: -{res['rel_pen']} ({res['rel_msg']})")


# ==========================================
# MODE 2: EXAMINER CONSOLE
# ==========================================
elif mode == "Examiner Console":
    st.title("🔒 Examiner Grading Portal")
    if st.sidebar.text_input("Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter Password.")
        st.stop()
    
    tab1, tab2 = st.tabs(["📝 Grading Console", "⚙️ Data Management"])

    # --- TAB 2: DATA ---
    with tab2:
        st.write("### 1. Master Assignment List")
        up_csv = st.file_uploader("Upload 'PhD_Review_Assignment_Distribution.csv'", type=['csv'])
        if up_csv:
            if save_uploaded_file(up_csv):
                st.toast("File Saved!")
                st.cache_data.clear()
                if 'master_list' in st.session_state: del st.session_state['master_list']
                load_data()
                st.rerun()
        
        if st.session_state.master_list is not None:
             if st.button("🗑️ DELETE Master List"):
                try: 
                    os.remove(MASTER_CSV_FILE)
                    st.session_state.master_list = None
                    st.rerun()
                except: pass

        st.markdown("---")
        st.write("### 2. Gradebook")
        if not st.session_state.gradebook.empty:
            st.dataframe(st.session_state.gradebook)
            # Delete Logic
            opts = st.session_state.gradebook.apply(
                lambda x: f"{x['Roll Number']} - {x['Student Name']} ({x['Final Score']})", axis=1
            ).tolist()
            d_sel = st.selectbox("Select Entry to Delete:", ["Select..."] + opts)
            if d_sel != "Select..." and st.button("❌ Delete Selected Entry"):
                r_del = d_sel.split(" - ")[0]
                st.session_state.gradebook = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] != r_del]
                st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                st.success("Deleted.")
                st.rerun()

    # --- TAB 1: GRADING ---
    with tab1:
        if st.session_state.master_list is None:
            st.error("⚠️ Please upload the CSV in 'Data Management' first.")
        else:
            # Dropdown List
            stu_opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
            sel_stu = st.selectbox("Select Student:", ["Select..."] + stu_opts)
            
            if sel_stu != "Select...":
                r_num = sel_stu.split(" - ")[0]
                s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                
                st.info(f"**Topic:** {s_row['Assigned Topic']}")
                with st.expander("Requirements"):
                    st.write(s_row['Must Cover in Review Section'])
                
                # *** KEY FIX: CHECK FOR EXISTING GRADE ***
                existing_grade = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == r_num]
                
                # Default Values (If no previous grade, use safe defaults)
                def_ai = 5.0
                def_rel = 0.0
                def_rem = ""
                # We can't easily restore individual sliders unless we saved them individually. 
                # Currently we only save Final Score. So we reset sliders to STARTING_SCORE.
                
                if not existing_grade.empty:
                    last_rec = existing_grade.iloc[-1]
                    def_ai = float(last_rec['AI %'])
                    def_rel = float(last_rec['Relevance %'])
                    def_rem = str(last_rec['Examiner Comments'])
                    st.success("✅ Loading previous assessment data for this student.")

                # --- GRADING INTERFACE ---
                c1, c2 = st.columns(2)
                
                with c1:
                    st.subheader("1. Penalties")
                    # Relevance
                    st.write("**Content Match**")
                    f_up = st.file_uploader("Upload File", type=['pdf', 'docx'], key=f"up_{r_num}")
                    rel_v = def_rel # Use default or calculated
                    if f_up:
                        txt = extract_text(f_up)
                        rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                    
                    st.metric("Relevance %", f"{rel_v:.1f}%")

                    # AI
                    st.write("**AI Check**")
                    ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, def_ai, step=0.1, key=f"ai_{r_num}")
                    
                    # Live Calc
                    res_preview = calculate_final_score({}, ai_inp, rel_v)
                    if res_preview['rejected']:
                        st.error(f"⛔ REJECTED: {res_preview['ai_msg']} | {res_preview['rel_msg']}")
                    else:
                        if res_preview['ai_pen'] > 0: st.warning(f"AI Penalty: {res_preview['ai_msg']}")
                        if res_preview['rel_pen'] > 0: st.warning(f"Rel Penalty: {res_preview['rel_msg']}")

                with c2:
                    st.subheader("2. Rubric")
                    st.caption(f"Sliders start at {STARTING_SCORE} (Average).")
                    
                    sc = {}
                    is_rej = res_preview['rejected']
                    
                    for key, label in RUBRIC_CRITERIA.items():
                        sc[key] = st.slider(label, 0.0, 2.0, STARTING_SCORE, 0.25, disabled=is_rej, key=f"ex_{r_num}_{key}")
                    
                    final_res = calculate_final_score(sc, ai_inp, rel_v)
                    
                    if not is_rej:
                        st.metric("Current Grade", f"{final_res['final']} / 10")
                
                st.markdown("---")
                rem = st.text_area("Examiner Remarks", value=def_rem, disabled=is_rej, key=f"rem_{r_num}")
                
                if st.button("💾 SAVE GRADE", type="primary"):
                    new_rec = {
                        "Roll Number": r_num,
                        "Student Name": s_row['Student Name'],
                        "Subtopic": s_row['Assigned Topic'],
                        "Relevance %": round(rel_v, 1),
                        "AI %": ai_inp,
                        "Final Score": final_res['final'],
                        "Examiner Comments": rem,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    # Update Gradebook (Remove old, add new)
                    if not st.session_state.gradebook.empty:
                        st.session_state.gradebook = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] != r_num]
                        
                    st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_rec])], ignore_index=True)
                    st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                    st.success(f"✅ Saved! Final Score: {final_res['final']}/10")
            
            st.divider()
            if not st.session_state.gradebook.empty:
                st.write("### Recent Grades")
                st.dataframe(st.session_state.gradebook)
