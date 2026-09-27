import streamlit as st
import pandas as pd
import sqlite3
import datetime
import urllib.parse

# --- PAGE CONFIG & CUSTOM CAMPSEC STYLING ---
st.set_page_config(
    page_title="CampSec | יובל פתרונות אבטחה",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom RTL CSS to replicate the exact CampSec Web App UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Rubik', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Top App Navigation Bar */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 20px 30px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .app-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .app-subtitle {
        color: #93c5fd;
        font-size: 14px;
        margin-top: 4px;
    }
    
    /* KPI Cards */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border-right: 5px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .kpi-title {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 5px;
    }
    .kpi-desc {
        font-size: 12px;
        color: #10b981;
        font-weight: 500;
        margin-top: 4px;
    }
    
    /* Status Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-green { background-color: #d1fae5; color: #065f46; }
    .badge-yellow { background-color: #fef3c7; color: #92400e; }
    .badge-red { background-color: #fee2e2; color: #991b1b; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    
    /* Escort Rules Banner */
    .alert-banner {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        color: #9f1239;
        padding: 14px 20px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_FILE = "yuval_campsec.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS guards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, tz TEXT UNIQUE, phone TEXT, role TEXT, site TEXT,
            classification TEXT, cert TEXT, weapon TEXT, safety TEXT,
            license_exp TEXT, apparel TEXT, missing_docs TEXT, is_active INT DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, email TEXT, site TEXT,
            military_bg TEXT, cert TEXT, status TEXT, date_added TEXT
        )
    """)
    conn.commit()
    
    # Seed default sample data if empty
    c.execute("SELECT COUNT(*) FROM guards")
    if c.fetchone()[0] == 0:
        sample_guards = [
            ("ישראל ישראלי", "012345678", "0501234567", 'מנהל יחידה / קב"ט', "מתקן פי גלילות", "סיווג 6", "מתקדם ב'", "כן (M16)", "תקין", "2027-12-31", "L", "תקין"),
            ("אבי כהן", "023456789", "0502345678", 'אחמ"ש', "מתקן תקשוב", "סיווג 3", "מתקדם ב'", "כן (M16)", "תקין", "2026-11-30", "M", "חסר תמונת פספורט"),
            ("משה לוי", "034567890", "0503456789", 'אחמ"ש', "יחידה 12", "סיווג 6", "מתקדם ב'", "כן (M16)", "תקין", "2027-05-15", "XL", "תקין"),
            ("דוד מזרחי", "045678901", "0504567890", 'אחמ"ש', "בית יציב", "סיווג 3", "מתקדם ב'", "כן (M16)", "תקין", "2026-09-30", "L", "חסר אישור רפואי"),
            ("תומר גבאי", "056789012", "0505678901", "סייר ממונע", "וולוו", "סיווג 3", "רמה א'", "כן (אקדח)", "תקין", "2027-01-10", "M", "תקין"),
            ("חיים גולדברג", "067890123", "0506789012", "קב"ט אתר", "מתקן קמפוס", "סיווג 6", "מתקדם ב'", "כן (M16)", "תקין", "2028-04-20", "XXL", "תקין")
        ]
        c.executemany("""
            INSERT INTO guards (name, tz, phone, role, site, classification, cert, weapon, safety, license_exp, apparel, missing_docs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_guards)
        
    c.execute("SELECT COUNT(*) FROM leads")
    if c.fetchone()[0] == 0:
        sample_leads = [
            ("אלירן שוקרון", "0521112233", "eliran@example.com", "מתקן פי גלילות", "קרבי - 07", "מתקדם ב' (M16)", "חדש - להזמין לראיון", "2026-09-23"),
            ("תומר אזולאי", "0542223344", "tomer@example.com", "מתקן קמפוס", "רובאי 05", "רמה א' (אקדח)", "נשלח זימון לראיון", "2026-09-22"),
            ("שגיא שטרן", "0503334455", "sagi@example.com", "יחידה 12", "קרבי - 08", "מתקדם ב' (M16)", "התקבל - להשלים 101", "2026-09-21")
        ]
        c.executemany("""
            INSERT INTO leads (name, phone, email, site, military_bg, cert, status, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_leads)
        
    conn.commit()
    conn.close()

init_db()

# --- HEADER SECTION ---
col_logo, col_head = st.columns([1, 5])
with col_head:
    st.markdown("""
        <div class="app-header">
            <div>
                <div class="app-title">🛡️ CampSec · יובל פתרונות אבטחה</div>
                <div class="app-subtitle">מערכת ניהול סד"כ, משמרות, ליווים ולידים מולטי-אתרים | yuvalshamdar@gmail.com</div>
            </div>
            <div style="text-align: left;">
                <span class="badge badge-green">✓ מחובר כמנהל מערכת</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.image("/workspace/artifacts/yuval_security_logo.png", use_column_width=True)
st.sidebar.title("📌 ניווט במערכת CampSec")

sites_list = ["כל 6 האתרים", "מתקן פי גלילות", "מתקן קמפוס", "יחידה 12", "מתקן תקשוב", "בית יציב", "וולוו"]
selected_site = st.sidebar.selectbox("🏢 סינון לפי אתר אבטחה:", sites_list)

menu = st.sidebar.radio(
    "תפריט מודולים:",
    [
        "📊 דשבורד מנהל ומדדים",
        "👥 תיקי מאבטחים ומצבה",
        "📩 ניהול לידים ומיזוג מיילים",
        "📅 סידור עבודה ואילוצים",
        "🚶 ניהול ליווים וציוד",
        "🎯 ניהול משימות אתר",
        "💬 טפסים ושיחות קב"ט",
        "⏱️ דוח שעות ותקן"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("📧 דוא"ל מנהל: **yuvalshamdar@gmail.com**

📲 תמיכה טכנית WhatsApp: **050-1234567**")

# Helper DB connection
def get_guards(site_filter):
    conn = sqlite3.connect(DB_FILE)
    if site_filter == "כל 6 האתרים":
        df = pd.read_sql_query("SELECT * FROM guards WHERE is_active=1", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM guards WHERE is_active=1 AND site=?", conn, params=(site_filter,))
    conn.close()
    return df

def get_leads():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()
    return df

# --- MODULE 1: DASHBOARD ---
if menu == "📊 דשבורד מנהל ומדדים":
    st.header("📊 דשבורד מנהל מבצעי — CampSec")
    
    df_guards = get_guards(selected_site)
    df_leads = get_leads()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">סה"כ סד"כ פעיל במצבה</div>
                <div class="kpi-value">{len(df_guards)}</div>
                <div class="kpi-desc">לוחמים ומאבטחים</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        armed_cnt = len(df_guards[df_guards['weapon'].str.contains('M16|אקדח|כן', na=False)])
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">סה"כ חמושים (M16/אקדח)</div>
                <div class="kpi-value">{armed_cnt}</div>
                <div class="kpi-desc">מורשי נשק אקטיביים</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        class_cnt = len(df_guards[df_guards['classification'].str.contains('3|6', na=False)])
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">בעלי סיווג 3 / 6</div>
                <div class="kpi-value">{class_cnt}</div>
                <div class="kpi-desc">אישור ביטחוני בתוקף</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">לידים חדשים בגיוס</div>
                <div class="kpi-value">{len(df_leads)}</div>
                <div class="kpi-desc">מועמדים בקליטה</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.subheader("🏢 סד"כ ותקן אבטחה ב-6 האתרים המבצעיים")
    sites_data = [
        {"אתר אבטחה": "מתקן פי גלילות", "סוג מתקן": "תשתיות דלק (רמה ב')", "תקן יומי": 8, "מצבה פעילה": 13, "קב"ט אתר": "ישראל ישראלי", "סטטוס כיסוי": "✓ תקין (162%)"},
        {"אתר אבטחה": "מתקן קמפוס", "סוג מתקן": "מתקן אקדמי (רמה א')", "תקן יומי": 6, "מצבה פעילה": 9, "קב"ט אתר": "חיים גולדברג", "סטטוס כיסוי": "✓ תקין (150%)"},
        {"אתר אבטחה": "יחידה 12", "סוג מתקן": "מתקן מסווג (רמה ב')", "תקן יומי": 6, "מצבה פעילה": 8, "קב"ט אתר": "אלון שרעבי", "סטטוס כיסוי": "✓ תקין (133%)"},
        {"אתר אבטחה": "מתקן תקשוב", "סוג מתקן": "מתקן טכנולוגי (רמה ב')", "תקן יומי": 4, "מצבה פעילה": 6, "קב"ט אתר": "אבי כהן", "סטטוס כיסוי": "✓ תקין (150%)"},
        {"אתר אבטחה": "בית יציב", "סוג מתקן": "מתחם חינוך ושגרה", "תקן יומי": 4, "מצבה פעילה": 5, "קב"ט אתר": "דוד מזרחי", "סטטוס כיסוי": "✓ תקין (125%)"},
        {"אתר אבטחה": "וולוו", "סוג מתקן": "מתחם לוגיסטי", "תקן יומי": 4, "מצבה פעילה": 5, "קב"ט אתר": "תומר גבאי", "סטטוס כיסוי": "✓ תקין (125%)"}
    ]
    st.dataframe(pd.DataFrame(sites_data), use_container_width=True, hide_index=True)

# --- MODULE 2: GUARDS DATABASE ---
elif menu == "👥 תיקי מאבטחים ומצבה":
    st.header("👥 תיקי מאבטחים ומסד נתונים")
    df_guards = get_guards(selected_site)
    
    # Generate direct WhatsApp and Email Links
    df_display = df_guards.copy()
    df_display['WhatsApp'] = df_display['phone'].apply(lambda x: f"https://wa.me/972{str(x).replace('-','').lstrip('0')}")
    df_display['Mail Merge'] = df_display.apply(lambda r: f"mailto:yuvalshamdar@gmail.com?subject=עדכון תיק מאבטח - {r['name']} ({r['site']})&body=שלום {r['name']},

הודעה בנוגע לתיק אישי באתר {r['site']}.", axis=1)
    
    st.dataframe(
        df_display[['name', 'tz', 'phone', 'role', 'site', 'classification', 'cert', 'weapon', 'safety', 'license_exp', 'apparel', 'missing_docs']],
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("💬 פנייה מהירה ב-WhatsApp ומיזוג מיילים")
    selected_guard = st.selectbox("בחר מאבטח לפנייה:", df_guards['name'].tolist() if not df_guards.empty else ["אין נתונים"])
    if selected_guard != "אין נתונים":
        g_info = df_guards[df_guards['name'] == selected_guard].iloc[0]
        wa_url = f"https://wa.me/972{str(g_info['phone']).replace('-','').lstrip('0')}?text=" + urllib.parse.quote(f"שלום {g_info['name']}, תזכורת משמרת/חוסרים בתיק אישי באתר {g_info['site']}.")
        mail_url = f"mailto:yuvalshamdar@gmail.com?subject=" + urllib.parse.quote(f"עדכון תיק אישי - {g_info['name']}") + "&body=" + urllib.parse.quote(f"שלום {g_info['name']},
אנא העבר את הטפסים החסרים: {g_info['missing_docs']}.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<a href="{wa_url}" target="_blank" style="background-color:#25d366;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">💬 פנה ב-WhatsApp בשיחה ישירה</a>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<a href="{mail_url}" target="_blank" style="background-color:#1e3a8a;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">📧 שלח דוא"ל מורחב (Mail Merge)</a>', unsafe_allow_html=True)

# --- MODULE 3: LEADS & MAIL MERGE ---
elif menu == "📩 ניהול לידים ומיזוג מיילים":
    st.header("📩 ניהול לידים, מועמדים ומיזוג מיילים (Mail Merge)")
    st.info("כתובת מייל שולח רשמית: **yuvalshamdar@gmail.com**")
    
    df_leads = get_leads()
    st.dataframe(df_leads[['id', 'name', 'phone', 'email', 'site', 'military_bg', 'cert', 'status', 'date_added']], use_container_width=True, hide_index=True)
    
    st.subheader("➕ הוספת ליד / מועמד חדש למערכת")
    with st.form("add_lead_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            l_name = st.text_input("שם מלא:")
            l_phone = st.text_input("טלפון:")
        with c2:
            l_email = st.text_input("דוא"ל:")
            l_site = st.selectbox("אתר מבוקש:", sites_list[1:])
        with c3:
            l_mil = st.text_input("רקע צבאי / רובאי:")
            l_cert = st.selectbox("הסמכה נדרשת:", ["מתקדם ב' (M16)", "רמה א' (אקדח)", "ללא הסמכה"])
        
        submitted = st.form_submit_button("שמור ליד במערכת")
        if submitted and l_name:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("""
                INSERT INTO leads (name, phone, email, site, military_bg, cert, status, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (l_name, l_phone, l_email, l_site, l_mil, l_cert, "חדש - להזמין לראיון", str(datetime.date.today())))
            conn.commit()
            conn.close()
            st.success(f"הליד {l_name} נשמר בהצלחה!")
            st.rerun()

# --- MODULE 4: SHIFT SCHEDULE ---
elif menu == "📅 סידור עבודה ואילוצים":
    st.header("📅 סידור עבודה שבועי ובקרת אילוצים")
    st.markdown("""
        <div style="display:flex; gap:15px; margin-bottom:15px;">
            <span class="badge badge-yellow">🟨 צהוב = אילוץ</span>
            <span class="badge badge-red">🟥 אדום = לילה+בוקר עוקב</span>
            <span class="badge badge-blue">🟦 כחול = ללא תפקיד</span>
            <span class="badge badge-green">🟩 ירוק = שיבוץ תקין</span>
        </div>
    """, unsafe_allow_html=True)
    
    schedule_data = [
        {"מאבטח / תפקיד": "אבי כהן (אחמ"ש)", "א": "בוקר", "ב": "לילה", "ג": "אילוץ (מוצדק)", "ד": "בוקר", "ה": "צהריים", "ו": "בוקר", "ש": "מנוחה"},
        {"מאבטח / תפקיד": "משה לוי (אחמ"ש)", "א": "צהריים", "ב": "בוקר", "ג": "בוקר", "ד": "לילה", "ה": "מנוחה", "ו": "צהריים", "ש": "בוקר"},
        {"מאבטח / תפקיד": "דוד מזרחי (אחמ"ש)", "א": "לילה", "ב": "צהריים", "ג": "צהריים", "ד": "אילוץ (מוצדק)", "ה": "בוקר", "ו": "לילה", "ש": "צהריים"},
        {"מאבטח / תפקיד": "יוסי אברהם (מאבטח)", "א": "בוקר", "ב": "בוקר", "ג": "לילה", "ד": "צהריים", "ה": "לילה", "ו": "אילוץ", "ש": "מנוחה"},
        {"מאבטח / תפקיד": "תומר גבאי (סייר)", "א": "צהריים", "ב": "לילה", "ג": "בוקר", "ד": "בוקר", "ה": "לילה", "ו": "מנוחה", "ש": "לילה"}
    ]
    st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)

# --- MODULE 5: ESCORTS & EQUIPMENT ---
elif menu == "🚶 ניהול ליווים וציוד":
    st.header("🚶 ניהול ליווים, סיווגי קומות ומלאי ציוד")
    st.markdown("""
        <div class="alert-banner">
            ⚠️ <b>חוקי ברזל לליווים:</b> אין אישור לליווי עובדים זרים/מז' ירושלים | מלווה 1 מלווה עד 4 עובדים בקשר עין באותו מתחם בלבד.
        </div>
    """, unsafe_allow_html=True)
    
    escort_data = [
        {"תאריך": "2026-09-23", "חברה מלווה": "קבלני תשתיות אלקטרה", "מתחם באתר": "מתחם מכליות ב'", "קומה/אזור": "קומה 1 - צנרת", "סיווג": "שמור", "מס' עובדים": 3, "מאבטח מלווה": "תומר גבאי", "סטטוס": "בביצוע"},
        {"תאריך": "2026-09-23", "חברה מלווה": "תקשורת בזק", "מתחם באתר": "חמ"ל וניהול", "קומה/אזור": "קומה 2 - שרתים", "סיווג": "סודי", "מס' עובדים": 2, "מאבטח מלווה": "אבי כהן", "סטטוס": "מתוכנן"}
    ]
    st.dataframe(pd.DataFrame(escort_data), use_container_width=True, hide_index=True)

# --- MODULE 6: TASKS ---
elif menu == "🎯 ניהול משימות אתר":
    st.header("🎯 ניהול משימות אתר ושגרה")
    tasks_data = [
        {"סטטוס": "בטיפול", "נושא המשימה": "ביקורת תקינות מערכת כריזה וסירנה", "מבצע": "תומר גבאי", "עדיפות": "דחופה", "יעד": "2026-09-24", "תדירות": "שבועי"},
        {"סטטוס": "פתוחה", "נושא המשימה": "רענון נהלי פתיחה באש וטוהר הנשק", "מבצע": "אבי כהן", "עדיפות": "גבוהה", "יעד": "2026-09-26", "תדירות": "חודשי"},
        {"סטטוס": "הושלמה", "נושא המשימה": "בדיקת תיקי עזרה ראשונה בחמ"ל", "מבצע": "דוד מזרחי", "עדיפות": "רגילה", "יעד": "2026-09-22", "תדירות": "חודשי"}
    ]
    st.dataframe(pd.DataFrame(tasks_data), use_container_width=True, hide_index=True)

# --- MODULE 7: FORMS ---
elif menu == "💬 טפסים ושיחות קב"ט":
    st.header("💬 סיכום שיחות קב"ט וראיונות מועמדים")
    forms_data = [
        {"תאריך": "2026-09-20", "מאבטח": "יוסי אברהם", "מראיין/קב"ט": "ישראל ישראלי", "סוג השיחה": "שיחה תקופתית", "תוכן": "דיון בהשלמת אישור משטרה", "סיכום": "ימציא אישור עד 30.09", "חתימה": "✓ נחתם"},
        {"תאריך": "2026-09-21", "מאבטח": "עידו שלום", "מראיין/קב"ט": "ישראל ישראלי", "סוג השיחה": "תיאום רענון", "תוכן": "תיאום מועד לרענון ירי בקליבר 3", "סיכום": "שובץ לרענון ב-28.09", "חתימה": "✓ נחתם"}
    ]
    st.dataframe(pd.DataFrame(forms_data), use_container_width=True, hide_index=True)

# --- MODULE 8: HOURS REPORT ---
elif menu == "⏱️ דוח שעות ותקן":
    st.header("⏱️ דוח שעות ותקן מול ביצוע (נעול לשינויים)")
    st.info("הגדרת חישוב: דילוג שבתות/חגים | שעות חודשיות כוללות: 2,640 שעות")
    hours_data = [
        {"עמדת אבטחה": "חמ"ל ופיקוד", "תקן חודשי (שעות)": 720, "בוצע בפועל": 720, "פער": 0, "אחוז ביצוע": "100%", "סטטוס": "✓ ירוק (עומד בתקן)"},
        {"עמדת אבטחה": "שער ראשי (בידוק מכליות)", "תקן חודשי (שעות)": 720, "בוצע בפועל": 720, "פער": 0, "אחוז ביצוע": "100%", "סטטוס": "✓ ירוק (עומד בתקן)"},
        {"עמדת אבטחה": "סיור ממונע היקפי", "תקן חודשי (שעות)": 720, "בוצע בפועל": 720, "פער": 0, "אחוז ביצוע": "100%", "סטטוס": "✓ ירוק (עומד בתקן)"},
        {"עמדת אבטחה": "תגבור / עמדה אחורית", "תקן חודשי (שעות)": 480, "בוצע בפועל": 480, "פער": 0, "אחוז ביצוע": "100%", "סטטוס": "✓ ירוק (עומד בתקן)"}
    ]
    st.dataframe(pd.DataFrame(hours_data), use_container_width=True, hide_index=True)
