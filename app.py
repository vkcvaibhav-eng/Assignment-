import streamlit as st

# 1. Setup the page layout
st.set_page_config(layout="wide", page_title="Navsari Uni Bill")

# 2. CSS for A4 Paper Layout and Gujarati Font Support
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;700&display=swap');

    .stApp {
        background-color: #555; /* Dark background to make pages pop */
    }
    
    .a4-page {
        background-color: white;
        color: black;
        width: 210mm;
        height: 297mm;
        padding: 15mm;
        margin: 10px auto;
        font-family: 'Noto Sans Gujarati', sans-serif;
        font-size: 12px;
        line-height: 1.4;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden; 
    }

    .header-center { text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 5px; }
    .sub-header { text-align: center; font-weight: bold; font-size: 14px; text-decoration: underline; margin-bottom: 15px; }
    
    .row-flex { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .field { border-bottom: 1px dotted black; flex-grow: 1; margin-left: 5px; }
    
    table.budget-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }
    table.budget-table th, table.budget-table td { border: 1px solid black; padding: 4px; text-align: left; }
    
    .signature-section { margin-top: 30px; display: flex; justify-content: space-between; align-items: flex-end; }
    .footer-calc { border: 1px solid black; padding: 10px; margin-top: 10px; }
    
    /* Utility for spacing */
    .spacer-10 { height: 10px; }
    .spacer-20 { height: 20px; }
    .bold { font-weight: bold; }
    .right { text-align: right; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 1 CONTENT (HTML Construction)
# ---------------------------------------------------------
page1_html = """
<div class="row-flex">
    <div>હિસાબી પત્રક નંબર: <span style="min-width:50px; display:inline-block; border-bottom:1px dotted black;">&nbsp;</span></div>
    <div>બીલ નંબર: <span style="min-width:50px; display:inline-block; border-bottom:1px dotted black;">&nbsp;</span></div>
    <div>તારીખ: <span style="min-width:80px; display:inline-block; border-bottom:1px dotted black;">&nbsp;</span></div>
</div>

<div class="header-center" style="font-size: 20px; margin-top: 10px;">નવસારી કૃષિ વિશ્વવિધાલય</div>
<div class="header-center">મુસાફરી ભથ્થા બીલ</div>

<div class="row-flex" style="margin-top: 15px;">
    <div style="width: 45%;">
        વાઉચર નં.: _________________<br>
        તારીખ: _________________
    </div>
    <div style="width: 45%; text-align: right;">
        યુનિટ નંબર: _________________<br>
        કોડ નંબર: _________________
    </div>
</div>

<div style="margin-top: 15px;">
    <strong>આચાર્ય અને ડીનશ્રી, નં. મ. કૃષિ મહાવિદ્યાલય, નવસારી ની કચેરીનું માહે: ઓક્ટોમ્બર - ૨૦૨૫ નું</strong>
</div>
<div class="sub-header">મુસાફરી ભથ્થા બિલ</div>

<div>
    યુનિટ/સબયુનિટ : <strong>આચાર્ય અને ડીનશ્રી, ન. મ. કૃષિ મહાવિદ્યાલય, નકૃયું, નવસારી</strong>
</div>

<div style="margin-top: 10px; text-align: justify;">
    આથી રૂ।. <strong>12161</strong> નો દાવો મંજુર કરી ગ્રાહય રાખવામાં આવે છે.
</div>

<div style="margin-top: 10px;">
    ખર્ચ માટેનું બજેટ સદર : __________________________________________<br>
    યોજનાનું નામ : __________________________________________
</div>

<div style="margin-top: 15px; border: 1px solid black; padding: 10px;">
    રૂા. <strong>12161</strong> ( અંકે રૂપિયા <strong>બાર હજાર એકસો એકસઠ પુરા</strong> પૈસા )
    <br><br>
    આ બીલમાં જણાવેલ રૂા _________ મંજુર કરવામાં આવે છે અને તે રોકડા / ચેક નં. _________ થી ચુકવવામાં આવે છે.
</div>

<div class="signature-section">
    <div style="text-align: left;">
        નવસારી<br>
        તારીખ : ______________
    </div>
    <div style="text-align: right;">
        બીલ મંજુર કરનાર અધિકારીની<br>
        સહી અને હોદ્દો
    </div>
</div>

<div style="display: flex; margin-top: 20px;">
    <div style="width: 60%;">
        <table class="budget-table">
            <tr>
                <th>વિગત</th>
                <th>રૂ.</th>
                <th>પૈસા</th>
            </tr>
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
        </table>
    </div>
    <div style="width: 40%; display: flex; align-items: flex-end; justify-content: flex-end;">
        <div style="text-align: center;">
            _______________________<br>
            નિયંત્રણ અધિકારીની સહી
        </div>
    </div>
</div>

<div style="margin-top: 10px;">
    રૂપ ( <strong>12161</strong> ) અંકે રૂપિયા : બાર હજાર એકસો એકસઠ પુરા મંજુર કર્યા.
</div>
"""

# ---------------------------------------------------------
# PAGE 2 CONTENT (HTML Construction)
# ---------------------------------------------------------
page2_html = """
<div style="font-size: 11px;">
    <strong>નોંધ :-</strong>
    <ol style="margin-top: 5px; padding-left: 20px;">
        <li>કોલમ નં. ૭ માં મુસાફરી પ્રકાર રેલ્વે/એસ.ટી./હવાઈ/સ્ટીમર/ભાડાનું યુનિવર્સિટી કે સરકારી કે પોતાનું વાહન ઈત્યાદી મારફત કરેલ મુસાફરીની સ્પષ્ટ નોંધ આપવી.</li>
        <li>કોલમ નં. ૧૧ થી ૧૩ માઈલેજ મેળવતા અધિકારીઓ કે સભ્યોએ ભરવી.</li>
        <li>કોલમ નં. ૧૬ માં માત્ર દૈનિક ભથ્થાની રકમ લેવી જેથી કોલમ (૧૪ X ૧૫= ૧૬) થઈ રહેવું જોઈએ.</li>
        <li>જયારે મુસાફરી ભથ્થા બીલમાં શરૂઆતમાં મુસાફરીને બદલે 'હોલ્ટ' દર્શાવવામાં આવેલ હોય તેવા કિસ્સામાં 'હોલ્ટ' ની શરૂઆત થયાની તારીખ કો.નં. ૧૯ માં દર્શાવવી.</li>
    </ol>
</div>

<div style="margin-top: 10px;">
    <strong>યુનિવર્સિટી કર્મચારીએ આપવાનું પ્રમાણપત્ર</strong>
    <ol style="margin-top: 5px; padding-left: 20px;">
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે, આ બીલમાં આકારેલ રકમ બીજા કોઈ બીલમાં આકારેલ નથી.</li>
        <li>આથી પ્રમાણીત કરવામાં આવે છે કે સદર મુસાફરી ભથ્થા બીલમાં દર્શાવેલ હકીકત સાચી છે અને સદર મુસાફરી ભથ્થા બીલમાં કરવામાં આવેલ દાવો વખતો વખત સુધારવામાં આવેલ ગુજરાત કૃષિ વિશ્વવિધાલય મુસાફરી ભથ્થા નિયમોના ૬૫-૧ ના અનુમાનોને આધારે સાચો છે.</li>
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે બીલમાં દર્શાવેલ પ્રવાસ માટે મેં આ અગાઉ પેશગી લીધેલ નથી / <span style="text-decoration: line-through;">મે પેશગી લીધેલ છે જેની વિગત નીચે દર્શાવેલ છે.</span> (લાગુ ન પડતી બાબત છેકી નાખવી).</li>
        <li>આ બીલમાં જણાવેલ યુનિવર્સિટી સિવાયની અન્ય સંસ્થાની ભ્રમગીરીના પ્રવાસ માટે જે તે સંસ્થા તરફથી પ્રવાસ ભથ્થના નાણાં મને મળેલ નથી અને જે તે સંસ્થા તરફથી નાણાં મળશે તો તે રકમ યુનિવર્સિટી ફંડમાં જમા કરાવવામાં આવશે.</li>
        <li>આથી પ્રમાણપત્ર આપવામાં આવે છે કે, પ્રવાસ ડાયરીમાં દર્શાવવામાં આવેલ સ્થળ, તારીખ, સમય, કિલોમીટર કચેરીના વાહન લોગબુક મુજબ આકારવામાં આવેલ છે.</li>
    </ol>
</div>

<div class="signature-section">
    <div></div>
    <div style="text-align: center;">
        <strong>(સચિન આર. પટેલ)</strong><br>
        સહ પ્રાધ્યાપક<br>
        કર્મચારીની સહી નામ અને હોદ્દો
    </div>
</div>

<hr style="margin: 10px 0; border-top: 1px solid black;">

<div>
    <strong>યુનિવર્સિટી અધિકારીઓ અને અન્ય સભ્યોએ આપવાનું પ્રમાણપત્ર</strong><br>
    આથી પ્રમાણિત કરવામાં આવે છે કે સદર બીલમાં કરેલ મુસાફરી ભથ્થાનો દાવો આ અંગેના નિયમોની જોગવાઈઓના આધારે ખરો અને યોગ્ય છે.
</div>

<div class="signature-section">
    <div></div>
    <div style="text-align: center;">
        _______________________<br>
        <strong>પ્રાધ્યાપક અને વડા</strong><br>
        કિટકશાત્ર વિભાગ<br>
        નં. મ. કૃષિ મહાવિદ્યાલય, નકૃયું, નવસારી
    </div>
</div>

<div class="footer-calc">
    <strong>કર્મચારી/અધિકારી / સભ્યશ્રીએ નીચેની વિગત ભરવી.</strong><br>
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <div>બીલની કુલ રકમ<br><strong>12161</strong></div>
        <div>-</div>
        <div>બાદ: બીલની પેશગીની રકમ<br><strong>0</strong></div>
        <div>=</div>
        <div>ચૂકવવા પાત્ર ચોખ્ખી રકમ<br><strong>12161</strong></div>
    </div>
    <div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 5px;">
        અંકે રૂપિયા <strong>બાર હજાર એકસો એકસઠ પુરા</strong> મને મળ્યા છે.
    </div>
</div>

<div style="margin-top: 15px; display: flex; justify-content: space-between; font-size: 11px;">
    <div style="width: 60%;">
        પેશગીના નાણાં મળ્યાની તારીખ: __________<br>
        પેશગી કયા ઝોન યુનિટમાંથી ઉપાડવામાં આવી: __________<br>
        પેશગી ઉપાડવાના વાઉચર નંબર: __________ તારીખ: ______
    </div>
    <div style="width: 35%; text-align: center; border: 1px solid black; padding: 5px;">
         <br><br>
         <strong>(સચિન આર. પટેલ)</strong><br>
         સહ પ્રાધ્યાપક<br>
         કર્મચારીની સહી
    </div>
</div>
"""

# ---------------------------------------------------------
# RENDER COLUMNS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div class="a4-page">{page1_html}</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="a4-page">{page2_html}</div>', unsafe_allow_html=True)
