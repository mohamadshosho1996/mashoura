import datetime
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==================== إعدادات الصفحة والتصميم ====================
st.set_page_config(
    page_title="برنامج بودى للمشورة الأسرية",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

/* تصميم الرسالة التحذيرية الحمراء الكبيرة */
.danger-alert-box {
    background-color: #FEE2E2;
    border: 3px solid #DC2626;
    border-radius: 12px;
    padding: 20px;
    margin-top: 15px;
    margin-bottom: 15px;
    text-align: center;
    box-shadow: 0px 4px 15px rgba(220, 38, 38, 0.3);
}
.danger-alert-title {
    color: #991B1B;
    font-size: 24px;
    font-weight: 900;
    margin-bottom: 8px;
}
.danger-alert-text {
    color: #B91C1C;
    font-size: 18px;
    font-weight: bold;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ==================== مكون الإدخال الصوتي ====================
def voice_input_button(key_id, label="🎙️ إدخال صوتي"):
    html_code = f"""
    <div style="margin-bottom: 10px;">
        <button id="btn_{key_id}" onclick="startDictation('{key_id}')" style="
            background-color: #BE185D;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 5px;">
            {label}
        </button>
        <span id="status_{key_id}" style="margin-right: 10px; color: #701A75; font-size: 13px; font-weight: bold;"></span>
    </div>

    <script>
    function startDictation(keyId) {{
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            var recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = "ar-EG";

            var statusElem = document.getElementById('status_' + keyId);
            statusElem.innerText = "جاري الاستماع... 🔴";

            recognition.start();

            recognition.onresult = function(e) {{
                var resultText = e.results[0][0].transcript;
                statusElem.innerText = "تم الالتقاط: " + resultText;
                
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: resultText
                }}, '*');
            }};

            recognition.onerror = function(e) {{
                statusElem.innerText = "خطأ في التعرف على الصوت";
            }};

            recognition.onend = function() {{
                if (statusElem.innerText === "جاري الاستماع... 🔴") {{
                    statusElem.innerText = "";
                }}
            }};
        }} else {{
            alert("المتصفح لا يدعم الخاصية الصوتية");
        }}
    }}
    </script>
    """
    return components.html(html_code, height=45)


# ==================== الثوابت وإعدادات البيانات ====================
EXCEL_FILE = "template.xlsx"

DEFAULT_USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "د. شيماء 🌸"},
    "user1": {"pass": "1234", "role": "user", "name": "د. علا 🎀"},
    "user2": {"pass": "1234", "role": "user", "name": "د. عبير 🎀"},
    "user3": {"pass": "1234", "role": "user", "name": "د. ايه 🎀"},
}

VISIT_SCHEDULE_OPTIONS = [
    "الاسبوع الاول",
    "عمر شهرين",
    "عمر 4 شهور",
    "عمر 6 شهور",
    "عمر 9 شهور",
    "عمر 12 شهر",
    "عمر 18 شهر",
    "عمر سنتين",
    "عمر سنتين ونصف",
    "عمر 3 سنين",
    "عمر 3 سنين ونصف",
    "عمر 4 سنين",
    "عمر 4 سنين ونصف",
    "عمر 5 سنين",
    "عمر 5 سنين ونصف",
    "عمر 6 سنين",
]

DROPDOWN_OPTIONS = {
    "مستوى التعليم": [
        "امى",
        "يجيد القراءة",
        "مؤهل متوسط",
        "فوق متوسط",
        "مؤهل عالى",
    ],
    "الوظيفة": ["يعمل", "لا تعمل"],
    "قرابة بين الزوجين": ["نعم", "لا"],
    "وسيلة تنظيم الأسرة المستخدمة سابقا": [
        "توجد",
        "مرغوب",
        "غير مرغوب",
    ],
    "شهر الحمل": [
        "الشهر الاول",
        "الشهر الثانى",
        "الشهر الثالث",
        "الشهر الرابع",
        "الشهر الخامس",
        "الشهر السادس",
        "الشهر السابع",
        "الشهر الثامن",
        "الشهر التاسع",
    ],
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
    "التحذير منناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة": [
        "تم",
        "لم يتم",
    ],
    "المتاعب البسيطة في الشهور الأولى": ["تم", "لم يتم"],
    "المتاعب في الشهور الأخيرة": ["تم", "لم يتم"],
    "علامات الخطر أثناء الحمل": ["تم", "لم يتم"],
    "مشاكل الولادة المبكرة وكيفية تجنبها": ["تم", "لم يتم"],
    "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين": [
        "تم",
        "لم يتم",
    ],
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
    "مستوى التعليم للام": [
        "امى",
        "يجيد القراءة",
        "مؤهل متوسط",
        "فوق متوسط",
        "مؤهل عالى",
    ],
    "مستوى التعليم للاب": [
        "امى",
        "يجيد القراءة",
        "مؤهل متوسط",
        "فوق متوسط",
        "مؤهل عالى",
    ],
    "الوظيفة للام": ["يعمل", "لا تعمل"],
    "مكان الولادة": ["المستشفى", "المنزل"],
    "سبب دخول الحضانة": [
        "انخفاض وزن الطفل.",
        "احتياج الطفل لأدوية محددة بهذا الوقت.",
        "صعوبة شديدة في التنفس لعدم اكتمال نمو الرئتين.",
        "ارتفاع درجة حرارة جسم الرضيع.",
        "تعطل العمليات الحيوية بجسم الطفل.",
        "انخفاض معدل الجلوكوز في دم الطفل.",
        "معاناة الرضيع مشكلات في الجهاز الهضمي.",
        "إصابة الطفل بعدوى في الدم.",
        "إصابة الطفل بالصفراء.",
        "حدوث مشكلات خلال الولادة “الولادة المتعسرة أو الحمل الحرج”.",
        "وجود عيب خلقي يمنع الطفل عن التنفس أو الرضاعة بشكل طبيعي.",
    ],
    "موعد الزيارة": VISIT_SCHEDULE_OPTIONS,
    "رضاعة طبيعية مع سوائل وأعشاب": ["تم", "لم يتم"],
    "رضاعة طبيعية مع صناعي": ["تم", "لم يتم"],
    "رضاعة لبن صناعي": ["تم", "لم يتم"],
    "دخول الحضانة": ["تم", "لم يتم"],
    "ملامسة الجلد فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "الرضاعة الطبيعية فى الساعة الذهبية الأولى": ["تم", "لم يتم"],
    "موقف إستخدام وسيلة تنظيم أسرة": [
        "توجد",
        "مرغوب",
        "غير مرغوب",
        "حدث",
        "لم يحدث",
    ],
    "الحمل الجديد": ["مرغوب", "غير مرغوب"],
    "الخدمات الغير ملباه": ["يوجد"],
    "تحويل الى عيادة تنظيم الاسره": ["تم", "لم يتم"],
    "النمو والتطور الحركي": ["طبيعى", "متقدم", "متاخر"],
    "التطور الإدراكي والمعرفي": ["طبيعى", "متقدم", "متاخر"],
    "التطور اللغوي": ["طبيعى", "متقدم", "متاخر"],
    "رسائل التربية الإيجابية": ["تم", "لم يتم"],
    "الأنشطة التحفيزية": ["تم", "لم يتم"],
    (
        "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة"
    ): ["تم", "لم يتم"],
    "إعطاء الجرعة اليومية من الحديد": ["يوجد"],
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة": [
        "تم التوعيه",
        "لم يتم التوعيه",
    ],
    "إعطاء الجرعة اليومية من فيتامين د": ["يوجد"],
    "كيفية رعاية السرة والإهتمام بنظافة الطفل": ["تم", "لم يتم"],
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو": [
        "تم",
        "لم يتم",
    ],
    "أهمية الإلتزام بتطعيمات الطفل": ["تم", "لم يتم"],
    "التغذية الصحية للأم المرضعة": ["تم", "لم يتم"],
    "كيفية التعرف على علامات الخطورة": ["تم", "لم يتم"],
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع": [
        "تم",
        "لم يتم",
    ],
    "كفاية اللبن وكمية البراز": ["تم", "لم يتم"],
}

PREGNANT_COLUMNS = [
    "تاريخ التسجيل",
    "اسم المستخدم",
    "الاسم",
    "العنوان",
    "الرقم القومى",
    "رقم الموبايل",
    "العمر الحالى",
    "السن عند الزواج",
    "السن عند الحمل الاول",
    "مستوى التعليم",
    "الوظيفة",
    "تاريخ اخر دورة شهرية",
    "قرابة بين الزوجين",
    "عدد مرات الحمل",
    "عدد مرات الاجهاض",
    "عدد الاطفال",
    "المدة بين اخر حملين",
    "نوع الولادة",
    "أمراض مزمنة: إرتفاع ضغط الدم",
    "أمراض مزمنة: السكر",
    "أمراض مزمنة: إضطرابات الغدة",
    "أمراض مزمنة: الأنيميا",
    "أمراض مزمنة: اخرى",
    'مكملات "قبل": حمض الفوليك',
    'مكملات "قبل": الحديد',
    'مكملات "قبل": الكالسيوم',
    'مكملات "أثناء": حمض الفوليك',
    'مكملات "أثناء": الحديد',
    'مكملات "أثناء": الكالسيوم',
    "وسيلة تنظيم الأسرة المستخدمة سابقا",
    "مدة إستخدام الوسيلة السابقة",
    "شهر الحمل",
    "التاريخ الزيارة",
    "التغذية السليمة",
    "المكملات الغذائية",
    "التمرينات الرياضية",
    "قسط من النوم والراحة",
    "المتابعة الدورية للحمل",
    "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة",
    "المتاعب البسيطة في الشهور الأولى",
    "المتاعب في الشهور الأخيرة",
    "علامات الخطر أثناء الحمل",
    "مشاكل الولادة المبكرة وكيفية تجنبها",
    "حركة الجنين / معرفة جنس الجنين/ تمييز الأصوات من قبل الجنين",
    "تغير لون الجلد حول الحلمة وظهور بعض إفرازات من الثدي",
    "إرتداء الملابس الفضفاضة المريحة",
    "الإستعداد للولادة / تحضير ملابس المولود ، الخ",
    "علامات الولادة",
    "مميزات الولادة الطبيعية",
    "الساعة الذهبية الأولى",
    "ملامسة الجلد للجلد",
    "البداية المبكرة للرضاعة الطبيعية",
    "الرضاعة الطبيعية المطلقة",
    "أهمية المباعدة",
    "وسائل تنظيم الأسرة",
    "إستخدام وسيلة بعد الولادة مباشرة",
    "التطور العصبي والنفسي للطفل",
    "ملاحظات/ توصيات",
    "تخطيط الزيارة القادمة",
    "المتابعة ما بعد الولادة",
]

CHILD_COLUMNS = [
    "تاريخ التسجيل",
    "اسم المستخدم",
    "تاريخ اول زيارة",
    "رقم الحالة",
    "اسم الام",
    "الرقم القومى للام",
    "رقم الموبايل للام",
    "تاريخ ميلاد الام",
    "مستوى التعليم للام",
    "عدد الاطفال لدى الام",
    "المدة بين اخر حملين",
    "الوظيفة للام",
    "الرقم القومى للاب",
    "رقم الموبايل للاب",
    "اسم الاب",
    "مستوى التعليم للاب",
    "اسم الطفل",
    "تاريخ الميلاد للطفل",
    "العمر الحالى للطفل (شهور)",
    "العمر الرحمى للطفل (أسابيع)",
    "مكان المتابعة (وحدة)",
    "مكان المتابعة (مستشفى)",
    "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)",
    "مصدر الاحالة (عيادة خاصة)",
    "مصدر الاحالة(عيادة التطعيمات)",
    "مصدر الاحالة(نصيحة)",
    "نوع الولادة",
    "مكان الولادة",
    "وزن الطفل عند الولادة",
    "طول الطفل عند الولادة",
    "مقاس راس الطفل عند الولادة",
    "دخول الحضانة",
    "سبب دخول الحضانة",
    "مدة البقاء فى الحضانة",
    "ملامسة الجلد فى الساعة الذهبية الأولى",
    "الرضاعة الطبيعية فى الساعة الذهبية الأولى",
    "موعد الزيارة",
    "تاريخ الزيارة",
    "رضاعة طبيعية مطلقة",
    "رضاعة طبيعية مع سوائل وأعشاب",
    "رضاعة طبيعية مع صناعي",
    "رضاعة لبن صناعي",
    "الوزن (كجم)",
    "الطول (سم)",
    "محيط الرأس (سم)",
    "فوائد الرضاعة الطبيعية والأوضاع وعلامات الجوع والشبع",
    "كفاية اللبن وكمية البراز",
    "إعطاء الجرعة اليومية من فيتامين د",
    "كيفية رعاية السرة والإهتمام بنظافة الطفل",
    "البطاقة الصحية وأهمية المتابعة الدورية ومنحنيات النمو",
    "أهمية الإلتزام بتطعيمات الطفل",
    "التغذية الصحية للأم المرضعة",
    "كيفية التعرف على علامات الخطورة",
    "النمو والتطور الحركي",
    "التطور الإدراكي والمعرفي",
    "التطور اللغوي",
    "رسائل التربية الإيجابية",
    "الأنشطة التحفيزية",
    "التوعية عن التغذية التكميلية وسلامة الغذاء والتغذية السليمة",
    "إعطاء الجرعة اليومية من الحديد",
    "أهمية إستخدام وسيلة تنظيم أسرة وأهمية المباعدة",
    "موقف إستخدام وسيلة تنظيم أسرة",
    "الحمل الجديد",
    "الخدمات الغير ملباه",
    "تحويل الى عيادة تنظيم الاسره",
    "تخطيط الزيارة القادمة",
]

YES_NO_CHECKBOX_FIELDS = [
    "مكان المتابعة (وحدة)",
    "مكان المتابعة (مستشفى)",
    "مكان المتابعة (اخرى)",
    "مصدر الاحالة(مستشفى الولادة)",
    "مصدر الاحالة (عيادة خاصة)",
    "مصدر الاحالة(عيادة التطعيمات)",
    "مصدر الاحالة(نصيحة)",
]


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
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
            return str(birth_date), str(age)
        except ValueError:
            return "", ""
    return "", ""


# ==================== دالة التطور الحركي بناءً على الوزن والطول ====================
def calculate_motor_development(
    age_str, weight_birth, length_birth, weight_current, length_current
):
    try:
        w_b = float(weight_birth) if weight_birth else 3.2
        l_b = float(length_birth) if length_birth else 50.0
        w_c = float(weight_current) if weight_current else w_b
        l_c = float(length_current) if length_current else l_b

        if not age_str:
            age_months = 0.5
        elif "يوم" in age_str:
            age_months = 0.2
        elif "أسبوع" in age_str:
            weeks = float(
                "".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1
            )
            age_months = weeks / 4.0
        else:
            age_months = float(
                "".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1
            )

        # معدل زيادة الوزن المتوقع شهرياً حسب العمر (معايير منظمة الصحة العالمية)
        if age_months <= 3:
            expected_w_gain = age_months * 0.8
            expected_l_gain = age_months * 3.5
        elif age_months <= 6:
            expected_w_gain = (3 * 0.8) + ((age_months - 3) * 0.6)
            expected_l_gain = (3 * 3.5) + ((age_months - 3) * 2.0)
        elif age_months <= 12:
            expected_w_gain = (3 * 0.8) + (3 * 0.6) + ((age_months - 6) * 0.4)
            expected_l_gain = (3 * 3.5) + (3 * 2.0) + ((age_months - 6) * 1.5)
        else:
            expected_w_gain = 4.2 + ((age_months - 12) * 0.2)
            expected_l_gain = 20.0 + ((age_months - 12) * 1.0)

        exp_weight = w_b + expected_w_gain
        exp_length = l_b + expected_l_gain

        weight_ratio = w_c / exp_weight
        length_ratio = l_c / exp_length
        combined_score = (weight_ratio * 0.6) + (length_ratio * 0.4)

        if combined_score < 0.83:
            return "متاخر"
        elif combined_score > 1.22:
            return "متقدم"
        else:
            return "طبيعى"
    except Exception:
        return "طبيعى"


def get_existing_data(nat_id, sheet_name, id_column):
    clean_id = clean_digits(nat_id, 14)
    if os.path.exists(EXCEL_FILE) and len(clean_id) == 14:
        try:
            excel = pd.ExcelFile(EXCEL_FILE)
            for s in excel.sheet_names:
                df = pd.read_excel(excel, sheet_name=s, dtype=str)
                if id_column in df.columns:
                    match = df[df[id_column].astype(str).str.strip() == clean_id]
                    if not match.empty:
                        return match.iloc[-1].to_dict()
        except Exception:
            pass
    return {}


if not os.path.exists(EXCEL_FILE):
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            pd.DataFrame(columns=PREGNANT_COLUMNS).to_excel(
                writer, sheet_name="المشورة الاسرية للحامل", index=False
            )
            pd.DataFrame(columns=CHILD_COLUMNS).to_excel(
                writer, sheet_name="سجل المشورة للاطفال", index=False
            )
    except ModuleNotFoundError:
        st.error(
            "تنبيه: مكتبة openpyxl غير مضافة في requirements.txt الخاص بالمشروع!"
        )

# ==================== تسجيل الدخول ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.name = None
    st.session_state.role = None

if not st.session_state.logged_in:
    st.markdown(
        "<h2 style='text-align: center; color: #BE185D;'>🌸 برنامج بودى للمشورة"
        " الأسرية 🌸</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h4 style='text-align: center; color: #701A75;'>تسجيل الدخول للنظام</h4>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_options = {
            f"{v['name']} ({k})": k for k, v in DEFAULT_USERS.items()
        }
        selected_display = st.selectbox(
            "اختر الحساب والطبيبة 🩺", list(user_options.keys())
        )
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
menu_options = [
    "الصفحة الرئيسية",
    "سجل الحوامل",
    "سجل الأطفال",
    "استعراض البيانات والداشبورد",
]
if st.session_state.role == "admin":
    menu_options.append("إدارة المستخدمين")

st.sidebar.markdown(f"### أهلاً بكِ د. {st.session_state.name} 🌸")
sidebar_menu = st.sidebar.radio(
    "القائمة الرئيسية (جانبية)", menu_options, key="sidebar_radio"
)

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown("---")
col_mobile_nav, col_mobile_logout = st.columns([3, 1])
with col_mobile_nav:
    main_screen_menu = st.selectbox(
        "📱 انتقل مباشرة إلى القسم المطلوب:", menu_options, key="mobile_selectbox"
    )
with col_mobile_logout:
    if st.button("خروج 🚪"):
        st.session_state.logged_in = False
        st.rerun()

menu = main_screen_menu
st.markdown("---")

# ==================== 1. الصفحة الرئيسية ====================
if menu == "الصفحة الرئيسية":
    st.markdown(
        "<h1>✨ مرحباً بكِ في نظام المشورة الأسرية الشامل ✨</h1>",
        unsafe_allow_html=True,
    )

# ==================== 2. سجل الحوامل ====================
elif menu == "سجل الحوامل":
    st.markdown("<h2>🤰 سجل المشورة الأسرية للحوامل</h2>", unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for col in PREGNANT_COLUMNS:
        if f"p_{col}" not in st.session_state:
            if col == "التاريخ الزيارة":
                st.session_state[f"p_{col}"] = today_str
            else:
                st.session_state[f"p_{col}"] = ""

    form_data = {}
    for col_name in PREGNANT_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم"]:
            continue

        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"p_{col_name}", "")
            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1:
                chk_nat = st.checkbox(
                    "طبيعى",
                    value=(current_val == "طبيعى"),
                    key="p_birth_nat",
                )
            with c_opt2:
                chk_ces = st.checkbox(
                    "قيصرى",
                    value=(current_val == "قيصرى"),
                    key="p_birth_ces",
                )
            with c_opt3:
                chk_none = st.checkbox(
                    "لا يوجد",
                    value=(current_val == "لا يوجد" or current_val == ""),
                    key="p_birth_none",
                )
            selected_birth = (
                "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")
            )
            form_data[col_name] = selected_birth
            st.session_state[f"p_{col_name}"] = selected_birth

        elif col_name in DROPDOWN_OPTIONS:
            st.markdown(f"**{col_name}**")
            options = DROPDOWN_OPTIONS[col_name]
            current_val = st.session_state.get(f"p_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}",
                options,
                index=(options.index(current_val) if current_val in options else 0),
                key=f"p_radio_{col_name}",
                horizontal=True,
            )
            form_data[col_name] = chosen_choice
            st.session_state[f"p_{col_name}"] = chosen_choice
        else:
            voice_input_button(f"p_btn_{col_name}")

            if col_name == "الرقم القومى":
                raw_val = st.text_input(col_name, key=f"p_{col_name}")
                cleaned_val = clean_digits(raw_val, 14)
                form_data[col_name] = cleaned_val
                if len(cleaned_val) == 14:
                    _, calc_age = parse_national_id(cleaned_val)
                    if calc_age:
                        st.session_state["p_العمر الحالى"] = calc_age
            elif col_name == "رقم الموبايل":
                raw_val = st.text_input(col_name, key=f"p_{col_name}")
                cleaned_val = clean_digits(raw_val, 11)
                form_data[col_name] = cleaned_val
            elif col_name == "العمر الحالى":
                form_data[col_name] = st.text_input(
                    f"{col_name} [محسوب تلقائياً من الرقم القومي]",
                    key=f"p_{col_name}",
                )
            elif col_name == "التاريخ الزيارة":
                form_data[col_name] = st.text_input(
                    f"{col_name} [تاريخ اليوم التلقائي]", key=f"p_{col_name}"
                )
            else:
                form_data[col_name] = st.text_input(col_name, key=f"p_{col_name}")

    if st.button("💾 حفظ بيانات الحامل", use_container_width=True):
        final_form_data = {}
        for col in PREGNANT_COLUMNS:
            if col == "تاريخ التسجيل":
                final_form_data[col] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif col == "اسم المستخدم":
                final_form_data[col] = st.session_state.name
            else:
                final_form_data[col] = st.session_state.get(
                    f"p_{col}", form_data.get(col, "")
                )

        new_df = pd.DataFrame([final_form_data], dtype=str)
        excel = pd.ExcelFile(EXCEL_FILE)
        all_dfs = {
            s: pd.read_excel(excel, sheet_name=s, dtype=str)
            for s in excel.sheet_names
        }

        for col in PREGNANT_COLUMNS:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[PREGNANT_COLUMNS]

        if "المشورة الاسرية للحامل" in all_dfs:
            all_dfs["المشورة الاسرية للحامل"] = pd.concat(
                [all_dfs["المشورة الاسرية للحامل"], new_df], ignore_index=True
            )
        else:
            all_dfs["المشورة الاسرية للحامل"] = new_df

        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            for s, df in all_dfs.items():
                df.to_excel(writer, sheet_name=s, index=False)
        st.success("تم حفظ بيانات الحامل بنجاح! ✨")

# ==================== 3. سجل الأطفال ====================
elif menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            if col in ["تاريخ الزيارة", "تاريخ اول زيارة"]:
                st.session_state[f"c_{col}"] = today_str
            else:
                st.session_state[f"c_{col}"] = ""

    voice_input_button("c_btn_الرقم القومى للام")
    raw_nat_id_mom = st.text_input(
        "الرقم القومى للام (اختياري)", key="c_الرقم القومى للام_input"
    )
    nat_id_mom_input = clean_digits(raw_nat_id_mom, 14)
    if nat_id_mom_input:
        st.session_state["c_الرقم القومى للام"] = nat_id_mom_input

    if len(nat_id_mom_input) == 14:
        b_date_mom, _ = parse_national_id(nat_id_mom_input)
        if b_date_mom and not st.session_state.get("c_تاريخ ميلاد الام"):
            st.session_state["c_تاريخ ميلاد الام"] = b_date_mom

    if len(nat_id_mom_input) == 14:
        if st.button("🔍 استرجاع بيانات الأسرة المسجلة مسبقاً"):
            found_data = get_existing_data(
                nat_id_mom_input, "سجل المشورة للاطفال", "الرقم القومى للام"
            ) or get_existing_data(
                nat_id_mom_input, "المشورة الاسرية للحامل", "الرقم القومى"
            )
            for c_name in CHILD_COLUMNS:
                if c_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
                    continue
                val = found_data.get(c_name, "")
                if val:
                    st.session_state[f"c_{c_name}"] = str(val)
            st.rerun()

    # تحديث تلقائي مستمر للنمو والتطور الحركي
    calculated_motor = calculate_motor_development(
        st.session_state.get("c_العمر الحالى للطفل (شهور)", ""),
        st.session_state.get("c_وزن الطفل عند الولادة", ""),
        st.session_state.get("c_طول الطفل عند الولادة", ""),
        st.session_state.get("c_الوزن (كجم)", ""),
        st.session_state.get("c_الطول (سم)", ""),
    )
    st.session_state["c_النمو والتطور الحركي"] = calculated_motor

    for col_name in CHILD_COLUMNS:
        if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
            continue

        if col_name == "نوع الولادة":
            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", "")
            c_opt1, c_opt2, c_opt3 = st.columns(3)
            with c_opt1:
                chk_nat = st.checkbox(
                    "طبيعى",
                    value=(current_val == "طبيعى"),
                    key="c_birth_nat",
                )
            with c_opt2:
                chk_ces = st.checkbox(
                    "قيصرى",
                    value=(current_val == "قيصرى"),
                    key="c_birth_ces",
                )
            with c_opt3:
                chk_none = st.checkbox(
                    "لا يوجد",
                    value=(current_val == "لا يوجد" or current_val == ""),
                    key="c_birth_none",
                )
            selected_birth = (
                "طبيعى" if chk_nat else ("قيصرى" if chk_ces else "لا يوجد")
            )
            st.session_state[f"c_{col_name}"] = selected_birth

        elif col_name == "رضاعة طبيعية مطلقة":
            st.markdown(f"**{col_name}**")
            c1, c2, c3 = st.columns(3)
            current_val = st.session_state.get(f"c_{col_name}", "")
            with c1:
                chk_3 = st.checkbox(
                    "3 شهور", value=(current_val == "3 شهور"), key="c_bf_ex_3"
                )
            with c2:
                chk_4 = st.checkbox(
                    "4 شهور", value=(current_val == "4 شهور"), key="c_bf_ex_4"
                )
            with c3:
                chk_6 = st.checkbox(
                    "6 شهور", value=(current_val == "6 شهور"), key="c_bf_ex_6"
                )
            selected_bf_ex = (
                "3 شهور" if chk_3 else ("4 شهور" if chk_4 else ("6 شهور" if chk_6 else ""))
            )
            st.session_state[f"c_{col_name}"] = selected_bf_ex

        elif col_name in YES_NO_CHECKBOX_FIELDS:
            checked = st.checkbox(col_name, value=False, key=f"c_chk_{col_name}")
            st.session_state[f"c_{col_name}"] = "نعم" if checked else ""

        elif col_name in DROPDOWN_OPTIONS:
            options = DROPDOWN_OPTIONS[col_name]

            if col_name == "موعد الزيارة":
                auto_visit_choice = VISIT_SCHEDULE_OPTIONS[0]
                try:
                    age_str = st.session_state.get("c_العمر الحالى للطفل (شهور)", "")
                    if age_str:
                        if "يوم" in age_str or "أسبوع" in age_str:
                            auto_visit_choice = "الاسبوع الاول"
                        else:
                            age_num = float(
                                "".join(
                                    filter(lambda x: x.isdigit() or x == ".", age_str)
                                )
                                or 0
                            )
                            if age_num <= 2:
                                auto_visit_choice = "عمر شهرين"
                            elif age_num <= 4:
                                auto_visit_choice = "عمر 4 شهور"
                            elif age_num <= 6:
                                auto_visit_choice = "عمر 6 شهور"
                            elif age_num <= 9:
                                auto_visit_choice = "عمر 9 شهور"
                            elif age_num <= 12:
                                auto_visit_choice = "عمر 12 شهر"
                            elif age_num <= 18:
                                auto_visit_choice = "عمر 18 شهر"
                            elif age_num <= 24:
                                auto_visit_choice = "عمر سنتين"
                            elif age_num <= 30:
                                auto_visit_choice = "عمر سنتين ونصف"
                            elif age_num <= 36:
                                auto_visit_choice = "عمر 3 سنين"
                            elif age_num <= 42:
                                auto_visit_choice = "عمر 3 سنين ونصف"
                            elif age_num <= 48:
                                auto_visit_choice = "عمر 4 سنين"
                            elif age_num <= 54:
                                auto_visit_choice = "عمر 4 سنين ونصف"
                            elif age_num <= 60:
                                auto_visit_choice = "عمر 5 سنين"
                            elif age_num <= 66:
                                auto_visit_choice = "عمر 5 سنين ونصف"
                            else:
                                auto_visit_choice = "عمر 6 سنين"
                except Exception:
                    pass
                st.session_state[f"c_{col_name}"] = auto_visit_choice

            st.markdown(f"**{col_name}**")
            current_val = st.session_state.get(f"c_{col_name}", options[0])
            chosen_choice = st.radio(
                f"اختر {col_name}",
                options,
                index=(options.index(current_val) if current_val in options else 0),
                key=f"c_radio_{col_name}",
                horizontal=True,
            )
            st.session_state[f"c_{col_name}"] = chosen_choice

        else:
            voice_input_button(f"c_btn_{col_name}")

            if col_name in ["الرقم القومى للام", "الرقم القومى للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم الموبايل للام", "رقم الموبايل للاب"]:
                raw_val = st.text_input(col_name, key=f"c_{col_name}_raw")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name == "تاريخ ميلاد الام":
                st.text_input(
                    f"{col_name} [يتولد تلقائياً إذا أُدخل الرقم القومي للأم]",
                    key=f"c_{col_name}",
                )

            elif col_name == "تاريخ الميلاد للطفل":
                default_date_val = datetime.date.today()
                existing_b_date = st.session_state.get(f"c_{col_name}", "")
                if existing_b_date:
                    try:
                        default_date_val = datetime.datetime.strptime(
                            existing_b_date.strip(), "%Y-%m-%d"
                        ).date()
                    except Exception:
                        pass

                chosen_date = st.date_input(
                    col_name, value=default_date_val, key=f"c_date_input_{col_name}"
                )
                st.session_state[f"c_{col_name}"] = str(chosen_date)

                try:
                    if st.session_state[f"c_{col_name}"]:
                        today_date = datetime.date.today()
                        delta_days = (today_date - chosen_date).days

                        if delta_days >= 0:
                            if delta_days < 7:
                                age_display = f"{delta_days} يوم"
                            elif delta_days < 30:
                                weeks_count = round(delta_days / 7)
                                age_display = f"{weeks_count} أسبوع"
                            else:
                                months_count = round(delta_days / 30.44, 1)
                                if months_count.is_integer():
                                    months_count = int(months_count)
                                age_display = f"{months_count} شهر"
                            st.session_state["c_العمر الحالى للطفل (شهور)"] = age_display

                            gestational_weeks_calc = max(
                                24, min(42, 40 - max(0, round((280 - delta_days) / 7)))
                            )
                            st.session_state["c_العمر الرحمى للطفل (أسابيع)"] = (
                                f"{gestational_weeks_calc} أسبوع"
                            )
                except Exception:
                    pass

            elif col_name == "العمر الحالى للطفل (شهور)":
                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")

            elif col_name == "العمر الرحمى للطفل (أسابيع)":
                st.text_input(
                    f"{col_name} [محسوب بدقة بناءً على تاريخ الميلاد]",
                    key=f"c_{col_name}",
                )

            elif col_name == "وزن الطفل عند الولادة":
                st.text_input(col_name, key=f"c_{col_name}")

            elif col_name == "طول الطفل عند الولادة":
                st.text_input(col_name, key=f"c_{col_name}")
                try:
                    w_val = st.session_state.get("c_وزن الطفل عند الولادة", "3.0")
                    l_val = st.session_state.get("c_طول الطفل عند الولادة", "50.0")
                    if w_val and l_val:
                        st.session_state["c_مقاس راس الطفل عند الولادة"] = str(
                            round((float(l_val) / 2) + (float(w_val) * 0.5) + 10, 1)
                        )
                except Exception:
                    pass

            elif col_name == "محيط الرأس (سم)":
                try:
                    w_birth = float(
                        st.session_state.get("c_وزن الطفل عند الولادة", "3.0") or 3.0
                    )
                    l_birth = float(
                        st.session_state.get("c_طول الطفل عند الولادة", "50.0") or 50.0
                    )
                    w_curr = float(st.session_state.get("c_الوزن (كجم)", "3.5") or 3.5)
                    l_curr = float(st.session_state.get("c_الطول (سم)", "52.0") or 52.0)
                    age_str = st.session_state.get("c_العمر الحالى للطفل (شهور)", "1")

                    if "يوم" in age_str or "أسبوع" in age_str:
                        age_m = 0.5
                    else:
                        age_m = float(
                            "".join(filter(lambda x: x.isdigit() or x == ".", age_str))
                            or 1.0
                        )

                    base_head = (l_birth * 0.35) + (w_birth * 0.8) + 15.0
                    growth_factor = (l_curr * 0.1) + (w_curr * 0.4) + (age_m * 0.5)
                    calc_head = round((base_head + growth_factor) / 2.0 + 10.0, 1)

                    st.session_state[f"c_{col_name}"] = str(calc_head)
                except Exception:
                    pass

                st.text_input(
                    f"{col_name} [محسوب تلقائياً من بيانات الولادة، الحالي، وعمر الطفل]",
                    key=f"c_{col_name}",
                )

            elif col_name == "تخطيط الزيارة القادمة":
                try:
                    current_visit = st.session_state.get("c_موعد الزيارة", "")
                    reg_date_str = st.session_state.get("c_تاريخ الزيارة", today_str)
                    base_date = datetime.datetime.strptime(
                        reg_date_str.strip(), "%Y-%m-%d"
                    ).date()

                    days_to_add = 30
                    if current_visit in VISIT_SCHEDULE_OPTIONS:
                        idx = VISIT_SCHEDULE_OPTIONS.index(current_visit)
                        if idx + 1 < len(VISIT_SCHEDULE_OPTIONS):
                            next_visit_name = VISIT_SCHEDULE_OPTIONS[idx + 1]
                            if "شهر" in next_visit_name:
                                m_num = int(
                                    "".join(
                                        filter(lambda x: x.isdigit(), next_visit_name)
                                    )
                                    or 1
                                )
                                days_to_add = m_num * 30
                            elif "سنين" in next_visit_name or "سنتين" in next_visit_name:
                                days_to_add = 180 if "نصف" in next_visit_name else 365
                            elif "الاسبوع" in next_visit_name:
                                days_to_add = 7

                    next_date = base_date + datetime.timedelta(days=days_to_add)
                    st.session_state[f"c_{col_name}"] = str(next_date)
                except Exception:
                    pass

                st.text_input(f"{col_name} [محسوب تلقائياً]", key=f"c_{col_name}")

            else:
                st.text_input(col_name, key=f"c_{col_name}")

    if st.button("💾 حفظ بيانات الطفل", use_container_width=True):
        final_child_data = {}
        for col in CHILD_COLUMNS:
            if col == "تاريخ التسجيل":
                final_child_data[col] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            elif col == "اسم المستخدم":
                final_child_data[col] = st.session_state.name
            else:
                final_child_data[col] = st.session_state.get(f"c_{col}", "")

        new_df = pd.DataFrame([final_child_data], dtype=str)
        excel = pd.ExcelFile(EXCEL_FILE)
        all_dfs = {
            s: pd.read_excel(excel, sheet_name=s, dtype=str)
            for s in excel.sheet_names
        }

        for col in CHILD_COLUMNS:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[CHILD_COLUMNS]

        if "سجل المشورة للاطفال" in all_dfs:
            all_dfs["سجل المشورة للاطفال"] = pd.concat(
                [all_dfs["سجل المشورة للاطفال"], new_df], ignore_index=True
            )
        else:
            all_dfs["سجل المشورة للاطفال"] = new_df

        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            for s, df in all_dfs.items():
                df.to_excel(writer, sheet_name=s, index=False)

        # التنبيه الأحمر البارز عند التأخر الحركي
        motor_status = final_child_data.get("النمو والتطور الحركي", "")
        if motor_status == "متاخر":
            st.markdown(
                """
                <div class="danger-alert-box">
                    <div class="danger-alert-title">🚨 تنبيه حرج: الطفل متأخر في النمو! 🚨</div>
                    <div class="danger-alert-text">بناءً على قياسات الوزن والطول مقارنة بالعُمر والحالة عند الولادة، يبدو أن الطفل يعاني من تأخر في النمو والتطور الحركي. يرجى المتابعة والتحويل للتقييم الطبي الفوري.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.success("تم حفظ بيانات الطفل بنجاح! ✨")

# ==================== 4. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
    st.markdown("<h2>📊 لوحة البيانات والإحصائيات</h2>", unsafe_allow_html=True)
    if os.path.exists(EXCEL_FILE):
        excel = pd.ExcelFile(EXCEL_FILE)
        df_preg = (
            pd.read_excel(excel, sheet_name="المشورة الاسرية للحامل")
            if "المشورة الاسرية للحامل" in excel.sheet_names
            else pd.DataFrame()
        )
        df_child = (
            pd.read_excel(excel, sheet_name="سجل المشورة للاطفال")
            if "سجل المشورة للاطفال" in excel.sheet_names
            else pd.DataFrame()
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric("عدد الحوامل المسجلات", len(df_preg))
        with col2:
            st.metric("عدد الأطفال المسجلين", len(df_child))

        tab1, tab2 = st.tabs(["بيانات الحوامل", "بيانات الأطفال"])
        with tab1:
            st.dataframe(df_preg)
        with tab2:
            st.dataframe(df_child)

# ==================== 5. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
    st.markdown("<h2>⚙️ إدارة حسابات المستخدمين</h2>", unsafe_allow_html=True)
    st.write("جدول المستخدمين المتاحين حالياً في النظام:")
    st.json(DEFAULT_USERS)
