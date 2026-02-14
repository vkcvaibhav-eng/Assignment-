import streamlit as st

# 1. Setup the page layout
st.set_page_config(layout="wide", page_title="Navsari Uni Bill - Official Layout")

# 2. CSS for Exact A4 Paper Layout and Gujarati Font Support
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700&display=swap');

    .stApp {
        background-color: #555; /* Dark background to make pages stand out */
    }
    
    .a4-page {
        background-color: white;
        color: black;
        width: 210mm;
        min-height: 297mm;
        padding: 15mm 15mm;
        margin: 10px auto;
        font-family: 'Noto Sans Gujarati', sans-serif;
        font-size: 13px; /* Slightly larger for readability */
        line-height: 1.3;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        position: relative;
    }

    /* Headings */
    .header-main { text-align: center; font-weight: 700; font-size: 18px; margin-top: 5px; }
    .header-sub { text-align: center; font-weight: 600; font-size: 16px; margin-bottom: 5px; }
    .bill-title { text-align: center; font-weight: 700; font-size: 14px; text-decoration: underline; margin: 10px 0; }

    /* Grid Layouts for Inputs */
    .top-info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        margin-bottom: 10px;
        font-size: 12px;
    }
    
    .voucher-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-top: 15px;
        border-bottom: 1px solid black;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }

    /* Input Lines */
    .input-line {
        border-bottom: 1px dotted black;
        display: inline-block;
        min-width: 50px;
        margin-left: 5px;
    }
    
    /* Tables */
    table.budget-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }
    table.budget-table th, table.budget-table td { border: 1px solid black; padding: 6px; }
    table.budget-table th { background-color: #f0f0f0; text-align: center; }
    
    /* Footer & Signatures */
    .signature-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-top: 40px;
    }
    
    .box-border { border: 1px solid black; padding: 10px; margin-top: 10px; }
    
    /* Page 2 Calculation Grid */
    .calc-grid {
        display: grid;
        grid-template-columns: 1fr auto 1fr auto 1fr;
        text-align: center;
        align-items: center;
        border: 1px solid black;
        padding: 10px;
        margin-top: 10px;
        background-color: #fafafa;
    }
    
    .bold { font-weight: 700; }
    
    /* Print handling */
    @media print {
        .stApp { background-color: white; }
        .a4-page { margin: 0; box-shadow: none; page-break-after: always; }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 1 CONTENT
# ---------------------------------------------------------
page1_html = """
<div class="top-info-grid">
    <div>હિસાબી પત્રક નંબર: <span class="input-line" style="width:80px;"></span></div>
    <div style="text-align: center;">બીલ નંબર: <span class="input-line" style="width:80px;"></span></div>
    <div style="text-align: right;">તારીખ: <span class="input-line" style="width:80px;"></span></div>
</div>

<div class="header-main">નવસારી કૃષિ વિશ્વવિધાલય</div>
<div class="header-sub">મુસાફરી ભથ્થા બીલ</div>

<div class="voucher-grid">
    <div>
        વાઉચર નં.: <span class="input-line" style="width:120px;"></span><br>
        તારીખ: <span class="input-line" style="width:138px;"></span>
    </div>
    <div style="text-align: right;">
        યુનિટ નંબર: <span class="input-line" style="width:100px;"></span><br>
        કોડ નંબર: <span class="input-line" style="width:108px;"></span>
    </div>
</div>

<div style="margin-top: 10px;">
    <strong>આચાર્ય અને ડીનશ્રી, નં. મ. કૃષિ મહાવિદ્યાલય, નવસારી ની કચેરીનું માહે: ઓક્ટોમ્બર - ૨૦૨૫ નું</strong>
</div>

<div class="bill-title">મુસાફરી ભથ્થા બિલ</div>

<div>
    યુનિટ/સબયુનિટ : <strong>આચાર્ય અને ડીનશ્રી, ન. મ. કૃષિ મહાવિદ્યાલય, નકૃયું, નવસારી</strong>
</div>

<div style="margin-top: 15px; text-align: justify;">
    આથી રૂ।. <strong style="font-size:14px; text-decoration: underline;">12161</strong> નો દાવો મંજુર કરી ગ્રાહય રાખવામાં આવે છે.
</div>

<div style="margin-top: 10px;">
    ખર્ચ માટેનું બજેટ સદર : <span class="input-line" style="width: 250px;"></span><br>
    યોજનાનું નામ : <span class="input-line" style="width: 295px;"></span>
</div>

<div class="box-border" style="background-color: #fff;">
    રૂા. <strong>12161</strong> ( અંકે રૂપિયા <strong>બાર હજાર એકસો એકસઠ પુરા</strong> પૈસા )
    <br><br>
    આ બીલમાં જણાવેલ રૂા <span class="input-line" style="width:80px;"></span> મંજુર કરવામાં આવે છે અને તે રોકડા / ચેક નં. <span class="input-line" style="width:80px;"></span> થી ચુકવવામાં આવે છે.
</div>

<div class="signature-row">
    <div style="text-align: left;">
        નવસારી<br>
        તારીખ : <span class="input-line" style="width:100px;"></span>
    </div>
    <div style="text-align: center;">
        <span class="input-line" style="width:150px;"></span><br>
        બીલ મંજુર કરનાર અધિકારીની<br>
        સહી અને હોદ્દો
    </div>
</div>

<table class="budget-table">
    <colgroup>
        <col style="width: 70%;">
        <col style="width: 15%;">
        <col style="width: 15%;">
    </colgroup>
    <thead>
        <tr>
            <th>વિગત</th>
            <th>રૂ.</th>
            <th>પૈસા</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>(૧) સને ૨૦૨૪-૨૫ માટે બજેટમાં મંજુર થયેલ રકમ</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>(૨) આ બીલ સાથે થયેલ કુલ ખર્ચ</td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>(૩) ખર્ચ માટે બાકી રહેતી રકમ</td>
            <td></td>
            <td></td>
        </tr>
    </tbody>
</table>

<div style="margin-top: 20px; border-top: 1px solid black; padding-top: 10px;">
    <div style="float: right; text-align: center; margin-left: 20px;">
         <span class="input-line" style="width:150px;"></span><br>
         નિયંત્રણ અધિકારીની સહી
    </div>
    <div style="padding-top: 10px;">
        રૂપ ( <strong>12161</strong> ) અંકે રૂપિયા : બાર હજાર એકસો એકસઠ પુરા મંજુર કર્યા.
    </div>
</div>
"""

# ---------------------------------------------------------
# PAGE 2 CONTENT
# ---------------------------------------------------------
page2_html = """
<div style="font-size: 11px;">
    <strong>નોંધ :-</strong>
    <ol style="margin-top: 5px; padding-left: 20px; margin-bottom: 10px;">
        <li>કોલમ નં. ૭ માં મુસાફરી પ્રકાર રેલ્વે/એસ.ટી./હવાઈ/સ્ટીમર/ભાડાનું યુનિવર્સિટી કે સરકારી કે પોતાનું વાહન ઈત્યાદી મારફત કરેલ મુસાફરીની સ્પષ્ટ નોંધ આપવી.</li>
        <li>કોલમ નં. ૧૧ થી ૧૩ માઈલેજ મેળવતા અધિકારીઓ કે સભ્યોએ ભરવી.</li>
        <li>કોલમ નં. ૧૬ માં માત્ર દૈનિક ભથ્થાની રકમ લેવી જેથી કોલમ (૧૪ X ૧૫= ૧૬) થઈ રહેવું જોઈએ.</li>
        <li>જયારે મુસાફરી ભથ્થા બીલમાં શરૂઆતમાં મુસાફરીને બદલે 'હોલ્ટ' દર્શાવવામાં આવેલ હોય તેવા કિસ્સામાં 'હોલ્ટ' ની શરૂઆત થયાની તારીખ કો.નં. ૧૯ માં દર્શાવવી.</li>
    </ol>
</div>

<div style="margin-top: 15px;">
    <strong>યુનિવર્સિટી કર્મચારીએ આપવાનું પ્રમાણપત્ર</strong>
    <ol style="margin-top: 5px; padding-left: 20px;">
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે, આ બીલમાં આકારેલ રકમ બીજા કોઈ બીલમાં આકારેલ નથી.</li>
        <li>આથી પ્રમાણીત કરવામાં આવે છે કે સદર મુસાફરી ભથ્થા બીલમાં દર્શાવેલ હકીકત સાચી છે... (નિયમોના ૬૫-૧ ના અનુમાનોને આધારે સાચો છે).</li>
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે બીલમાં દર્શાવેલ પ્રવાસ માટે મેં આ અગાઉ પેશગી લીધેલ નથી / <span style="text-decoration: line-through;">મે પેશગી લીધેલ છે...</span></li>
        <li>આ બીલમાં જણાવેલ યુનિવર્સિટી સિવાયની અન્ય સંસ્થાની ભ્રમગીરીના પ્રવાસ માટે... (નાણાં મળશે તો જમા કરાવવામાં આવશે).</li>
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે, પ્રવાસ ડાયરીમાં દર્શાવવામાં આવેલ સ્થળ, તારીખ, સમય, કિલોમીટર કચેરીના વાહન લોગબુક મુજબ આકારવામાં આવેલ છે.</li>
    </ol>
</div>

<div class="signature-row" style="margin-top: 20px;">
    <div></div>
    <div style="text-align: center;">
        <strong>(સચિન આર. પટેલ)</strong><br>
        સહ પ્રાધ્યાપક<br>
        કર્મચારીની સહી નામ અને હોદ્દો
    </div>
</div>

<hr style="border-top: 1px solid black; margin: 15px 0;">

<div>
    <strong>યુનિવર્સિટી અધિકારીઓ અને અન્ય સભ્યોએ આપવાનું પ્રમાણપત્ર</strong><br>
    <span style="font-size: 12px;">આથી પ્રમાણિત કરવામાં આવે છે કે સદર બીલમાં કરેલ મુસાફરી ભથ્થાનો દાવો આ અંગેના નિયમોની જોગવાઈઓના આધારે ખરો અને યોગ્ય છે.</span>
</div>

<div class="signature-row" style="margin-top: 30px;">
    <div></div>
    <div style="text-align: center;">
        <span class="input-line" style="width:150px;"></span><br>
        <strong>પ્રાધ્યાપક અને વડા</strong><br>
        કિટકશાત્ર વિભાગ<br>
        નં. મ. કૃષિ મહાવિદ્યાલય, નકૃયું, નવસારી
    </div>
</div>

<div class="box-border" style="margin-top: 20px;">
    <strong>કર્મચારી/અધિકારી / સભ્યશ્રીએ નીચેની વિગત ભરવી.</strong>
    
    <div class="calc-grid">
        <div>
            બીલની કુલ રકમ<br>
            <strong>12161</strong>
        </div>
        <div>-</div>
        <div>
            બાદ: બીલની પેશગીની રકમ<br>
            <strong>0</strong>
        </div>
        <div>=</div>
        <div>
            ચૂકવવા પાત્ર ચોખ્ખી રકમ<br>
            <strong>12161</strong>
        </div>
    </div>
    
    <div style="margin-top: 10px; border-top: 1px solid #ddd; padding-top: 5px;">
        અંકે રૂપિયા <strong>બાર હજાર એકસો એકસઠ પુરા</strong> મને મળ્યા છે.
    </div>
</div>

<div style="margin-top: 15px; display: flex; justify-content: space-between; font-size: 11px;">
    <div style="width: 55%;">
        પેશગીના નાણાં મળ્યાની તારીખ: <span class="input-line" style="width:80px;"></span><br>
        <div style="margin-top:5px;">પેશગી કયા ઝોન યુનિટમાંથી ઉપાડવામાં આવી: <span class="input-line" style="width:80px;"></span></div>
        <div style="margin-top:5px;">પેશગી ઉપાડવાના વાઉચર નંબર: <span class="input-line" style="width:50px;"></span> તારીખ: <span class="input-line" style="width:50px;"></span></div>
    </div>
    <div style="width: 40%; text-align: center; border: 1px solid black; padding: 5px;">
         <br><br>
         <strong>(સચિન આર. પટેલ)</strong><br>
         સહ પ્રાધ્યાપક<br>
         કર્મચારીની સહી
    </div>
</div>
"""

# ---------------------------------------------------------
# RENDER SIDE-BY-SIDE COLUMNS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div class="a4-page">{page1_html}</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="a4-page">{page2_html}</div>', unsafe_allow_html=True)
