import datetime
import math
import os
import io
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==================== إعدادات Supabase ====================
SUPABASE_URL = "https://ndxzbpmdvqjinpjrbytd.supabase.co"
SUPABASE_KEY = "sb_publishable_ubwXt_RivsCvAT6nFE0hoQ_3DD5aYOK"
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
    "مستوى التعليم": ["امى", "يجيد القراءة", "مؤهل متوسط", "فوق متوسط", "مؤهل عالى"],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة بين الزوجين": ["نعم", "لا"],
    "وسيلة تنظيم الأسرة المستخدمة سابقا": ["توجد", "مرغوب", "غير مرغوب"],
    "شهر الحمل": [f"الشهر {x}" for x in ["الاول", "الثانى", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع"]],
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
        "انخفاض وزن الطفل.", "احتياج الطفل لأدوية محددة بهذا الوقت.",
        "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.", "ارتفاع درجة حرارة جسم الرضيع.",
        "تعطل العمليات الحيوية بجسم الطفل.", "انخفاض معدل الجلوكوز في دم الطفل.",
        "معاناة الرضيع مشكلات في الجهاز الهضمي.", "إصابة الطفل بعدوى في الدم.",
        "إصابة الطفل بالصفراء.", "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.",
        "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي."
    ],
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
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النوم": ["تم", "لم يتم"],
    "أهمية الإلتزام بتطعيمات الطفل": ["تم", "لم يتم"],
    "التغذية الصحية للأم المرضعة": ["تم", "لم يتم"],
    "كيفية التعرف على علامات الخطورة": ["تم", "لم يتم"],
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع": ["تم", "لم يتم"],
    "كفاية اللبن وكمية البراز": ["تم", "لم يتم"]
}

PREGNANT_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "تاريخ الزيارة", "الرقم القومى للزوجة", "اسم الزوجة",
    "تاريخ الميلاد", "السن", "رقم الموبايل", "الرقم القومى للزوج", "اسم الزوج", "تاريخ ميلاد الزوج",
    "مستوى التعليم", "الوظيفة", "قرابة بين الزوجين", "عدد مرات الحمل", "عدد مرات الولادة",
    "عدد الاطفال الأحياء", "عمر أصغر طفل", "وسيلة تنظيم الأسرة المستخدمة سابقا", "شهر الحمل",
    "أمراض مزمنة: إرتفاع ضغط الدم", "أمراض مزمنة: السكر", "أمراض مزمنة: إضطرابات الغدة",
    "أمراض مزمنة: الأنيميا", 'مكملات "قبل": حمض الفوليك', 'مكملات "قبل": الحديد', 'مكملات "قبل": الكالسيوم',
    'مكملات "أثناء": حمض الفوليك', 'مكملات "أثناء": الحديد', 'مكملات "أثناء": الكالسيوم',
    "التغذية السليمة", "المكملات الغذائية", "التمرينات الرياضية", "قسط من النوم والراحة",
    "المتابعة الدورية للحمل", "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة",
    "المتاعب البسيطة في الشهور الأولى", "المتاعب في الشهور الأخيرة", "علامات الخطر أثناء الحمل",
    "مشاكل الولادة المبكرة وكيفية تجنبها", "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين",
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي", "إرتداء الملابس الفضفاضة المريحة",
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ", "علامات الولادة", "مميزات الولادة الطبيعية",
    "الساعة الذهبية الأولى", "ملامسة الجلد للجلد", "البداية المبكرة للرضاعة الطبيعية",
    "الرضاعة الطبيعية المطلقة", "أهمية المباعدة", "وسائل تنظيم الأسرة", "إستخدام وسيلة بعد الولادة مباشرة",
    "التطور العصبي والنفسي للطفل"
]

CHILD_COLUMNS = [
    "تاريخ التسجيل", "اسم المستخدم", "تاريخ اول زيارة", "رقم الحالة", "اسم الام", "الرقم القومى للام",
    "رقم الموبايل للام", "تاريخ ميلاد الام", "مستوى التعليم للام", "عدد الاطفال لدى الام",
    "المدة بين اخر حملين", "الوظيفة للام", "الرقم القومى للاب", "رقم الموبايل للاب", "اسم الاب",
    "مستوى التعليم للاب", "اسم الطفل", "تاريخ الميلاد للطفل", "العمر الحالى للطفل (شهور)",
    "العمر الرحمى للطفل (أسابيع)", "مكان المتابعة (وحدة)", "مكان المتابعة (مستشفى)",
    "مكان المتابعة (اخرى)", "مصدر الاحالة(مستشفى الولادة)", "مصدر الاحالة (عيادة خاصة)",
    "مصدر الاحالة(عيادة التطعيمات)", "مصدر الاحالة(نصيحة)", "نوع الولادة", "مكان الولادة",
    "وزن الطفل عند الولادة", "طول الطفل عند الولادة", "مقاس راس الطفل عند الولادة", "دخول الحضانة",
    "سبب دخول الحضانة", "مدة البقاء فى الحضانة", "ملامسة الجلد فى الساعة الذهبية الأولى",
    "الرضاعة الطبيعية فى الساعة الذهبية الأولى", "موعد الزيارة", "تاريخ الزيارة", "رضاعة طبيعية مطلقة",
    "رضاعة طبيعية مع سوائل وأعشاب", "رضاعة طبيعية مع صناعي", "رضاعة لبن صناعي", "الوزن (كجم)",
    "الطول (سم)", "محيط الرأس (سم)", "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع",
    "كفاية اللبن وكمية البراز", "إعطاء الجرعة اليومية من فيتامين د", "كيفية رعاية السرة والإهتمام بنظافة الطفل",
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النوم", "أهمية الإلتزام بتطعيمات الطفل",
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
    """دالة لحساب معدل النمو والتطور الحركي بناءً على العمر والوزن عند الولادة والوزن الحالي"""
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

        # حساب معدل الزيادة المتوقعة بالوزن شهرياً تقريباً
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

# ==================== دوال المساعدة وتنسيق النصوص ====================
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

def fetch_auto_data_from_supabase(table_name, id_col_name, nat_id_val, prefix):
    clean_id = clean_digits(nat_id_val, 14)
    if len(clean_id) == 14 and st.session_state.get(f"{prefix}_last_fetched_id") != clean_id:
        try:
            response = supabase.table(table_name).select("*").eq(id_col_name, clean_id).execute()
            if response.data:
                latest_data = response.data[-1]
                cols = PREGNANT_COLUMNS if prefix == "p" else CHILD_COLUMNS
                for col in cols:
                    if col in latest_data and latest_data[col]:
                        st.session_state[f"{prefix}_{col}"] = str(latest_data[col]).replace("'", "")
                st.session_state[f"{prefix}_last_fetched_id"] = clean_id
                st.toast("⚡ تم استدعاء بيانات الحساب المسجل تلقائياً من Supabase!", icon="✨")
        except Exception as e:
            print(f"Fetch Error: {e}")

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
            st.session_state[f"p_{col}"] = today_str if col == "تاريخ الزيارة" else ""

    raw_id = st.text_input("الرقم القومى للزوجة", key="p_الرقم القومى للزوجة_input")
    clean_p_id = clean_digits(raw_id, 14)
    if clean_p_id:
        st.session_state["p_الرقم القومى للزوجة"] = clean_p_id
        if len(clean_p_id) == 14:
            b_date, age = parse_national_id(clean_p_id)
            if b_date: st.session_state["p_تاريخ الميلاد"] = b_date
            if age: st.session_state["p_السن"] = age
            fetch_auto_data_from_supabase("pregnant_records", "الرقم القومى للزوجة", clean_p_id, "p")

    for col_name in PREGNANT_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للزوجة"]:
            continue

        if col_name in DROPDOWN_OPTIONS:
            opts = DROPDOWN_OPTIONS[col_name]
            st.markdown(f"**{col_name}**")
            curr = st.session_state.get(f"p_{col_name}", opts[0])
            st.session_state[f"p_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"p_radio_{col_name}", horizontal=True
            )
        else:
            if col_name == "الرقم القومى للزوج":
                raw_husband_id = st.text_input(col_name, key=f"p_{col_name}_raw")
                clean_h_id = clean_digits(raw_husband_id, 14)
                st.session_state[f"p_{col_name}"] = clean_h_id
                if len(clean_h_id) == 14:
                    hb_date, _ = parse_national_id(clean_h_id)
                    if hb_date: st.session_state["p_تاريخ ميلاد الزوج"] = hb_date
            elif col_name == "رقم الموبايل":
                raw_mob = st.text_input(col_name, key=f"p_{col_name}_raw")
                st.session_state[f"p_{col_name}"] = clean_digits(raw_mob, 11)
            elif col_name in ["تاريخ الميلاد", "السن", "تاريخ ميلاد الزوج"]:
                st.text_input(f"{col_name} [تلقائي]", key=f"p_{col_name}")
            else:
                val_text = st.text_input(col_name, key=f"p_text_{col_name}")
                st.session_state[f"p_{col_name}"] = val_text

    if st.button("💾 حفظ بيانات الحامل في Supabase", use_container_width=True):
        final_p_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ التسجيل":
                final_p_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_p_data[col] = st.session_state.name
            else:
                val = st.session_state.get(f"p_{col}", "")
                if "الرقم القومى" in col or "رقم الموبايل" in col:
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
            st.session_state[f"c_{col}"] = today_str if col in ["تاريخ الزيارة", "تاريخ اول زيارة"] else ""

    raw_nat_id_mom = st.text_input("الرقم القومى للام (اختياري)", key="c_الرقم القومى للام_input")
    clean_c_id = clean_digits(raw_nat_id_mom, 14)
    if clean_c_id:
        st.session_state["c_الرقم القومى للام"] = clean_c_id
        if len(clean_c_id) == 14:
            b_mom, _ = parse_national_id(clean_c_id)
            if b_mom: st.session_state["c_تاريخ ميلاد الام"] = b_mom
            fetch_auto_data_from_supabase("children_records", "الرقم القومى للام", clean_c_id, "c")

    auto_birth_hc = calculate_birth_head_circumference(
        st.session_state.get("c_وزن الطفل عند الولادة"),
        st.session_state.get("c_طول الطفل عند الولادة")
    )
    if auto_birth_hc:
        st.session_state["c_مقاس راس الطفل عند الولادة"] = auto_birth_hc

    auto_curr_hc = calculate_current_head_circumference(
        st.session_state.get("c_العمر الحالى للطفل (شهور)"),
        st.session_state.get("c_وزن الطفل عند الولادة"),
        st.session_state.get("c_طول الطفل عند الولادة"),
        st.session_state.get("c_الوزن (كجم)"),
        st.session_state.get("c_الطول (سم)")
    )
    if auto_curr_hc:
        st.session_state["c_محيط الرأس (سم)"] = auto_curr_hc

    # الحساب التلقائي لمعدل النمو والتطور الحركي
    auto_motor_dev = calculate_motor_development(
        st.session_state.get("c_العمر الحالى للطفل (شهور)"),
        st.session_state.get("c_وزن الطفل عند الولادة"),
        st.session_state.get("c_الوزن (كجم)")
    )
    if auto_motor_dev:
        st.session_state["c_النمو والتطور الحركي"] = auto_motor_dev

    auto_visit_schedule = get_best_visit_schedule(st.session_state.get("c_العمر الحالى للطفل (شهور)", 0))
    if not st.session_state.get("c_موعد الزيارة") or st.session_state.get("c_auto_visit_set") != auto_visit_schedule:
        st.session_state["c_موعد الزيارة"] = auto_visit_schedule
        st.session_state["c_auto_visit_set"] = auto_visit_schedule

    auto_next_visit = calculate_next_visit_date(
        st.session_state.get("c_تاريخ الزيارة", today_str),
        st.session_state.get("c_موعد الزيارة")
    )
    st.session_state["c_تخطيط الزيارة القادمة"] = auto_next_visit

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
            continue

        elif col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            curr = st.session_state.get(f"c_{col_name}", "")
            c1, c2, c3 = st.columns(3)
            with c1: chk_nat = st.checkbox("طبيعى", value=(curr == "طبيعى"), key="c_birth_nat")
            with c2: chk_ces = st.checkbox("قيصرى", value=(curr == "قيصرى"), key="c_birth_ces")
            with c3: chk_none = st.checkbox("لا يوجد", value=(curr in ["لا يوجد", ""]), key="c_birth_none")
            st.session_state[f"c_{col_name}"] = "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")

        elif col_name == "رضاعة طبيعية مطلقة":
            st.markdown(f"**{col_name}**")
            curr = st.session_state.get(f"c_{col_name}", "")
            c1, c2, c3 = st.columns(3)
            with c1: chk3 = st.checkbox("3 شهور", value=(curr == "3 شهور"), key="c_bf_3")
            with c2: chk4 = st.checkbox("4 شهور", value=(curr == "4 شهور"), key="c_bf_4")
            with c3: chk6 = st.checkbox("6 شهور", value=(curr == "6 شهور"), key="c_bf_6")
            st.session_state[f"c_{col_name}"] = "3 شهور" if chk3 else ("4 شهور" if chk4 else ("6 شهور" if chk6 else ""))

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            chk = st.checkbox(col_name, value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if chk else ""

        elif col_name == "موعد الزيارة":
            st.markdown(f"**{col_name} [مُقترح آلياً 🎯]**")
            curr_val = st.session_state.get(f"c_{col_name}", VISIT_SCHEDULE_OPTIONS[0])
            st.session_state[f"c_{col_name}"] = st.selectbox(
                "اختر موعد الزيارة", VISIT_SCHEDULE_OPTIONS,
                index=VISIT_SCHEDULE_OPTIONS.index(curr_val) if curr_val in VISIT_SCHEDULE_OPTIONS else 0,
                key="c_select_موعد الزيارة"
            )

        elif col_name in ["مقاس راس الطفل عند الولادة", "محيط الرأس (سم)", "تخطيط الزيارة القادمة"]:
            st.text_input(
                f"{col_name} [حساب تلقائي ⚙️]",
                value=st.session_state.get(f"c_{col_name}", ""),
                key=f"c_auto_{col_name}",
                disabled=True
            )

        elif col_name == "النمو والتطور الحركي":
            st.markdown(f"**{col_name} [تحديد آلي بناءً على القياسات ⚙️]**")
            opts = DROPDOWN_OPTIONS[col_name]
            curr = st.session_state.get(f"c_{col_name}", opts[0])
            st.session_state[f"c_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"c_radio_{col_name}", horizontal=True
            )

        elif col_name in DROPDOWN_OPTIONS:
            opts = DROPDOWN_OPTIONS[col_name]
            st.markdown(f"**{col_name}**")
            curr = st.session_state.get(f"c_{col_name}", opts[0])
            st.session_state[f"c_{col_name}"] = st.radio(
                f"اختر {col_name}", opts, index=(opts.index(curr) if curr in opts else 0),
                key=f"c_radio_{col_name}", horizontal=True
            )

        else:
            if col_name in ["الرقم القومى للام", "الرقم القومى للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم الموبايل للام", "رقم الموبايل للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name == "تاريخ الميلاد للطفل":
                def_date = datetime.date.today()
                if st.session_state.get(f"c_{col_name}"):
                    try: def_date = datetime.datetime.strptime(st.session_state[f"c_{col_name}"], "%Y-%m-%d").date()
                    except: pass
                chosen_date = st.date_input(col_name, value=def_date, key=f"c_date_{col_name}")
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                delta_days = (datetime.date.today() - chosen_date).days
                if delta_days >= 0:
                    if delta_days < 7: age_str = f"{delta_days} يوم"
                    elif delta_days < 30: age_str = f"{round(delta_days/7)} أسبوع"
                    else: age_str = f"{round(delta_days/30.44, 1)} شهر"
                    st.session_state["c_العمر الحالى للطفل (شهور)"] = age_str
                    st.session_state["c_العمر الرحمى للطفل (أسابيع)"] = f"{max(24, min(42, 40 - max(0, round((280 - delta_days) / 7))))} أسبوع"
            else:
                val_text = st.text_input(col_name, key=f"c_text_{col_name}")
                st.session_state[f"c_{col_name}"] = val_text

    # التحقق من حالة التطور الحركي قبل الحفظ لإظهار مربع تحذير أحمر
    current_motor_status = st.session_state.get("c_النمو والتطور الحركي", "")
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
            if col == "تاريخ التسجيل":
                final_c_data[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif col == "اسم المستخدم":
                final_c_data[col] = st.session_state.name
            else:
                val = st.session_state.get(f"c_{col}", "")
                if "الرقم القومى" in col or "رقم الموبايل" in col:
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
