import streamlit as st

# 1. Set page to wide mode to accommodate two A4 pages side-by-side
st.set_page_config(layout="wide", page_title="Dual A4 App")

# 2. Define the CSS to create the "A4 Paper" look
# We enforce white background, black text, and A4 dimensions (210mm x 297mm)
st.markdown("""
    <style>
    /* Main background color adjustment */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* The A4 Page Container */
    .a4-page {
        background-color: white;
        color: black;
        width: 210mm;       /* Standard A4 Width */
        height: 297mm;      /* Standard A4 Height */
        padding: 20mm;      /* Standard print margins */
        margin: auto;       /* Center in the column */
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); /* Drop shadow for depth */
        font-family: Arial, sans-serif;
        overflow: hidden;   /* Prevents content from spilling out of the page */
    }

    /* Helper to remove default Streamlit top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DEFINE YOUR CONTENT HERE
# ---------------------------------------------------------
# Edit this HTML block. It will appear EXACTLY the same on both pages.
# Do not change the layout logic below, just edit the content inside this string.

page_content = """
    <div style="border-bottom: 2px solid black; margin-bottom: 20px;">
        <h1 style="margin: 0;">DOCUMENT TITLE</h1>
        <p style="color: gray;">Subtitle or Date</p>
    </div>

    <h3>Section Header</h3>
    <p>
        This is the content area. Because you requested "no add from your side," 
        I have left this generic. You can paste your text, tables, or image links here.
    </p>
    
    <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    </p>

    <br>
    
    <div style="background-color: #eee; padding: 10px; border: 1px solid #ccc;">
        <strong>Boxed Element</strong><br>
        Details: _______________________
    </div>

    <div style="position: absolute; bottom: 20mm; width: 100%;">
        <hr>
        <p style="text-align: center; font-size: 12px;">Footer Content / Page Number</p>
    </div>
"""

# ---------------------------------------------------------
# 4. RENDER THE LAYOUT
# ---------------------------------------------------------

# Create two columns for side-by-side layout
col1, col2 = st.columns(2)

# Column 1: Page 1
with col1:
    st.markdown(f'<div class="a4-page">{page_content}</div>', unsafe_allow_html=True)

# Column 2: Page 2 (Identical Copy)
with col2:
    st.markdown(f'<div class="a4-page">{page_content}</div>', unsafe_allow_html=True)

