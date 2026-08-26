import datetime
import math
import os
import io
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_mic_recorder import mic_recorder

# ==================== إعدادات Supabase (آمنة عبر Secrets) ====================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ برجاء ضبط إعدادات الاتصال بـ Supabase (SUPABASE_URL و SUPABASE_KEY) في ملف الـ Secrets أو متغيرات البيئة.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# ==================== الثوابت ====================
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

VISIT_MONTHS_MAP = {
    "الاسبوع الاول": 0.25,
    "عمر شهرين": 2,
    "عمر 4 شهور": 4,
    "عمر 6 شهور": 6,
    "عمر 9 شهور": 9,
    "عمر 12 شهر": 12,
    "عمر 18 شهر": 18,
    "عمر سنتين": 24,
    "عمر سنتين ونصف": 30,
    "عمر 3 سنين": 36,
    "عمر 3 سنين ونصف": 42,
    "عمر 4 سنين": 48,
    "عمر 4 سنين ونصف": 54,
    "عمر 5 سنين": 60,
    "عمر 5 سنين ونصف": 66,
    "عمر 6 سنين": 72
}

DROPDOWN_OPTIONS = {
    "مستوى_التعليم": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة_بين_الزوجين": ["نعم", "لا"],
    "وسيلة_تنظيم_الأسرة_المستخدمة_سابقا": ["توجد", "مرغوب", "غير مرغوب"],
    "شهر_الحمل": [f"الشهر {x}" for x in ["الاول", "الثانى", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع"]],
    "امراض_مزمنة_ضغط_الدم": ["تم", "لم يتم"],
    "امراض_مزمنة_السكر": ["تم", "لم يتم"],
    "امراض_مزمنة_الغدة": ["تم", "لم يتم"],
    "امراض_مزمنة_الأنيميا": ["تم", "لم يتم"],
    "مكملات_قبل_حمض_الفوليك": ["تم", "لم يتم"],
    "مكملات_قبل_الحديد": ["تم", "لم يتم"],
    "مكملات_قبل_الكالسيوم": ["تم", "لم يتم"],
    "مكملات_اثناء_حمض_الفوليك": ["تم", "لم يتم"],
    "مكملات_اثناء_الحديد": ["تم", "لم يتم"],
    "مكملات_اثناء_الكالسيوم": ["تم", "لم يتم"],
    "التغذية_السليمة": ["تم", "لم يتم"],
    "المكملات_الغذائية": ["تم", "لم يتم"],
    "التمرينات_الرياضية": ["تم", "لم يتم"],
    "قسط_من_النوم_والراحة": ["تم", "لم يتم"],
    "المتابعة_الدورية_للحمل": ["تم", "لم يتم"],
    "التحذير_من_الأدوية": ["تم", "لم يتم"],
    "المتاعب_البسيطة": ["تم", "لم يتم"],
    "المتاعب_في_الشهور_الأخيرة": ["تم", "لم يتم"],
    "علامات_الخطر_أثناء_الحمل": ["تم", "لم يتم"],
    "مشاكل_الولادة_المبكرة": ["تم", "لم يتم"],
    "حركة_الجنين": ["تم", "لم يتم"],
    "تغير_لون_الجلد": ["تم", "لم يتم"],
    "ارتداء_الملابس_الفضفاضة": ["تم", "لم يتم"],
    "الاستعداد_للولادة": ["تم", "لم يتم"],
    "علامات_الولادة": ["تم", "لم يتم"],
    "مميزات_الولادة_الطبيعية": ["تم", "لم يتم"],
    "الساعة_الذهبية_الأولى": ["تم", "لم يتم"],
    "ملامسة_الجلد_للجلد": ["تم", "لم يتم"],
    "البداية_المبكرة_للرضاعة": ["تم", "لم يتم"],
    "الرضاعة_الطبيعية_المطلقة": ["تم", "لم يتم"],
    "اهمية_المباعدة": ["تم", "لم يتم"],
    "وسائل_تنظيم_الأسرة": ["تم", "لم يتم"],
    "استخدام_وسيلة_بعد_الولادة": ["تم", "لم يتم"],
    "التطور_العصبي_والنفسي": ["طبيعى", "متقدم", "متاخر"],
    "مستوى_التعليم_للام": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "مستوى_التعليم_للاب": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة_للام": ["يعمل", "لا تعمل"],
    "مكان_الولادة": ["المستشفى", "المنزل"],
    "سبب_دخول_الحضانة": [
        "انخفاض وزن الطفل.", "احتياج الطفل لأدوية محددة بهذا الوقت.",
        "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.", "ارتفاع درجة حرارة جسم الرضيع.",
        "تعطل العمليات الحيوية بجسم الطفل.", "انخفاض معدل الجلوكوز في دم الطفل.",
        "معاناة الرضيع مشكلات في الجهاز الهضمي.", "إصابة الطفل بعدوى في الدم.",
        "إصابة الطفل بالصفراء.", "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.",
        "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي."
    ],
    "رضاعة_مع_سوائل": ["تم", "لم يتم"],
    "رضاعة_مع_صناعي": ["تم", "لم يتم"],
    "رضاعة_لبن_صناعي": ["تم", "لم يتم"],
    "دخول_الحضانة": ["تم", "لم يتم"],
    "ملامسة_الجلد_الساعة_الذهبية": ["تم", "لم يتم"],
    "الرضاعة_الساعة_الذهبية": ["تم", "لم يتم"],
    "موقف_الوسيلة": ["توجد", "مرغوب", "غير مرغوب", "حدث", "لم يحدث"],
    "الحمل_الجديد": ["مرغوب", "غير مرغوب"],
    "الخدمات_الغير_ملباه": ["يوجد"],
    "تحويل_تنظيم_الاسره": ["تم", "لم يتم"],
    "النمو_الحركي": ["طبيعى", "متقدم", "متاخر"],
    "التطور_الإدراكي": ["طبيعى", "متقدم", "متاخر"],
    "التطور_اللغوي": ["طبيعى", "متقدم", "متاخر"],
    "التربية_الإيجابية": ["تم", "لم يتم"],
    "الأنشطة_التحفيزية": ["تم", "لم يتم"],
    "التغذية_التكميلية": ["تم", "لم يتم"],
    "جرعة_الحديد": ["يوجد"],
    "أهمية_الوسيلة": ["تم التوعيه", "لم يتم التوعيه"],
    "فيتامين_د": ["يوجد"],
    "رعاية_السرة": ["تم", "لم يتم"],
    "البطاقة_الصحية": ["تم", "لم يتم"],
    "التطعيمات": ["تم", "لم يتم"],
    "التغذية_للام": ["تم", "لم يتم"],
    "علامات_الخطورة": ["تم", "لم يتم"],
    "فوائد_الرضاعة": ["تم", "لم يتم"],
    "كفاية_اللبن": ["تم", "لم يتم"]
}

PREGNANT_COLUMNS = [
    "تاريخ_التسجيل", "اسم_المستخدم", "تاريخ_الزيارة", "الرقم_القومى_للزوجة", "اسم_الزوجة",
    "تاريخ_الميلاد", "السن", "رقم_الموبايل", "الرقم_القومى_للزوج", "اسم_الزوج", "تاريخ_ميلاد_الزوج",
    "مستوى_التعليم", "الوظيفة", "قرابة_بين_الزوجين", "عدد_مرات_الحمل", "عدد_مرات_الولادة",
    "عدد_الايدال_الأحياء", "عمر_أصغر_طفل", "وسيلة_تنظيم_الأسرة_المستخدمة_سابقا", "شهر_الحمل",
    "امراض_مزمنة_ضغط_الدم", "امراض_مزمنة_السكر", "امراض_مزمنة_الغدة",
    "امراض_مزمنة_الأنيميا", "مكملات_قبل_حمض_الفوليك", "مكملات_قبل_الحديد", "مكملات_قبل_الكالسيوم",
    "مكملات_اثناء_حمض_الفوليك", "مكملات_اثناء_الحديد", "مكملات_اثناء_الكالسيوم",
    "التغذية_السليمة", "المكملات_الغذائية", "التمرينات_الرياضية", "قسط_من_النوم_والراحة",
    "المتابعة_الدورية_للحمل", "التحذير_من_الأدوية",
    "المتاعب_البسيطة", "المتاعب_في_الشهور_الأخيرة", "علامات_الخطر_أثناء_الحمل",
    "مشاكل_الولادة_المبكرة", "حركة_الجنين",
    "تغير_لون_الجلد", "ارتداء_الملابس_الفضفاضة",
    "الاستعداد_للولادة", "علامات_الولادة", "مميزات_الولادة_الطبيعية",
    "الساعة_الذهبية_الأولى", "ملامسة_الجلد_للجلد", "البداية_المبكرة_للرضاعة",
    "الرضاعة_الطبيعية_المطلقة", "اهمية_المباعدة", "وسائل_تنظيم_الأسرة", "استخدام_وسيلة_بعد_الولادة",
    "التطور_العصبي_والنفسي"
]

CHILD_COLUMNS = [
    "تاريخ_التسجيل", "اسم_المستخدم", "تاريخ_اول_زيارة", "رقم_الحالة", "اسم_الام", "الرقم_القومى_للام",
    "رقم_الموبايل_للام", "تاريخ_ميلاد_للام", "مستوى_التعليم_للام", "عدد_الاطفال_لدى_الام",
    "المدة_بين_اخر_حملين", "الوظيفة_للام", "الرقم_القومى_للاب", "رقم_الموبايل_للاب", "اسم_الاب",
    "مستوى_التعليم_للاب", "اسم_الطفل", "تاريخ_الميلاد_للطفل", "العمر_الحالى_للطفل",
    "العمر_الرحمى_للطفل", "مكان_المتابعة_وحدة", "مكان_المتابعة_مستشفى",
    "مكان_المتابعة_اخرى", "مصدر_الاحالة_مستشفى", "مصدر_الاحالة_عيادة",
    "مصدر_الاحالة_تطعيمات", "مصدر_الاحالة_نصيحة", "نوع_الولادة", "مكان_الولادة",
    "وزن_الطفل", "طول_الطفل", "مقاس_راس_الطفل", "دخول_الحضانة",
    "سبب_دخول_الحضانة", "مدة_البقاء_فى_الحضانة", "ملامسة_الجلد_الساعة_الذهبية",
    "الرضاعة_الساعة_الذهبية", "موعد_الزيارة", "تاريخ_الزيارة", "رضاعة_طبيعية_مطلقة",
    "رضاعة_مع_سوائل", "رضاعة_مع_صناعي", "رضاعة_لبن_صناعي", "الوزن",
    "الطول", "محيط_الرأس", "فوائد_الرضاعة",
    "كفاية_اللبن", "فيتامين_د", "رعاية_السرة",
    "البطاقة_الصحية", "التطعيمات",
    "التغذية_للام", "علامات_الخطورة", "النمو_الحركي",
    "التطور_الإدراكي", "التطور_اللغوي", "التربية_الإيجابية", "الأنشطة_التحفيزية",
    "التغذية_التكميلية", "جرعة_الحديد",
    "أهمية_الوسيلة", "موقف_الوسيلة",
    "الحمل_الجديد", "الخدمات_الغير_ملباه", "تحويل_تنظيم_الاسره", "تخطيط_الزيارة"
]

YES_NO_CHECKBOX_FIELDS = [
    "مكان_المتابعة_وحدة", "مكان_المتابعة_مستشفى", "مكان_المتابعة_اخرى",
    "مصدر_الاحالة_مستشفى", "مصدر_الاحالة_عيادة",
    "مصدر_الاحالة_تطعيمات", "مصدر_الاحالة_نصيحة"
]

# ==================== دالة حقل النص مع الإدخال الصوتي ====================
def text_input_with_voice(label, key_prefix, value=""):
    col_f1, col_f2 = st.columns([5, 1])
    with col_f1:
        val = st.text_input(label, value=value, key=f"{key_prefix}_txt")
    with col_f2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        audio = mic_recorder(
            start_prompt="🎤",
            stop_prompt="⏹️",
            key=f"{key_prefix}_mic"
        )
    if audio and "bytes" in audio:
        st.toast(f"تم تسجيل الصوت بنجاح لـ: {label}", icon="🎙️")
    return val

# ==================== دوال الحسابات والنمو والزيارات ====================
def calculate_birth_head_circumference(weight_kg, length_cm):
    try:
        w = float(weight_kg)
        l = float(length_cm)
        if w > 0 and l > 0:
            head_circ = (l / 2.0) + 9.5 + ((w - 3.3) * 0.8)
            return str(round(head_circ, 1))
    except (ValueError, TypeError):
        pass
    return ""

def calculate_current_head_circumference(age_months_val, birth_w, birth_l, current_w, current_l):
    try:
        age_m = 0.0
        if isinstance(age_months_val, str):
            clean_str = age_months_val.replace("شهر", "").replace("أسبوع", "").replace("يوم", "").strip()
            if clean_str:
                age_m = float(clean_str)
                if "أسبوع" in age_months_val:
                    age_m = age_m / 4.33
                elif "يوم" in age_months_val:
                    age_m = age_m / 30.44
        else:
            age_m = float(age_months_val)

        base_hc = float(calculate_birth_head_circumference(birth_w, birth_l)) if birth_w and birth_l else 34.5

        if age_m <= 3:
            growth = age_m * 2.0
        elif age_m <= 6:
            growth = (3 * 2.0) + ((age_m - 3) * 1.0)
        elif age_m <= 12:
            growth = (3 * 2.0) + (3 * 1.0) + ((age_m - 6) * 0.5)
        else:
            growth = (3 * 2.0) + (3 * 1.0) + (6 * 0.5) + ((age_m - 12) * 0.15)

        cw = float(current_w) if current_w else 0.0
        bw = float(birth_w) if birth_w else 0.0
        weight_factor = ((cw - bw) * 0.1) if (cw > 0 and bw > 0) else 0.0

        current_hc = base_hc + growth + weight_factor
        return str(round(current_hc, 1))
    except (ValueError, TypeError):
        pass
    return ""

def calculate_motor_development(age_months_val, birth_w, current_w):
    try:
        age_m = 0.0
        if isinstance(age_months_val, str):
            clean_str = age_months_val.replace("شهر", "").replace("أسبوع", "").replace("يوم", "").strip()
            if clean_str:
                age_m = float(clean_str)
                if "أسبوع" in age_months_val:
                    age_m = age_m / 4.33
                elif "يوم" in age_months_val:
                    age_m = age_m / 30.44
        else:
            age_m = float(age_months_val)

        cw = float(current_w) if current_w else 0.0
        bw = float(birth_w) if birth_w else 0.0

        if age_m <= 0 or cw <= 0 or bw <= 0:
            return "طبيعى"

        expected_current_weight = bw + (age_m * 0.6) if age_m <= 6 else bw + (6 * 0.6) + ((age_m - 6) * 0.4)
        
        ratio = cw / expected_current_weight
        if ratio < 0.80:
            return "متاخر"
        elif ratio > 1.25:
            return "متقدم"
        else:
            return "طبيعى"
    except Exception:
        return "طبيعى"

def get_best_visit_schedule(age_months_val):
    try:
        if isinstance(age_months_val, str):
            clean_str = age_months_val.replace("شهر", "").replace("أسبوع", "").replace("يوم", "").strip()
            if not clean_str:
                return VISIT_SCHEDULE_OPTIONS[0]
            age_m = float(clean_str)
            if "أسبوع" in age_months_val:
                age_m = age_m / 4.33
            elif "يوم" in age_months_val:
                age_m = age_m / 30.44
        else:
            age_m = float(age_months_val)

        closest_option = VISIT_SCHEDULE_OPTIONS[0]
        min_diff = float('inf')

        for option in VISIT_SCHEDULE_OPTIONS:
            target_m = VISIT_MONTHS_MAP[option]
            diff = abs(target_m - age_m)
            if diff < min_diff:
                min_diff = diff
                closest_option = option
        return closest_option
    except (ValueError, TypeError):
        return VISIT_SCHEDULE_OPTIONS[0]

def calculate_next_visit_date(current_visit_date_str, current_schedule_option):
    try:
        if not current_visit_date_str or current_schedule_option not in VISIT_SCHEDULE_OPTIONS:
            return ""

        current_idx = VISIT_SCHEDULE_OPTIONS.index(current_schedule_option)
        if current_idx >= len(VISIT_SCHEDULE_OPTIONS) - 1:
            return "مكتمل جميع الزيارات"

        next_schedule_option = VISIT_SCHEDULE_OPTIONS[current_idx + 1]
        
        curr_m = VISIT_MONTHS_MAP[current_schedule_option]
        next_m = VISIT_MONTHS_MAP[next_schedule_option]
        diff_months = next_m - curr_m

        base_date = datetime.datetime.strptime(current_visit_date_str, "%Y-%m-%d").date()
        days_to_add = int(round(diff_months * 30.44))
        next_date = base_date + datetime.timedelta(days=days_to_add)

        return f"{next_date.strftime('%Y-%m-%d')} ({next_schedule_option})"
    except Exception:
        return ""

def clean_digits(val, max_len=None):
    if not val:
        return ""
    digits = "".join(filter(str.isdigit, str(val)))
    if max_len:
        digits = digits[:max_len]
    return digits

def format_text_for_excel(val):
    if not val:
        return ""
    clean_val = str(val).strip()
    return f"'{clean_val}"

def parse_national_id(nat_id):
    clean_id = clean_digits(nat_id, 14)
    if len(clean_id) == 14:
        century_code = int(clean_id[0])
        year_digits = int(clean_id[1:3])
        month = int(clean_id[3:5])
        day = int(clean_id[5:7])
        
        if century_code == 2:
            century = 1900
        elif century_code == 3:
            century = 2000
        else:
            century = 1900
            
        birth_year = century + year_digits
        try:
            birth_date = datetime.date(birth_year, month, day)
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return str(birth_date), str(age)
        except ValueError:
            return "", ""
    return "", ""

# ==================== دالة جلب البيانات ====================
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

# ==================== تسجيل الدخول ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🌸 برنامج بودى للمشورة الأسرية 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>تسجيل الدخول للنظام</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_list = list(DEFAULT_USERS.keys())
        selected_username = st.selectbox("اختر اسم المستخدم (Username)", user_list, format_func=lambda x: f"{x} ({DEFAULT_USERS[x]['name']})")
        password_input = st.text_input("كلمة المرور (Password)", type="password")

        if st.button("تسجيل الدخول", use_container_width=True):
            if DEFAULT_USERS[selected_username]["pass"] == password_input:
                st.session_state.logged_in = True
                st.session_state.username = selected_username
                st.session_state.name = DEFAULT_USERS[selected_username]["name"]
                st.session_state.role = DEFAULT_USERS[selected_username]["role"]
                st.success(f"مرحباً بكِ {st.session_state.name} ✨")
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة!")
    st.stop()

# ==================== القائمة الجانبية ====================
st.sidebar.markdown(f"### 👩‍⚕️ أهلاً بكِ، {st.session_state.name}")
st.sidebar.markdown("---")

menu_options = ["سجل الحوامل", "سجل الأطفال", "استعراض البيانات والداشبورد", "استيراد البيانات (Excel/CSV)"]
if st.session_state.role == "admin":
    menu_options.append("إدارة المستخدمين")

menu = st.sidebar.selectbox("📋 اختر القسم المطلوب:", menu_options)

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

today_str = datetime.date.today().strftime("%Y-%m-%d")

# ==================== 1. سجل الحوامل ====================
if menu == "سجل الحوامل":
    st.markdown("<h2>🤰 سجل المشورة الأسرية للسيدات الحوامل</h2>", unsafe_allow_html=True)
    
    for col in PREGNANT_COLUMNS:
        if f"p_{col}" not in st.session_state:
            st.session_state[f"p_{col}"] = today_str if col == "تاريخ_الزيارة" else ""

    raw_id = st.text_input("الرقم القومى للزوجة", key="p_الرقم_القومى_للزوجة_input")
    clean_p_id = clean_digits(raw_id, 14)
    if clean_p_id:
        st.session_state["p_الرقم_القومى_للزوجة"] = clean_p_id
        if len(clean_p_id) == 14:
            b_date, age = parse_national_id(clean_p_id)
            if b_date: st.session_state["p_تاريخ_الميلاد"] = b_date
            if age: st.session_state["p_السن"] = age
            fetch_auto_data_from_supabase("pregnant_records", "الرقم_القومى_للزوجة", clean_p_id, "p")

    for col_name in PREGNANT_COLUMNS:
        if col_name in ["تاريخ_التسجيل", "اسم_المستخدم", "الرقم_القومى_للزوجة"]:
            continue

        if col_name in DROPDOWN_OPTIONS:
            opts = DROPDOWN_OPTIONS[col_name]
            st.markdown(f"**{col_name.replace('_', ' ')}**")
            curr = st.session_state.get(f"p_{col_name}", opts[0])
            st.session_state[f"p_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"p_radio_{col_name}", horizontal=True
            )
        else:
            if col_name == "الرقم_القومى_للزوج":
                raw_husband_id = st.text_input(col_name.replace('_', ' '), key=f"p_{col_name}_raw")
                clean_h_id = clean_digits(raw_husband_id, 14)
                st.session_state[f"p_{col_name}"] = clean_h_id
                if len(clean_h_id) == 14:
                    hb_date, _ = parse_national_id(clean_h_id)
                    if hb_date: st.session_state["p_تاريخ_ميلاد_الزوج"] = hb_date
            elif col_name == "رقم_الموبايل":
                raw_mob = st.text_input(col_name.replace('_', ' '), key=f"p_{col_name}_raw")
                st.session_state[f"p_{col_name}"] = clean_digits(raw_mob, 11)
            elif col_name in ["تاريخ_الميلاد", "السن", "تاريخ_ميلاد_الزوج"]:
                st.text_input(f"{col_name.replace('_', ' ')} [تلقائي]", key=f"p_{col_name}")
            else:
                val_text = text_input_with_voice(col_name.replace('_', ' '), f"p_text_{col_name}")
                st.session_state[f"p_{col_name}"] = val_text

    if st.button("💾 حفظ بيانات الحامل في Supabase", use_container_width=True):
        final_p_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ_التسجيل":
                final_p_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم_المستخدم":
                final_p_data[col] = st.session_state.name
            else:
                val = st.session_state.get(f"p_{col}", "")
                if "الرقم_القومى" in col or "رقم_الموبايل" in col:
                    val = format_text_for_excel(val)
                final_p_data[col] = val

        try:
            supabase.table("pregnant_records").insert(final_p_data).execute()
            st.success("تم حفظ بيانات الحامل في Supabase بنجاح! ✨")
            clear_form_state("p")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ: {e}")

# ==================== 2. سجل الأطفال ====================
elif menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    
    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            st.session_state[f"c_{col}"] = today_str if col in ["تاريخ_الزيارة", "تاريخ_اول_زيارة"] else ""

    # حقل الرقم القومي للأم مع التحليل والتحديث الفوري لتاريخ الميلاد
    raw_nat_id_mom = st.text_input("الرقم القومى للام", key="c_الرقم_القومى_للام_input")
    clean_c_id = clean_digits(raw_nat_id_mom, 14)
    
    if clean_c_id:
        st.session_state["c_الرقم_القومى_للام"] = clean_c_id
        if len(clean_c_id) == 14:
            b_mom, _ = parse_national_id(clean_c_id)
            if b_mom: 
                st.session_state["c_تاريخ_ميلاد_للام"] = b_mom
            fetch_auto_data_from_supabase("children_records", "الرقم_القومى_للام", clean_c_id, "c")
    else:
        if not raw_nat_id_mom:
            st.session_state["c_تاريخ_ميلاد_للام"] = ""

    auto_birth_hc = calculate_birth_head_circumference(
        st.session_state.get("c_وزن_الطفل"),
        st.session_state.get("c_طول_الطفل")
    )
    if auto_birth_hc:
        st.session_state["c_مقاس_راس_الطفل"] = auto_birth_hc

    auto_curr_hc = calculate_current_head_circumference(
        st.session_state.get("c_العمر_الحالى_للطفل"),
        st.session_state.get("c_وزن_الطفل"),
        st.session_state.get("c_طول_الطفل"),
        st.session_state.get("c_الوزن"),
        st.session_state.get("c_الطول")
    )
    if auto_curr_hc:
        st.session_state["c_محيط_الرأس"] = auto_curr_hc

    auto_motor_dev = calculate_motor_development(
        st.session_state.get("c_العمر_الحالى_للطفل"),
        st.session_state.get("c_وزن_الطفل"),
        st.session_state.get("c_الوزن")
    )
    if auto_motor_dev:
        st.session_state["c_النمو_الحركي"] = auto_motor_dev

    auto_visit_schedule = get_best_visit_schedule(st.session_state.get("c_العمر_الحالى_للطفل", 0))
    if not st.session_state.get("c_موعد_الزيارة") or st.session_state.get("c_auto_visit_set") != auto_visit_schedule:
        st.session_state["c_موعد_الزيارة"] = auto_visit_schedule
        st.session_state["c_auto_visit_set"] = auto_visit_schedule

    auto_next_visit = calculate_next_visit_date(
        st.session_state.get("c_تاريخ_الزيارة", today_str),
        st.session_state.get("c_موعد_الزيارة")
    )
    st.session_state["c_تخطيط_الزيارة"] = auto_next_visit

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ_التسجيل", "اسم_المستخدم", "الرقم_القومى_للام"]:
            continue

        elif col_name == "نوع_الولادة":
            st.markdown(f"**{col_name.replace('_', ' ')}**")
            curr = st.session_state.get(f"c_{col_name}", "")
            c1, c2, c3 = st.columns(3)
            with c1: chk_nat = st.checkbox("طبيعى", value=(curr == "طبيعى"), key="c_birth_nat")
            with c2: chk_ces = st.checkbox("قيصرى", value=(curr == "قيصرى"), key="c_birth_ces")
            with c3: chk_none = st.checkbox("لا يوجد", value=(curr in ["لا يوجد", ""]), key="c_birth_none")
            st.session_state[f"c_{col_name}"] = "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")

        elif col_name == "رضاعة_طبيعية_مطلقة":
            st.markdown(f"**{col_name.replace('_', ' ')}**")
            curr = st.session_state.get(f"c_{col_name}", "")
            c1, c2, c3 = st.columns(3)
            with c1: chk3 = st.checkbox("3 شهور", value=(curr == "3 شهور"), key="c_bf_3")
            with c2: chk4 = st.checkbox("4 شهور", value=(curr == "4 شهور"), key="c_bf_4")
            with c3: chk6 = st.checkbox("6 شهور", value=(curr == "6 شهور"), key="c_bf_6")
            st.session_state[f"c_{col_name}"] = "3 شهور" if chk3 else ("4 شهور" if chk4 else ("6 شهور" if chk6 else ""))

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            chk = st.checkbox(col_name.replace('_', ' '), value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if chk else ""

        elif col_name == "موعد_الزيارة":
            st.markdown(f"**{col_name.replace('_', ' ')} [مُقترح آلياً 🎯]**")
            curr_val = st.session_state.get(f"c_{col_name}", VISIT_SCHEDULE_OPTIONS[0])
            st.session_state[f"c_{col_name}"] = st.selectbox(
                "اختر موعد الزيارة", VISIT_SCHEDULE_OPTIONS,
                index=VISIT_SCHEDULE_OPTIONS.index(curr_val) if curr_val in VISIT_SCHEDULE_OPTIONS else 0,
                key="c_select_موعد_الزيارة"
            )

        elif col_name in ["مقاس_راس_الطفل", "محيط_الرأس", "تخطيط_الزيارة"]:
            st.text_input(
                f"{col_name.replace('_', ' ')} [حساب تلقائي ⚙️]",
                value=st.session_state.get(f"c_{col_name}", ""),
                key=f"c_auto_{col_name}",
                disabled=True
            )

        elif col_name == "تاريخ_ميلاد_للام":
            st.text_input(
                f"{col_name.replace('_', ' ')} [تلقائي ⚙️]",
                value=st.session_state.get(f"c_{col_name}", ""),
                key=f"c_auto_{col_name}",
                disabled=True
            )

        elif col_name == "النمو_الحركي":
            st.markdown(f"**{col_name.replace('_', ' ')} [تحديد آلي بناءً على القياسات ⚙️]**")
            opts = DROPDOWN_OPTIONS[col_name]
            curr = st.session_state.get(f"c_{col_name}", opts[0])
            st.session_state[f"c_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"c_radio_{col_name}", horizontal=True
            )

        elif col_name in DROPDOWN_OPTIONS:
            opts = DROPDOWN_OPTIONS[col_name]
            st.markdown(f"**{col_name.replace('_', ' ')}**")
            curr = st.session_state.get(f"c_{col_name}", opts[0])
            st.session_state[f"c_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"c_radio_{col_name}", horizontal=True
            )

        else:
            if col_name in ["الرقم_القومى_للاب"]:
                raw_val = st.text_input(col_name.replace('_', ' '), key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم_الموبايل_للام", "رقم_الموبايل_للاب"]:
                raw_val = st.text_input(col_name.replace('_', ' '), key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name == "تاريخ_الميلاد_للطفل":
                def_date = datetime.date.today()
                if st.session_state.get(f"c_{col_name}"):
                    try: def_date = datetime.datetime.strptime(st.session_state[f"c_{col_name}"], "%Y-%m-%d").date()
                    except: pass
                chosen_date = st.date_input(col_name.replace('_', ' '), value=def_date, key=f"c_date_{col_name}")
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                delta_days = (datetime.date.today() - chosen_date).days
                if delta_days >= 0:
                    if delta_days < 7: age_str = f"{delta_days} يوم"
                    elif delta_days < 30: age_str = f"{round(delta_days/7)} أسبوع"
                    else: age_str = f"{round(delta_days/30.44, 1)} شهر"
                    st.session_state["c_العمر_الحالى_للطفل"] = age_str
                    st.session_state["c_العمر_الرحمى_للطفل"] = f"{max(24, min(42, 40 - max(0, round((280 - delta_days) / 7))))} أسبوع"
            else:
                val_text = text_input_with_voice(col_name.replace('_', ' '), f"c_text_{col_name}")
                st.session_state[f"c_{col_name}"] = val_text

    current_motor_status = st.session_state.get("c_النمو_الحركي", "")
    if current_motor_status == "متاخر":
        st.markdown(
            """
            <div style="background-color: #FFCDD2; color: #B71C1C; padding: 15px; border-radius: 8px; border: 2px solid #F44336; margin-bottom: 15px; font-weight: bold; text-align: center;">
                ⚠️ تحذير هام: معدل النمو والتطور الحركي لهذا الطفل (متاخر)! يرجى اتخاذ التدابير اللازمة قبل الحفظ.
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("💾 حفظ بيانات الطفل في Supabase", use_container_width=True):
        final_c_data = {}
        for col in CHILD_COLUMNS:
            if col == "تاريخ_التسجيل":
                final_c_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم_المستخدم":
                final_c_data[col] = st.session_state.name
            else:
                val = st.session_state.get(f"c_{col}", "")
                if "الرقم_القومى" in col or "رقم_الموبايل" in col:
                    val = format_text_for_excel(val)
                final_c_data[col] = val

        try:
            supabase.table("children_records").insert(final_c_data).execute()
            st.success("تم حفظ بيانات الطفل في Supabase بنجاح! ✨")
            clear_form_state("c")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ: {e}")

# ==================== 3. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
    st.markdown("<h2>📊 لوحة المؤشرات واستعراض البيانات</h2>", unsafe_allow_html=True)
    
    record_type = st.radio("اختر السجل للاستعراض:", ["سجل الحوامل", "سجل الأطفال"], horizontal=True)
    db_table_name = "pregnant_records" if record_type == "سجل الحوامل" else "children_records"

    try:
        res = supabase.table(db_table_name).select("*").execute()
        df_view = pd.DataFrame(res.data) if res.data else pd.DataFrame()

        target_cols = PREGNANT_COLUMNS if record_type == "سجل الحوامل" else CHILD_COLUMNS
        
        for c in target_cols:
            if c not in df_view.columns:
                df_view[c] = ""
        df_view = df_view[target_cols]

        st.dataframe(df_view, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_view.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 تحميل البيانات كملف Excel",
            data=excel_data,
            file_name=f"{db_table_name}_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")

# ==================== 4. استيراد البيانات ====================
elif menu == "استيراد البيانات (Excel/CSV)":
    st.markdown("<h2>📂 استيراد البيانات من ملفات Excel أو CSV</h2>", unsafe_allow_html=True)
    import_type = st.radio("اختر جدول الاستيراد:", ["سجل الحوامل", "سجل الأطفال"], horizontal=True)
    db_table_name = "pregnant_records" if import_type == "سجل الحوامل" else "children_records"
    
    uploaded_file = st.file_uploader("اختر الملف", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_import = pd.read_csv(uploaded_file)
            else:
                df_import = pd.read_excel(uploaded_file)
            
            st.write("معاينة البيانات المستوردة:", df_import.head())
            if st.button("رفع وحفظ البيانات في قاعدة البيانات"):
                records_to_insert = df_import.to_dict(orient="records")
                for rec in records_to_insert:
                    cleaned_rec = {str(k): (str(v) if pd.notna(v) else "") for k, v in rec.items()}
                    supabase.table(db_table_name).insert(cleaned_rec).execute()
                st.success("تم رفع واستيراد البيانات بنجاح إلى Supabase! 🚀")
        except Exception as e:
            st.error(f"حدث خطأ أثناء استيراد الملف: {e}")

# ==================== 5. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
    st.markdown("<h2>⚙️ إدارة المستخدمين وصلاحيات النظام</h2>", unsafe_allow_html=True)
    st.info("هنا يمكنك مراجعة وتعديل مستخدمي النظام المعتمدين.")
    
    users_data = []
    for username, info in DEFAULT_USERS.items():
        users_data.append({
            "اسم المستخدم": username,
            "الاسم الظاهر": info["name"],
            "الصلاحية": info["role"]
        })
    df_users = pd.DataFrame(users_data)
    st.dataframe(df_users, use_container_width=True)
