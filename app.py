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

# RUBRIC DEFINITION
RUBRIC_CRITERIA = {
    "scholarly_understanding": "Depth of Scholarly Understanding (0-2)",
    "critical_analysis": "Critical Analysis & Synthesis (0-2)",
    "logical_flow": "Logical Flow & Coherence (0-2)",
    "literature_usage": "Relevance & Currency of Literature (0-2)",
    "writing_style": "Academic Tone & Formatting (0-2)"
}

# *** CORE FIX: UNIFIED STARTING VALUE ***
# Both Student and Examiner start at 1.0 per section (5.0 Total)
STARTING_SCORE = 1.0 

# ==========================================
# 2. SHARED CALCULATION ENGINE
# ==========================================

def calculate_penalties(ai_percent, rel_percent):
    """
    Calculates penalties based on AI and Relevance.
    Returns: (AI_Penalty, Rel_Penalty, Is_Rejected, Status_Messages)
    """
    # A. AI Rules
    if ai_percent > 30.0:
        ai_pen = 10.0 # Zeros the score
        ai_msg = "REJECTED (AI > 30%)"
        ai_rej = True
    elif ai_percent > 20.0:
        ai_pen = 4.0
        ai_msg = "Critical (-4 Marks)"
        ai_rej = False
    elif ai_percent > 10.0:
        ai_pen = 2.0
        ai_msg = "Warning (-2 Marks)"
        ai_rej = False
    else:
        ai_pen = 0.0
        ai_msg = "Safe"
        ai_rej = False

    # B. Relevance Rules
    if rel_percent < 5.0:
        rel_pen = 10.0
        rel_msg = "IRRELEVANT (<5%)"
        rel_rej = True
    elif rel_percent < 15.0:
        rel_pen = 2.0
        rel_msg = "Weak Match (-2 Marks)"
        rel_rej = False
    else:
        rel_pen = 0.0
        rel_msg = "Safe"
        rel_rej = False

    is_rejected = ai_rej or rel_rej
    return ai_pen, ai_msg, rel_pen, rel_msg, is_rejected

def calculate_final_score(rubric_scores_dict, ai_percent, rel_percent):
    """
    The Single Math Function used by both views.
    """
    # 1. Sum Rubric
    raw_quality = sum(rubric_scores_dict.values())
    
    # 2. Get Penalties
    ai_p, ai_m, rel_p, rel_m, is_rej = calculate_penalties(ai_percent, rel_percent)
    
    # 3. Calculate Final
    if is_rej:
        final_score = 0.0
    else:
        total_deduction = ai_p + rel_p
        final_score = max(0.0, raw_quality - total_deduction)
        
    return {
        "raw": raw_quality,
        "final": final_score,
        "ai_pen": ai_p,
        "ai_msg": ai_m,
        "rel_pen": rel_p,
        "rel_msg": rel_m,
        "rejected": is_rej
    }

def check_topic_relevance(doc_text, topic, must_cover):
    if not doc_text: return 0.0
    
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
                df.columns = [c.strip() for c in df.columns]
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
# 3. MAIN APPLICATION INTERFACE
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
        st.error("❌ No Class List Found")

# =========================================================
# MODE 1: STUDENT SIMULATOR (Standardized)
# =========================================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Simulator")
    
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
                st.caption(f"**Must Cover:** {student_data['Must Cover in Review Section']}")
        else:
            with col_info: st.warning("Roll number not found.")

    if student_data is not None:
        st.divider()
        # 1. Check if Official Grade Exists
        graded = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] == roll.strip()]
        
        if not graded.empty:
            last = graded.iloc[-1]
            st.subheader("🎉 Official Result Available")
            c1, c2, c3 = st.columns(3)
            c1.metric("Final Grade", f"{last['Final Score']}/10")
            c2.metric("AI Score", f"{last['AI %']}%")
            c3.metric("Relevance", f"{last['Relevance %']}%")
            st.write(f"**Examiner Remarks:** {last['Examiner Comments']}")
        else:
            # 2. Simulator
            st.subheader("🛠️ Grade Simulator")
            
            c_left, c_right = st.columns(2)
            
            with c_left:
                st.markdown("**1. Integrity Checks**")
                
                # Relevance
                up_file = st.file_uploader("Upload Draft", type=['pdf', 'docx'])
                rel_val = 0.0
                if up_file:
                    txt = extract_text(up_file)
                    rel_val = check_topic_relevance(txt, student_data['Assigned Topic'], student_data['Must Cover in Review Section'])
                st.metric("Relevance %", f"{rel_val:.1f}%")

                # AI
                ai_val = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1)
            
            with c_right:
                st.markdown("**2. Quality Self-Assessment**")
                st.caption(f"Sliders start at {STARTING_SCORE} (Average).")
                
                sim_scores = {}
                # SIMULATOR LOOP
                for key, label in RUBRIC_CRITERIA.items():
                    sim_scores[key] = st.slider(label, 0.0, 2.0, STARTING_SCORE, 0.25, key=f"sim_{key}")

            # LIVE CALCULATION
            res = calculate_final_score(sim_scores, ai_val, rel_val)
            
            st.markdown("---")
            st.write(f"### 📊 Predicted Grade: :blue[{res['final']} / 10]")
            
            # Show Calculation Logic
            with st.expander("Show Math Details"):
                st.write(f"Base Quality: {res['raw']} / 10")
                st.write(f"AI Penalty: -{res['ai_pen']} ({res['ai_msg']})")
                st.write(f"Relevance Penalty: -{res['rel_pen']} ({res['rel_msg']})")

# =========================================================
# MODE 2: EXAMINER CONSOLE (Live Update Fix)
# =========================================================
elif mode == "Examiner Console":
    st.title("🔒 Examiner Grading Portal")
    if st.sidebar.text_input("Password", type="password") != ADMIN_PASSWORD:
        st.warning("Enter Password.")
        st.stop()
    
    tab1, tab2 = st.tabs(["📝 Grading Console", "⚙️ Data Management"])
    
    # --- DATA MANAGEMENT ---
    with tab2:
        st.write("### Master List")
        up_csv = st.file_uploader("Upload 'PhD_Review_Assignment_Distribution.csv'", type=['csv'])
        if up_csv:
            if save_uploaded_file(up_csv):
                st.toast("List Saved!")
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
        st.write("### Gradebook")
        if not st.session_state.gradebook.empty:
            st.dataframe(st.session_state.gradebook)
            if st.button("❌ Delete Last Entry"):
                st.session_state.gradebook = st.session_state.gradebook.iloc[:-1]
                st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                st.success("Deleted last entry.")
                st.rerun()

    # --- GRADING ---
    with tab1:
        if st.session_state.master_list is None:
            st.error("Upload Data first.")
        else:
            # Student Selection
            stu_opts = st.session_state.master_list.apply(lambda x: f"{x['Roll number']} - {x['Student Name']}", axis=1).tolist()
            sel_stu = st.selectbox("Select Student:", ["Select..."] + stu_opts)
            
            if sel_stu != "Select...":
                r_num = sel_stu.split(" - ")[0]
                s_row = st.session_state.master_list[st.session_state.master_list['Roll number'] == r_num].iloc[0]
                
                st.info(f"**Topic:** {s_row['Assigned Topic']}")
                with st.expander("Requirements"):
                    st.write(s_row['Must Cover in Review Section'])
                
                # --- INPUT SECTION (NO FORM - LIVE UPDATES) ---
                c1, c2 = st.columns(2)
                
                with c1:
                    st.subheader("1. Penalties")
                    
                    # Relevance
                    st.write("**Content Match**")
                    f_up = st.file_uploader("Upload File", type=['pdf', 'docx'], key=f"up_{r_num}")
                    rel_v = 0.0
                    if f_up:
                        txt = extract_text(f_up)
                        rel_v = check_topic_relevance(txt, s_row['Assigned Topic'], s_row['Must Cover in Review Section'])
                    
                    # AI
                    st.write("**AI Check**")
                    ai_inp = st.number_input("StealthWriter %", 0.0, 100.0, 5.0, step=0.1, key=f"ai_{r_num}")
                    
                    # Live Status Indicators
                    st.write("---")
                    res_preview = calculate_final_score({}, ai_inp, rel_v) # Temporary calc for flags
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Relevance", f"{rel_v:.1f}%", delta=res_preview['rel_msg'], delta_color="inverse")
                    m2.metric("AI Score", f"{ai_inp}%", delta=res_preview['ai_msg'], delta_color="inverse")

                with c2:
                    st.subheader("2. Quality Rubric")
                    st.caption(f"Sliders start at {STARTING_SCORE}. Move to adjust score.")
                    
                    sc = {}
                    is_rej = res_preview['rejected']
                    
                    # EXAMINER LOOP (Matches Simulator)
                    for key, label in RUBRIC_CRITERIA.items():
                        sc[key] = st.slider(label, 0.0, 2.0, STARTING_SCORE, 0.25, disabled=is_rej, key=f"ex_{r_num}_{key}")
                    
                    # LIVE GRADE DISPLAY
                    final_res = calculate_final_score(sc, ai_inp, rel_v)
                    
                    if is_rej:
                        st.error(f"⛔ REJECTED: 0/10")
                    else:
                        st.metric("Current Grade", f"{final_res['final']} / 10")
                        st.caption(f"(Raw {final_res['raw']} - Penalties {final_res['ai_pen']+final_res['rel_pen']})")

                # --- SUBMISSION SECTION ---
                st.markdown("---")
                rem = st.text_area("Examiner Remarks", disabled=is_rej, key=f"rem_{r_num}")
                
                # Button is outside the "Live" interaction logic
                if st.button("💾 SAVE FINAL GRADE", type="primary"):
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
                    
                    # Remove old entry if exists
                    if not st.session_state.gradebook.empty:
                        st.session_state.gradebook = st.session_state.gradebook[st.session_state.gradebook['Roll Number'] != r_num]
                        
                    st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_rec])], ignore_index=True)
                    st.session_state.gradebook.to_csv(GRADES_CSV_FILE, index=False)
                    st.success(f"✅ Grade Recorded: {final_res['final']}/10")

            st.divider()
            if not st.session_state.gradebook.empty:
                st.dataframe(st.session_state.gradebook)
                st.download_button("Download CSV", st.session_state.gradebook.to_csv(index=False), "grades.csv")
