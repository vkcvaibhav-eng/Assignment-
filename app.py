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
    """
    Extracts raw text from PDF or DOCX files.
    """
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

def check_topic_relevance(doc_text, assigned_topic):
    """
    Calculates semantic similarity between the document text and the assigned topic.
    Returns a percentage score (0-100).
    """
    if not doc_text or not assigned_topic:
        return 0.0
    
    # Clean and prepare data
    clean_doc = doc_text.lower()
    clean_topic = assigned_topic.lower()
    
    documents = [clean_topic, clean_doc]
    
    # Calculate Cosine Similarity
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return similarity[0][0] * 100
    except:
        return 0.0

def calculate_ai_status(ai_percent):
    """
    Determines penalty status based on AI detection percentage.
    """
    if ai_percent <= AI_PENALTY_RULES['threshold_safe']:
        return "Safe (≤10%)", 0.0, False, "success"
    elif ai_percent <= AI_PENALTY_RULES['threshold_warn']:
        return "Warning (10-20%)", AI_PENALTY_RULES['penalty_score'], False, "warning"
    else:
        return "REJECTED (>20%)", 0.0, True, "error"

def calculate_final_grade(scores, penalty, is_rejected):
    """
    Calculates the final grade based on rubric scores and penalties.
    """
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
        "Student ID", "Subtopic", "Relevance %", "AI %", "Raw Score", "Penalty", "Final Score", "Examiner Comments", "Timestamp"
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
    st.info("Upload a CSV file with columns: `Student ID` and `Assigned Topic`")
    
    uploaded_master = st.file_uploader("Upload Assignment List (CSV)", type=['csv'])
    
    if uploaded_master:
        try:
            st.session_state.master_list = pd.read_csv(uploaded_master)
            # Ensure Student ID is treated as a string (to match inputs)
            st.session_state.master_list['Student ID'] = st.session_state.master_list['Student ID'].astype(str)
            st.success(f"✅ Loaded {len(st.session_state.master_list)} student assignments.")
        except Exception as e:
            st.error(f"Error loading CSV: {e}")

# ==========================================
# MODE 1: STUDENT SIMULATOR
# ==========================================
if mode == "Student Simulator":
    st.title("🎓 Student Pre-Submission Simulator")
    st.markdown("""
    Use this tool to verify your subtopic matches your assignment and to estimate your grade based on AI penalties.
    """)
    st.divider()

    # Step 1: ID Check
    col_input, col_status = st.columns([1, 2])
    student_topic = None
    
    with col_input:
        st_id_input = st.text_input("Enter your Student ID:", placeholder="e.g., 2024PHD01")
    
    with col_status:
        if st.session_state.master_list is not None and st_id_input:
            record = st.session_state.master_list[st.session_state.master_list['Student ID'] == st_id_input.strip()]
            if not record.empty:
                student_topic = record.iloc[0]['Assigned Topic']
                st.info(f"**Your Assigned Subtopic:** {student_topic}")
            else:
                st.warning("ID not found in the uploaded Master List.")
        elif st.session_state.master_list is None:
            st.warning("⚠️ Examiner has not uploaded the Master Assignment List yet.")

    # Step 2: Relevance Check
    if student_topic:
        st.subheader("1. Content Relevance Check")
        student_file = st.file_uploader("Upload Draft (PDF/DOCX)", type=['pdf', 'docx'])
        
        if student_file:
            with st.spinner("Analyzing document content..."):
                text_content = extract_text(student_file)
                rel_score = check_topic_relevance(text_content, student_topic)
                
            if rel_score > 10.0:
                st.success(f"✅ **Good Match:** Your content is {rel_score:.1f}% semantically relevant to '{student_topic}'.")
            else:
                st.error(f"⚠️ **Low Relevance ({rel_score:.1f}%):** The system detects low similarity to '{student_topic}'. Ensure you are using specific keywords related to your subtopic.")

        # Step 3: Grade Prediction
        st.subheader("2. Grade Predictor")
        st.caption("Self-assess your work to see how penalties affect your final mark.")
        
        c1, c2 = st.columns(2)
        with c1:
            sim_ai = st.number_input("Enter your StealthWriter AI Score:", 0.0, 100.0, 0.0, step=0.5)
            status_msg, penalty, rejected, color = calculate_ai_status(sim_ai)
            
            if rejected:
                st.error(f"❌ Status: {status_msg}")
            elif penalty > 0:
                st.warning(f"⚠️ Status: {status_msg}")
            else:
                st.success(f"✅ Status: {status_msg}")

        with c2:
            st.markdown("**Rubric Self-Estimation**")
            sim_scores = {}
            sim_scores['scholarly'] = st.slider("Scholarly Understanding", 0.0, 2.0, 1.5, 0.25)
            sim_scores['writing'] = st.slider("Writing Style", 0.0, 2.0, 1.5, 0.25)
            # Simplified sliders for simulation
            raw_sim = sim_scores['scholarly'] + sim_scores['writing'] + 6.0 # Assume average for others
            
        # Prediction Result
        _, final_sim = calculate_final_grade({'total': raw_sim}, penalty, rejected)
        
        st.metric("Estimated Maximum Potential Score", f"{final_sim} / 10")
        if rejected:
            st.markdown("🚨 **Action:** You must rewrite your paper to lower AI content below 20%.")


# ==========================================
# MODE 2: EXAMINER GRADING
# ==========================================
elif mode == "Examiner Grading":
    st.title("🔒 Examiner Evaluation Portal")
    
    # Authentication
    password_input = st.sidebar.text_input("Enter Admin Password", type="password")
    
    if password_input != ADMIN_PASSWORD:
        st.warning("⛔ Please enter the correct password in the sidebar to unlock grading tools.")
        st.stop()

    if st.session_state.master_list is None:
        st.error("Please upload the **Assignments.csv** in the sidebar to begin grading.")
        st.stop()

    # Grading Interface
    st.subheader("Assessment Console")
    
    col_id, col_ai = st.columns([1, 1])
    
    with col_id:
        exam_student_id = st.text_input("Enter Student ID to Grade:")
    
    if exam_student_id:
        # Fetch Data
        student_record = st.session_state.master_list[st.session_state.master_list['Student ID'] == exam_student_id.strip()]
        
        if not student_record.empty:
            assigned_topic = student_record.iloc[0]['Assigned Topic']
            st.markdown(f"**Assigned Subtopic:** `{assigned_topic}`")
            
            # File Upload & Analysis
            exam_file = st.file_uploader("Upload Student Submission", type=['pdf', 'docx'], key="exam_upload")
            
            relevance_percentage = 0.0
            
            if exam_file:
                # 1. Automatic Topic Check
                doc_text = extract_text(exam_file)
                relevance_percentage = check_topic_relevance(doc_text, assigned_topic)
                
                # Display Analysis Dashboard
                st.write("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Content Relevance", f"{relevance_percentage:.1f}%", delta_color="normal" if relevance_percentage > 10 else "inverse")
                
                with col_ai:
                    ai_input = st.number_input("StealthWriter AI %", 0.0, 100.0, step=0.1)
                
                status_msg, penalty, rejected, color = calculate_ai_status(ai_input)
                m2.metric("AI Status", status_msg)
                m3.metric("Penalty Applied", f"-{penalty}")

                # 2. Rubric Entry
                st.write("#### 📝 Rubric Evaluation")
                
                with st.form("official_grading_form"):
                    disabled_state = rejected  # Lock form if rejected
                    
                    c_rubric1, c_rubric2 = st.columns(2)
                    exam_scores = {}
                    
                    # Left Column Rubrics
                    with c_rubric1:
                        exam_scores['scholarly_understanding'] = st.slider(RUBRIC_CRITERIA['scholarly_understanding'], 0.0, 2.0, 1.0, 0.25, disabled=disabled_state)
                        exam_scores['critical_analysis'] = st.slider(RUBRIC_CRITERIA['critical_analysis'], 0.0, 2.0, 1.0, 0.25, disabled=disabled_state)
                        exam_scores['logical_flow'] = st.slider(RUBRIC_CRITERIA['logical_flow'], 0.0, 2.0, 1.0, 0.25, disabled=disabled_state)
                    
                    # Right Column Rubrics
                    with c_rubric2:
                        exam_scores['literature_usage'] = st.slider(RUBRIC_CRITERIA['literature_usage'], 0.0, 2.0, 1.0, 0.25, disabled=disabled_state)
                        exam_scores['writing_style'] = st.slider(RUBRIC_CRITERIA['writing_style'], 0.0, 2.0, 1.0, 0.25, disabled=disabled_state)

                    comments = st.text_area("Examiner Feedback / Remarks", disabled=disabled_state)
                    
                    submitted = st.form_submit_button("💾 Save Grade to Record")
                    
                    if submitted:
                        raw_tot, final_tot = calculate_final_grade(exam_scores, penalty, rejected)
                        
                        # Add to DataFrame
                        new_entry = {
                            "Student ID": exam_student_id,
                            "Subtopic": assigned_topic,
                            "Relevance %": round(relevance_percentage, 1),
                            "AI %": ai_input,
                            "Raw Score": raw_tot,
                            "Penalty": penalty,
                            "Final Score": final_tot,
                            "Examiner Comments": comments,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        st.session_state.gradebook = pd.concat([st.session_state.gradebook, pd.DataFrame([new_entry])], ignore_index=True)
                        st.success(f"✅ Grade Recorded! Final Score: {final_tot}/10")

        else:
            st.error("Student ID not found in Master List.")

    # Display & Export Records
    st.divider()
    st.subheader("📚 Assessment Records (Current Session)")
    if not st.session_state.gradebook.empty:
        st.dataframe(st.session_state.gradebook, use_container_width=True)
        
        # CSV Download
        csv_data = st.session_state.gradebook.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Gradebook CSV",
            data=csv_data,
            file_name=f"PhD_Assessment_Export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
    else:
        st.caption("No grades recorded yet.")