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
    "مستوى التعليم": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة بين الزوجين": ["نعم", "لا"],
    "وسيلة تنظيم الأسرة المستخدمة سابقا": ["توجد", "مرغوب", "غير مرغوب"],
    "شهر الحمل": ["الشهر الاول", "الشهر الثانى", "الشهر الثالث", "الشهر الرابع", "الشهر الخامس", "الشهر السادس", "الشهر السابع", "الشهر الثامن", "الشهر التاسع"],
    "أمراض مزمنة: إرتفاع ضغط الدم": ["تم", "لم يتم"],
    "أمراض مزمنة: السكر": ["تم", "لم يتم"],
    "أمراض مزمنة: إضطرابات الغدة": ["تم", "لم يتم"],
    "أمراض مزمنة: الأنيميا": ["تم", "لم يتم"],
    'مكملات "قبل": حمض الفوليك': ["تم", "لم يتم"],
    'مكملات "قبل": الحديد': ["تم", "لم يتم"],
    'مكملات "قبل": الكالسيوم': ["تم", "لم يتم"],
    'مكملات "أثناء": حمض الفوليك': ["تم", "لم يتم"],
    'مكملات "أثناء": الحديد': ["تم", "لم يتم"],
    'مكملات "أثناء": الكالسيوم': ["تم", "لم يتم"],
    "التغذية السليمة": ["تم", "لم يتم"],
    "المكملات الغذائية": ["تم", "لم يتم"],
    "التمرينات الرياضية": ["تم", "لم يتم"],
    "قسط من النوم والراحة": ["تم", "لم يتم"],
    "المتابعة الدورية للحمل": ["تم", "لم يتم"],
    "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة": ["تم", "لم يتم"],
    "المتاعب البسيطة في الشهور الأولى": ["تم", "لم يتم"],
    "المتاعب في الشهور الأخيرة": ["تم", "لم يتم"],
    "علامات الخطر أثناء الحمل": ["تم", "لم يتم"],
    "مشاكل الولادة المبكرة وكيفية تجنبها": ["تم", "لم يتم"],
    "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين": ["تم", "لم يتم"],
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي": ["تم", "لم يتم"],
    "إرتداء الملابس الفضفاضة المريحة": ["تم", "لم يتم"],
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ": ["تم", "لم يتم"],
    "علامات الولادة": ["تم", "لم يتم"],
    "مميزات الولادة الطبيعية": ["تم", "لم يتم"],
    "الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "ملامسة الجلد للجلد": ["تم", "لم يتم"],
    "البداية المبكرة للرضاعة الطبيعية": ["تم", "لم يتم"],
    "الرضاعة الطبيعية المطلقة": ["تم", "لم يتم"],
    "أهمية المباعدة": ["تم", "لم يتم"],
    "وسائل تنظيم الأسرة": ["تم", "لم يتم"],
    "إستخدام وسيلة بعد الولادة مباشرة": ["تم", "لم يتم"],
    "التطور العصبي والنفسي للطفل": ["طبيعى", "متقدم", "متاخر"],
    "مستوى التعليم للام": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "مستوى التعليم للاب": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة للام": ["يعمل", "لا تعمل"],
    "مكان الولادة": ["المستشفى", "المنزل"],
    "سبب دخول الحضانة": [
        "انخفاض وزن الطفل.", "احتياج الطفل لأدوية محددة بهذا الوقت.", "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.",
        "ارتفاع درجة حرارة جسم الرضيع.", "تعطل العمليات الحيوية بجسم الطفل.", "انخفاض معدل الجلوكوز في دم الطفل.",
        "معاناة الرضيع مشكلات في الجهاز الهضمي.", "إصابة الطفل بعدوى في الدم.", "إصابة الطفل بالصفراء.",
        "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.", "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي."
    ],
    "موعد الزيارة": VISIT_SCHEDULE_OPTIONS,
    "رضاعة طبيعية مع سوائل وأعشاب": ["تم", "لم يتم"],
    "رضاعة طبيعية مع صناعي": ["تم", "لم يتم"],
    "رضاعة لبن صناعي": ["تم", "لم يتم"],
    "دخول الحضانة": ["تم", "لم يتم"],
    "ملامسة الجلد فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "الرضاعة الطبيعية فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "موقف إستخدام وسيلة تنظيم أسرة": ["توجد", "مرغوب", "غير مرغوب", "حدث", "لم يحدث"],
    "الحمل الجديد": ["مرغوب", "غير مرغوب"],
    "الخدمات الغير ملباه": ["يوجد"],
    "تحويل الى عيادة تنظيم الاسره": ["تم", "لم يتم"],
    "النمو والتطور الحركي": ["طبيعى", "متقدم", "متاخر"],
    "التطور الإدراكي والمعرفي": ["طبيعى", "متقدم", "متاخر"],
    "التطور اللغوي": ["طبيعى", "متقدم", "متاخر"],
    "رسائل التربية الإيجابية": ["تم", "لم يتم"],
    "الأنشطة التحفيزية": ["تم", "لم يتم"],
    "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة": ["تم", "لم يتم"],
    "إعطاء الجرعة اليومية من الحديد": ["يوجد"],
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة": ["تم التوعيه", "لم يتم التوعيه"],
    "إعطاء الجرعة اليومية من فيتامين د": ["يوجد"],
    "كيفية رعاية السرة والإهتمام بنظافة الطفل": ["تم", "لم يتم"],
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو": ["تم", "لم يتم"],
    "أهمية الإلتزام بتطعيمات الطفل": ["تم", "لم يتم"],
    "التغذية الصحية للأم المرضعة": ["تم", "لم يتم"],
    "كيفية التعرف على علامات الخطورة": ["تم", "لم يتم"],
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع": ["تم", "لم يتم"],
    "كفاية اللبن وكمية البراز": ["تم", "لم يتم"],
}

PREGNANT_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "الاسم", "العنوان", "الرقم القومى", "رقم الموبايل",
    "العمر الحالى", "السن عند الزواج", "السن عند الحمل الاول", "مستوى التعليم", "الوظيفة",
    "تاريخ اخر دورة شهرية", "قرابة بين الزوجين", "عدد مرات الحمل", "عدد مرات الاجهاض",
    "عدد الاطفال", "المدة بين اخر حملين", "نوع الولادة", "أمراض مزمنة: إرتفاع ضغط الدم",
    "أمراض مزمنة: السكر", "أمراض مزمنة: إضطرابات الغدة", "أمراض مزمنة: الأنيميا", "أمراض مزمنة: اخرى",
    'مكملات "قبل": حمض الفوليك', 'مكملات "قبل": الحديد', 'مكملات "قبل": الكالسيوم',
    'مكملات "أثناء": حمض الفوليك', 'مكملات "أثناء": الحديد', 'مكملات "أثناء": الكالسيوم',
    "وسيلة تنظيم الأسرة المستخدمة سابقا", "مدة إستخدام الوسيلة السابقة", "شهر الحمل",
    "التاريخ الزيارة", "التغذية السليمة", "المكملات الغذائية", "التمرينات الرياضية",
    "قسط من النوم والراحة", "المتابعة الدورية للحمل",
    "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة",
    "المتاعب البسيطة في الشهور الأولى", "المتاعب في الشهور الأخيرة", "علامات الخطر أثناء الحمل",
    "مشاكل الولادة المبكرة وكيفية تجنبها", "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين",
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي", "إرتداء الملابس الفضفاضة المريحة",
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ", "علامات الولادة", "مميزات الولادة الطبيعية",
    "الساعة الذهبية الأولى", "ملامسة الجلد للجلد", "البداية المبكرة للرضاعة الطبيعية",
    "الرضاعة الطبيعية المطلقة", "أهمية المباعدة", "وسائل تنظيم الأسرة", "إستخدام وسيلة بعد الولادة مباشرة",
    "التطور العصبي والنفسي للطفل", "ملاحظات/ توصيات", "تخطيط الزيارة القادمة", "المتابعة ما بعد الولادة"
]

CHILD_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "تاريخ اول زيارة", "رقم الحالة", "اسم الام", "الرقم القومى للام",
    "رقم الموبايل للام", "تاريخ ميلاد الام", "مستوى التعليم للام", "عدد الاطفال لدى الام",
    "المدة بين اخر حملين", "الوظيفة للام", "الرقم القومى للاب", "رقم الموبايل للاب", "اسم الاب",
    "مستوى التعليم للاب", "اسم الطفل", "تاريخ الميلاد للطفل", "العمر الحالى للطفل (شهور)",
    "العمر الرحمى للطفل (أسابيع)", "مكان المتابعة (وحدة)", "مكان المتابعة (مستشفى)", "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)", "مصدر الاحالة (عيادة خاصة)", "مصدر الاحالة(عيادة التطعيمات)",
    "مصدر الاحالة(نصيحة)", "نوع الولادة", "مكان الولادة", "وزن الطفل عند الولادة", "طول الطفل عند الولادة",
    "مقاس راس الطفل عند الولادة", "دخول الحضانة", "سبب دخول الحضانة", "مدة البقاء فى الحضانة",
    "ملامسة الجلد فى الساعة الذهبية الأولى", "الرضاعة الطبيعية فى الساعة الذهبية الأولى", "موعد الزيارة",
    "تاريخ الزيارة", "رضاعة طبيعية مطلقة", "رضاعة طبيعية مع سوائل وأعشاب", "رضاعة طبيعية مع صناعي",
    "رضاعة لبن صناعي", "الوزن (كجم)", "الطول (سم)", "محيط الرأس (سم)",
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع", "كفاية اللبن وكمية البراز",
    "إعطاء الجرعة اليومية من فيتامين د", "كيفية رعاية السرة والإهتمام بنظافة الطفل",
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو", "أهمية الإلتزام بتطعيمات الطفل",
    "التغذية الصحية للأم المرضعة", "كيفية التعرف على علامات الخطورة", "النمو والتطور الحركي",
    "التطور الإدراكي والمعرفي", "التطور اللغوي", "رسائل التربية الإيجابية", "الأنشطة التحفيزية",
    "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة", "إعطاء الجرعة اليومية من الحديد",
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة", "موقف إستخدام وسيلة تنظيم أسرة",
    "الحمل الجديد", "الخدمات الغير ملباه", "تحويل الى عيادة تنظيم الاسره", "تخطيط الزيارة القادمة"
]

YES_NO_CHECKBOX_FIELDS = [
    "مكان المتابعة (وحدة)", "مكان المتابعة (مستشفى)", "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)", "مصدر الاحالة (عيادة خاصة)",
    "مصدر الاحالة(عيادة التطعيمات)", "مصدر الاحالة(نصيحة)"
]

# ==================== الدالات المساعدة ====================
def clean_digits(val, max_len=None):
    if not val:
        return ""
    digits = "".join(filter(str.isdigit, str(val)))
    if max_len:
        return digits[:max_len]
    return digits

def parse_national_id(nat_id):
    clean_id = clean_digits(nat_id, 14)
    if len(clean_id) == 14:
        century_code = int(clean_id[0])
        year_digits = int(clean_id[1:3])
        month = int(clean_id[3:5])
        day = int(clean_id[5:7])
        century = 2000 if century_code == 3 else 1900
        birth_year = century + year_digits
        try:
            birth_date = datetime.date(birth_year, month, day)
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return str(birth_date), str(age)
        except ValueError:
            return "", ""
    return "", ""

def calculate_motor_development(age_str, weight_birth, length_birth, weight_current, length_current):
    try:
        if not age_str:
            return "طبيعى"
        if "يوم" in age_str or "أسبوع" in age_str:
            age_months = 0.5
        else:
            age_months = float("".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1)
        w_curr = float(weight_current) if weight_current else 3.5
        expected_weight = 3.3 + (age_months * 0.8) if age_months <= 1 else (3.0 + (age_months * 0.75) if age_months <= 12 else 10.0 + ((age_months - 12) * 0.2))
        diff_ratio = w_curr / expected_weight
        if diff_ratio < 0.82:
            return "متاخر"
        elif diff_ratio > 1.25:
            return "متقدم"
        else:
            return "طبيعى"
    except Exception:
        return "طبيعى"

def fetch_auto_data_from_supabase(table_name, id_col_name, nat_id_val, prefix):
    clean_id = clean_digits(nat_id_val, 14)
    if len(clean_id) == 14 and st.session_state.get(f"{prefix}_last_fetched_id") != clean_id:
        try:
            response = supabase.table(table_name).select("*").eq(id_col_name, clean_id).execute()
            if response and hasattr(response, 'data') and response.data:
                latest_data = response.data[-1]
                cols = PREGNANT_COLUMNS if prefix == "p" else CHILD_COLUMNS
                for col in cols:
                    if col in latest_data and latest_data[col] is not None:
                        st.session_state[f"{prefix}_{col}"] = str(latest_data[col]).replace("'", "")
                st.session_state[f"{prefix}_last_fetched_id"] = clean_id
                st.toast("⚡ تم استدعاء بيانات الحساب المسجل تلقائياً من Supabase!", icon="✨")
        except Exception as e:
            print(f"Fetch Info: {e}")

def clear_form_state(prefix):
    cols = PREGNANT_COLUMNS if prefix == "p" else CHILD_COLUMNS
    for col in cols:
        st.session_state[f"{prefix}_{col}"] = ""
    st.session_state[f"{prefix}_last_fetched_id"] = ""

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

# ==================== القائمة والخيارات المشتركة ====================
menu_options = ["سجل الحوامل", "سجل الأطفال", "استعراض البيانات والداشبورد"]
if st.session_state.role == "admin":
    menu_options.append("إدارة المستخدمين")

st.sidebar.markdown(f"### أهلاً بكِ د. {st.session_state.name} 🌸")
sidebar_menu = st.sidebar.radio("القائمة الرئيسية (جانبية)", menu_options, key="sidebar_radio")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown("---")
col_mobile_nav, col_mobile_logout = st.columns([3, 1])
with col_mobile_nav:
    main_screen_menu = st.selectbox("📱 انتقل مباشرة إلى القسم المطلوب:", menu_options, key="mobile_selectbox")
with col_mobile_logout:
    if st.button("خروج 🚪"):
        st.session_state.logged_in = False
        st.rerun()

menu = main_screen_menu
st.markdown("---")

# ==================== 1. سجل الحوامل ====================
if menu == "سجل الحوامل":
    st.markdown("<h2>🤰 سجل المشورة الأسرية للحوامل</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in PREGNANT_COLUMNS:
        if f"p_{col}" not in st.session_state:
            st.session_state[f"p_{col}"] = today_str if col == "التاريخ الزيارة" else ""

    raw_id = st.text_input("الرقم القومى", key="p_الرقم القومى_input")
    clean_p_id = clean_digits(raw_id, 14)
    if clean_p_id:
        st.session_state["p_الرقم القومى"] = clean_p_id
        if len(clean_p_id) == 14:
            b_date, calc_age = parse_national_id(clean_p_id)
            if calc_age:
                st.session_state["p_العمر الحالى"] = calc_age
            fetch_auto_data_from_supabase("pregnant_records", "الرقم القومى", clean_p_id, "p")
    else:
        if not raw_id:
            st.session_state["p_الرقم القومى"] = ""

    form_data = {}
    for col_name in PREGNANT_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى"]:
            continue

        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"p_{col_name}", "")
            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1:
                chk_nat = st.checkbox("طبيعى", value=(current_val == "طبيعى"), key="p_birth_nat")
            with c_opt2:
                chk_ces = st.checkbox("قيصرى", value=(current_val == "قيصرى"), key="p_birth_ces")
            with c_opt3:
                chk_none = st.checkbox("لا يوجد", value=(current_val == "لا يوجد" or current_val == ""), key="p_birth_none")
            
            selected_birth = "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")
            form_data[col_name] = selected_birth
            st.session_state[f"p_{col_name}"] = selected_birth

        elif col_name in DROPDOWN_OPTIONS:
            st.markdown(f"**{col_name}**")
            options = DROPDOWN_OPTIONS[col_name]
            current_val = st.session_state.get(f"p_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}", options,
                index=(options.index(current_val) if current_val in options else 0),
                key=f"p_radio_{col_name}", horizontal=True
            )
            form_data[col_name] = chosen_choice
            st.session_state[f"p_{col_name}"] = chosen_choice
        else:
            if col_name == "رقم الموبايل":
                raw_val = st.text_input(col_name, key=f"p_{col_name}")
                cleaned_val = clean_digits(raw_val, 11)
                form_data[col_name] = cleaned_val
            elif col_name == "العمر الحالى":
                form_data[col_name] = st.text_input(f"{col_name} [محسوب تلقائياً من الرقم القومي]", key=f"p_{col_name}")
            elif col_name == "التاريخ الزيارة":
                form_data[col_name] = st.text_input(f"{col_name} [تاريخ اليوم التلقائي]", key=f"p_{col_name}")
            else:
                form_data[col_name] = st.text_input(col_name, key=f"p_{col_name}")

    if st.button("💾 حفظ بيانات الحامل", use_container_width=True):
        final_form_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ التسجيل":
                final_form_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_form_data[col] = st.session_state.name
            else:
                final_form_data[col] = st.session_state.get(f"p_{col}", form_data.get(col, ""))

        try:
            supabase.table("pregnant_records").insert(final_form_data).execute()
            st.success("تم حفظ بيانات الحامل في Supabase بنجاح! ✨")
            clear_form_state("p")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ في قاعدة البيانات: {e}")

# ==================== 2. سجل الأطفال ====================
elif menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            st.session_state[f"c_{col}"] = today_str if col in ["تاريخ الزيارة", "تاريخ اول زيارة"] else ""

    raw_nat_id_mom = st.text_input("الرقم القومى للام (اختياري)", key="c_الرقم القومى للام_input")
    clean_c_id = clean_digits(raw_nat_id_mom, 14)
    if clean_c_id:
        st.session_state["c_الرقم القومى للام"] = clean_c_id
        if len(clean_c_id) == 14:
            b_date_mom, _ = parse_national_id(clean_c_id)
            if b_date_mom and not st.session_state.get("c_تاريخ ميلاد الام"):
                st.session_state["c_تاريخ ميلاد الام"] = b_date_mom
            fetch_auto_data_from_supabase("children_records", "الرقم القومى للام", clean_c_id, "c")
    else:
        if not raw_nat_id_mom:
            st.session_state["c_الرقم القومى للام"] = ""

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
            continue

        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", "")
            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1:
                chk_nat = st.checkbox("طبيعى", value=(current_val == "طبيعى"), key="c_birth_nat")
            with c_opt2:
                chk_ces = st.checkbox("قيصرى", value=(current_val == "قيصرى"), key="c_birth_ces")
            with c_opt3:
                chk_none = st.checkbox("لا يوجد", value=(current_val == "لا يوجد" or current_val == ""), key="c_birth_none")
            
            st.session_state[f"c_{col_name}"] = "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")

        elif col_name == "رضاعة طبيعية مطلقة":
            st.markdown(f"**{col_name}**")
            c1, c2, c3 = st.columns(3)
            current_val = st.session_state.get(f"c_{col_name}", "")
            with c1:
                chk_3 = st.checkbox("3 شهور", value=(current_val == "3 شهور"), key="c_bf_ex_3")
            with c2:
                chk_4 = st.checkbox("4 شهور", value=(current_val == "4 شهور"), key="c_bf_ex_4")
            with c3:
                chk_6 = st.checkbox("6 شهور", value=(current_val == "6 شهور"), key="c_bf_ex_6")
            
            st.session_state[f"c_{col_name}"] = "3 شهور" if chk_3 else ("4 شهور" if chk_4 else ("6 شهور" if chk_6 else ""))

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            checked = st.checkbox(col_name, value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if checked else ""

        elif col_name in DROPDOWN_OPTIONS:
            options = DROPDOWN_OPTIONS[col_name]
            if col_name == "النمو والتطور الحركي":
                auto_motor = calculate_motor_development(
                    st.session_state.get("c_العمر الحالى للطفل (شهور)", ""),
                    st.session_state.get("c_وزن الطفل عند الولادة", ""),
                    st.session_state.get("c_طول الطفل عند الولادة", ""),
                    st.session_state.get("c_الوزن (كجم)", ""),
                    st.session_state.get("c_الطول (سم)", "")
                )
                if not st.session_state.get(f"c_{col_name}"):
                    st.session_state[f"c_{col_name}"] = auto_motor

            if col_name == "موعد الزيارة":
                auto_visit_choice = VISIT_SCHEDULE_OPTIONS[0]
                try:
                    age_str = st.session_state.get("c_العمر الحالى للطفل (شهور)", "")
                    if age_str:
                        if "يوم" in age_str or "أسبوع" in age_str:
                            auto_visit_choice = "الاسبوع الاول"
                        else:
                            age_num = float("".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 0)
                            if age_num <= 2: auto_visit_choice = "عمر شهرين"
                            elif age_num <= 4: auto_visit_choice = "عمر 4 شهور"
                            elif age_num <= 6: auto_visit_choice = "عمر 6 شهور"
                            elif age_num <= 9: auto_visit_choice = "عمر 9 شهور"
                            elif age_num <= 12: auto_visit_choice = "عمر 12 شهر"
                            elif age_num <= 18: auto_visit_choice = "عمر 18 شهر"
                            elif age_num <= 24: auto_visit_choice = "عمر سنتين"
                            elif age_num <= 30: auto_visit_choice = "عمر سنتين ونصف"
                            elif age_num <= 36: auto_visit_choice = "عمر 3 سنين"
                            elif age_num <= 42: auto_visit_choice = "عمر 3 سنين ونصف"
                            elif age_num <= 48: auto_visit_choice = "عمر 4 سنين"
                            elif age_num <= 54: auto_visit_choice = "عمر 4 سنين ونصف"
                            elif age_num <= 60: auto_visit_choice = "عمر 5 سنين"
                            elif age_num <= 66: auto_visit_choice = "عمر 5 سنين ونصف"
                            else: auto_visit_choice = "عمر 6 سنين"
                except Exception:
                    pass
                st.session_state[f"c_{col_name}"] = auto_visit_choice

            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}", options,
                index=(options.index(current_val) if current_val in options else 0),
                key=f"c_radio_{col_name}", horizontal=True
            )
            st.session_state[f"c_{col_name}"] = chosen_choice

        else:
            if col_name in ["الرقم القومى للام", "الرقم القومى للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم الموبايل للام", "رقم الموبايل للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name == "تاريخ ميلاد الام":
                st.text_input(f"{col_name} [يتولد تلقائياً إذا أُدخل الرقم القومي للأم]", key=f"c_{col_name}")
            elif col_name == "تاريخ الميلاد للطفل":
                default_date_val = datetime.date.today()
                existing_b_date = st.session_state.get(f"c_{col_name}", "")
                if existing_b_date:
                    try:
                        default_date_val = datetime.datetime.strptime(existing_b_date.strip(), "%Y-%m-%d").date()
                    except Exception:
                        pass
                chosen_date = st.date_input(col_name, value=default_date_val, key=f"c_date_input_{col_name}")
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                try:
                    today_date = datetime.date.today()
                    delta_days = (today_date - chosen_date).days
                    if delta_days >= 0:
                        if delta_days < 7: age_display = f"{delta_days} يوم"
                        elif delta_days < 30: age_display = f"{round(delta_days / 7)} أسبوع"
                        else:
                            m_cnt = round(delta_days / 30.44, 1)
                            age_display = f"{int(m_cnt)} شهر" if m_cnt.is_integer() else f"{m_cnt} شهر"
                        st.session_state["c_العمر الحالى للطفل (شهور)"] = age_display
                        g_weeks = max(24, min(42, 40 - max(0, round((280 - delta_days) / 7))))
                        st.session_state["c_العمر الرحمى للطفل (أسابيع)"] = f"{g_weeks} أسبوع"
                except Exception:
                    pass
            elif col_name == "العمر الحالى للطفل (شهور)":
                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")
            elif col_name == "العمر الرحمى للطفل (أسابيع)":
                st.text_input(f"{col_name} [محسوب بدقة بناءً على تاريخ الميلاد]", key=f"c_{col_name}")
            elif col_name == "طول الطفل عند الولادة":
                st.text_input(col_name, key=f"c_{col_name}")
                try:
                    w_val = st.session_state.get("c_وزن الطفل عند الولادة", "3.0")
                    l_val = st.session_state.get("c_طول الطفل عند الولادة", "50.0")
                    if w_val and l_val:
                        st.session_state["c_مقاس راس الطفل عند الولادة"] = str(round((float(l_val) / 2) + (float(w_val) * 0.5) + 10, 1))
                except Exception:
                    pass
            elif col_name == "محيط الرأس (سم)":
                try:
                    w_b = float(st.session_state.get("c_وزن الطفل عند الولادة", "3.0") or 3.0)
                    l_b = float(st.session_state.get("c_طول الطفل عند الولادة", "50.0") or 50.0)
                    w_c = float(st.session_state.get("c_الوزن (كجم)", "3.5") or 3.5)
                    l_c = float(st.session_state.get("c_الطول (سم)", "52.0") or 52.0)
                    age_s = st.session_state.get("c_العمر الحالى للطفل (شهور)", "1")
                    age_m = 0.5 if ("يوم" in age_s or "أسبوع" in age_s) else float("".join(filter(lambda x: x.isdigit() or x == ".", age_s)) or 1.0)
                    calc_head = round(((l_b * 0.35) + (w_b * 0.8) + 15.0 + (l_c * 0.1) + (w_c * 0.4) + (age_m * 0.5)) / 2.0 + 10.0, 1)
                    st.session_state[f"c_{col_name}"] = str(calc_head)
                except Exception:
                    pass
                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")
            elif col_name == "تخطيط الزيارة القادمة":
                try:
                    curr_v = st.session_state.get("c_موعد الزيارة", "")
                    reg_d = st.session_state.get("c_تاريخ الزيارة", today_str)
                    b_date = datetime.datetime.strptime(reg_d.strip(), "%Y-%m-%d").date()
                    d_add = 30
                    if curr_v in VISIT_SCHEDULE_OPTIONS:
                        idx = VISIT_SCHEDULE_OPTIONS.index(curr_v)
                        if idx + 1 < len(VISIT_SCHEDULE_OPTIONS):
                            n_v = VISIT_SCHEDULE_OPTIONS[idx + 1]
                            if "شهر" in n_v:
                                d_add = int("".join(filter(lambda x: x.isdigit(), n_v)) or 1) * 30
                            elif "سنين" in n_v or "سنتين" in n_v:
                                d_add = 30 * 30 if "نصف" in n_v else int("".join(filter(lambda x: x.isdigit(), n_v)) or 1) * 365
                    st.session_state[f"c_{col_name}"] = str(b_date + datetime.timedelta(days=d_add))
                except Exception:
                    pass
                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")
            else:
                st.text_input(col_name, key=f"c_{col_name}")

    if st.button("💾 حفظ بيانات الطفل", use_container_width=True):
        final_child_data = {}
        for col in CHILD_COLUMNS:
            if col == "تاريخ التسجيل":
                final_child_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_child_data[col] = st.session_state.name
            else:
                final_child_data[col] = st.session_state.get(f"c_{col}", "")

        try:
            supabase.table("children_records").insert(final_child_data).execute()
            st.success("تم حفظ بيانات الطفل في Supabase بنجاح! ✨")
            clear_form_state("c")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ في قاعدة البيانات: {e}")

# ==================== 3. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
    st.markdown("<h2>📊 لوحة المؤشرات واستعراض البيانات</h2>", unsafe_allow_html=True)
    sheet_to_show = st.selectbox("اختر السجل للاستعراض:", ["المشورة الاسرية للحامل", "سجل المشورة للاطفال"])
    db_table = "pregnant_records" if sheet_to_show == "المشورة الاسرية للحامل" else "children_records"

    try:
        res = supabase.table(db_table).select("*").execute()
        df_view = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        target_cols = PREGNANT_COLUMNS if sheet_to_show == "المشورة الاسرية للحامل" else CHILD_COLUMNS

        for c in target_cols:
            if c not in df_view.columns:
                df_view[c] = ""
        df_view = df_view[target_cols]

        st.markdown("### 📅 تصفية البيانات والبحث")
        search_query = st.text_input("🔍 بحث سريع:")
        filtered_df = df_view.copy()
        if search_query and not filtered_df.empty:
            mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 تحميل البيانات المعروضة (Excel)",
            data=excel_data,
            file_name=f"{db_table}_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات من Supabase: {e}")

# ==================== 4. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
    st.markdown("<h2>⚙️ إدارة المستخدمين والصلاحيات</h2>", unsafe_allow_html=True)
    for k, v in DEFAULT_USERS.items():
        st.write(f"- **{v['name']}** | اسم المستخدم: `{k}` | الصلاحية: `{v['role']}`")
