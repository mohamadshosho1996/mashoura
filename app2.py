import datetime
import math
import os
import io
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==================== إعدادات Supabase الصحيحة ====================
SUPABASE_URL = "https://yrbkerayycejpsjnmusk.supabase.co"
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", "sb_publishable_5ympl-5sujP5Xbg7kun0xA__YeYZ..."))

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# ==================== إعدادات الصفحة والتصميم ====================
st.set_page_config(
    page_title="برنامج بودى للمشورة الأسرية",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# التنقل التلقائي بزر Enter
enter_navigation_js = """
<script>
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        const target = event.target;
        if (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA') {
            event.preventDefault();
            const formElements = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'));
            const index = formElements.indexOf(target);
            if (index > -1 && index + 1 < formElements.length) {
                formElements[index + 1].focus();
                formElements[index + 1].click();
            }
        }
    }
});
</script>
"""
st.components.v1.html(enter_navigation_js, height=0, width=0)

custom_css = """
<style>
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100%;
}
.main {
    background-color: #FFF5F8;
}
.stButton>button {
    background-color: #EC4899;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    border: none;
    padding: 0.5rem 1rem;
    width: 100%;
}
.stButton>button:hover {
    background-color: #BE185D;
    color: white;
}
h1, h2, h3 {
    color: #701A75;
}
footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==================== الثوابت وإعدادات البيانات ====================
DEFAULT_USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "د. شيماء 🌸"},
    "user1": {"pass": "1234", "role": "user", "name": "د. علا 🎀"},
    "user2": {"pass": "1234", "role": "user", "name": "د. عبير 🎀"},
    "user3": {"pass": "1234", "role": "user", "name": "د. ايه 🎀"},
}

VISIT_SCHEDULE_OPTIONS = [
    "الاسبوع الاول", "عمر شهرين", "عمر 4 شهور", "عمر 6 شهور",
    "عمر 9 شهور", "عمر 12 شهر", "عمر 18 شهر", "عمر سنتين",
    "عمر سنتين ونصف", "عمر 3 سنين", "عمر 3 سنين ونصف", "عمر 4 سنين",
    "عمر 4 سنين ونصف", "عمر 5 سنين", "عمر 5 سنين ونصف", "عمر 6 سنين"
]

DROPDOWN_OPTIONS = {
    "health_card": ["تم", "لم يتم"],
    "vaccine_importance": ["تم", "لم يتم"],
    "breastfeeding_nutrition": ["تم", "لم يتم"],
    "danger_signs": ["تم", "لم يتم"],
    "motor_development": ["طبيعى", "متقدم", "متاخر"],
    "cognitive_development": ["طبيعى", "متقدم", "متاخر"],
    "linguistic_development": ["طبيعى", "متقدم", "متاخر"],
    "family_planning": ["يوجد", "مرغوب", "غير مرغوب"]
}

# ربط الأسماء الإنجليزية في قاعدة البيانات بالنصوص العربية الواضحة في الواجهة
FIELD_LABELS = {
    "child_name": "اسم الطفل",
    "mom_nat_id": "الرقم القومى للام",
    "mom_phone": "رقم الموبايل للام",
    "weight": "الوزن (كجم)",
    "height": "الطول (سم)",
    "head_circumference": "محيط الرأس (سم)",
    "health_card": "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو",
    "vaccine_importance": "أهمية الإلتزام بتطعيمات الطفل",
    "breastfeeding_nutrition": "التغذية الصحية للأم المرضعة",
    "danger_signs": "كيفية التعرف على علامات الخطورة",
    "motor_development": "النمو والتطور الحركي",
    "cognitive_development": "التطور الإدراكي والمعرفي",
    "linguistic_development": "التطور اللغوي",
    "family_planning": "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة",
    "next_visit": "تخطيط الزيارة القادمة"
}

CHILD_COLUMNS = [
    "username", "visit_date", "child_name", "mom_nat_id", "mom_phone",
    "weight", "height", "head_circumference", "health_card", "vaccine_importance",
    "breastfeeding_nutrition", "danger_signs", "motor_development",
    "cognitive_development", "linguistic_development", "family_planning", "next_visit"
]

# ==================== الدالات المساعدة ====================
def clean_digits(val, max_len=None):
    if not val:
        return ""
    digits = "".join(filter(str.isdigit, str(val)))
    if max_len:
        return digits[:max_len]
    return digits

def clear_form_state():
    for col in CHILD_COLUMNS:
        st.session_state[f"c_{col}"] = ""

# ==================== تسجيل الدخول والصلاحيات ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.name = None
    st.session_state.role = None

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #BE185D;'>🌸 برنامج بودى للمشورة الأسرية 🌸</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #701A75;'>تسجيل الدخول للنظام</h4>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_options = {f"{v['name']} ({k})": k for k, v in DEFAULT_USERS.items()}
        selected_display = st.selectbox("اختر الحساب والطبيبة 🩺", list(user_options.keys()))
        username = user_options[selected_display]
        password = st.text_input("كلمة المرور", type="password")

        if st.button("تسجيل الدخول ✨", use_container_width=True):
            if DEFAULT_USERS[username]["pass"] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.name = DEFAULT_USERS[username]["name"]
                st.session_state.role = DEFAULT_USERS[username]["role"]
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة!")
    st.stop()

# ==================== القائمة والخيارات ====================
menu_options = ["سجل الأطفال", "استعراض البيانات"]
st.sidebar.markdown(f"### أهلاً بكِ د. {st.session_state.name} 🌸")
menu = st.sidebar.radio("القائمة الرئيسية", menu_options)

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown("---")

# ==================== سجل الأطفال ====================
if menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            st.session_state[f"c_{col}"] = today_str if col == "visit_date" else ""

    # عرض الحقول في واجهة المستخدم بالنصوص العربية الكاملة
    for col_name in CHILD_COLUMNS:
        if col_name in ["username"]:
            continue
        
        display_label = FIELD_LABELS.get(col_name, col_name)

        if col_name == "visit_date":
            st.session_state[f"c_{col_name}"] = st.text_input(display_label, value=today_str, key=f"c_{col_name}")
        elif col_name in DROPDOWN_OPTIONS:
            st.markdown(f"**{display_label}**")
            options = DROPDOWN_OPTIONS[col_name]
            current_val = st.session_state.get(f"c_{col_name}", options[0])
            chosen = st.radio(display_label, options, index=options.index(current_val) if current_val in options else 0, key=f"radio_{col_name}", horizontal=True)
            st.session_state[f"c_{col_name}"] = chosen
        else:
            if col_name == "mom_nat_id":
                raw = st.text_input(display_label, key=f"c_{col_name}")
                st.session_state[f"c_{col_name}"] = clean_digits(raw, 14)
            elif col_name == "mom_phone":
                raw = st.text_input(display_label, key=f"c_{col_name}")
                st.session_state[f"c_{col_name}"] = clean_digits(raw, 11)
            else:
                st.session_state[f"c_{col_name}"] = st.text_input(display_label, key=f"c_{col_name}")

    if st.button("💾 حفظ بيانات الطفل", use_container_width=True):
        final_child_data = {}
        for col in CHILD_COLUMNS:
            if col == "username":
                final_child_data[col] = st.session_state.name
            else:
                final_child_data[col] = st.session_state.get(f"c_{col}", "")

        try:
            supabase.table("children_records").insert(final_child_data).execute()
            st.success("تم حفظ بيانات الطفل في Supabase بنجاح! ✨")
            clear_form_state()
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ في قاعدة البيانات: {e}")

# ==================== استعراض البيانات ====================
elif menu == "استعراض البيانات":
    st.markdown("<h2>📊 استعراض سجلات الأطفال</h2>", unsafe_allow_html=True)
    try:
        res = supabase.table("children_records").select("*").execute()
        df_view = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        
        # تحويل أسماء الأعمدة إلى العربية عند العرض لراحة الطبيبات
        if not df_view.empty:
            df_view = df_view.rename(columns=FIELD_LABELS)

        st.dataframe(df_view, use_container_width=True)
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
