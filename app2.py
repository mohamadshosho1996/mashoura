import datetime
import os
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
    "التحذير من تناول الأدوية بدون إستشارة طبيب والتعرض للتدخين والأبخرة": [
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


# ==================== دوال المساعدة ====================
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


def calculate_motor_development(
    age_str, weight_birth, length_birth, weight_current, length_current
):
  try:
    if not age_str:
      return "طبيعى"
    if "يوم" in age_str or "أسبوع" in age_str:
      age_months = 0.5
    else:
      age_months = float(
          "".join(filter(lambda x: x.isdigit() or x == ".", age_str)) or 1
      )

    w_curr = float(weight_current) if weight_current else 3.5

    if age_months <= 1:
      expected_weight = 3.3 + (age_months * 0.8)
    elif age_months <= 12:
      expected_weight = 3.0 + (age_months * 0.75)
    else:
      expected_weight = 10.0 + ((age_months - 12) * 0.2)

    diff_ratio = w_curr / expected_weight

    if diff_ratio < 0.82:
      return "متاخر"
    elif diff_ratio > 1.25:
      return "متقدم"
    else:
      return "طبيعى"
  except Exception:
    return "طبيعى"


def get_existing_data_supabase(nat_id, table_name, id_column):
  clean_id = clean_digits(nat_id, 14)
  if len(clean_id) == 14:
    try:
      response = (
          supabase.table(table_name)
          .select("*")
          .eq(id_column, clean_id)
          .execute()
      )
      if response.data and len(response.data) > 0:
        return response.data[-1]
    except Exception as e:
      print(f"Error fetching existing data: {e}")
  return {}


# ==================== تسجيل الدخول (Authentication) ====================
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False

if not st.session_state.logged_in:
  st.markdown(
      "<h1 style='text-align: center;'>🌸 برنامج بودى للمشورة الأسرية 🌸</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h3 style='text-align: center; color: #555;'>تسجيل الدخول للنظام</h3>",
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    username_input = st.text_input("اسم المستخدم (Username)")
    password_input = st.text_input("كلمة المرور (Password)", type="password")

    if st.button("تسجيل الدخول", use_container_width=True):
      if (
          username_input in DEFAULT_USERS
          and DEFAULT_USERS[username_input]["pass"] == password_input
      ):
        st.session_state.logged_in = True
        st.session_state.username = username_input
        st.session_state.name = DEFAULT_USERS[username_input]["name"]
        st.session_state.role = DEFAULT_USERS[username_input]["role"]
        st.success(f"مرحباً بكِ {st.session_state.name} ✨")
        st.rerun()
      else:
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")
  st.stop()


# ==================== القائمة الجانبية (Sidebar) ====================
st.sidebar.markdown(f"### 👩‍⚕️ أهلاً بكِ، {st.session_state.name}")
st.sidebar.markdown("---")

menu_options = [
    "سجل الأطفال",
    "استعراض البيانات والداشبورد",
]
if st.session_state.role == "admin":
  menu_options.append("إدارة المستخدمين")

menu = st.sidebar.selectbox("📋 اختر القسم المطلوب:", menu_options)

if st.sidebar.button("🚪 تسجيل الخروج"):
  st.session_state.logged_in = False
  st.rerun()


# ==================== 1. سجل الأطفال ====================
if menu == "سجل الأطفال":
  st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)

  today_str = datetime.date.today().strftime("%Y-%m-%d")
  for col in CHILD_COLUMNS:
    if f"c_{col}" not in st.session_state:
      if col in ["تاريخ الزيارة", "تاريخ اول زيارة"]:
        st.session_state[f"c_{col}"] = today_str
      else:
        st.session_state[f"c_{col}"] = ""

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
      found_data = get_existing_data_supabase(
          nat_id_mom_input, "children_records", "الرقم القومى للام"
      )
      for c_name in CHILD_COLUMNS:
        if c_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
          continue
        val = found_data.get(c_name, "")
        if val:
          st.session_state[f"c_{c_name}"] = str(val)
      st.rerun()

  for col_name in CHILD_COLUMNS:
    if col_name in ["تاريخ التسجيل", "اسم المستخدم", "الرقم القومى للام"]:
      continue

    if col_name == "نوع الولادة":
      st.markdown(f"**{col_name}**")
      current_val = st.session_state.get(f"c_{col_name}", "")

      c_opt1, c_opt2, c_opt3 = st.columns(3)
      with c_opt1:
        chk_nat = st.checkbox(
            "طبيعى", value=(current_val == "طبيعى"), key="c_birth_nat"
        )
      with c_opt2:
        chk_ces = st.checkbox(
            "قيصرى", value=(current_val == "قيصرى"), key="c_birth_ces"
        )
      with c_opt3:
        chk_none = st.checkbox(
            "لا يوجد",
            value=(current_val == "لا يوجد" or current_val == ""),
            key="c_birth_none",
        )

      selected_birth = ""
      if chk_nat:
        selected_birth = "طبيعى"
      elif chk_ces:
        selected_birth = "قيصرى"
      elif chk_none:
        selected_birth = "لا يوجد"

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

      selected_bf_ex = ""
      if chk_3:
        selected_bf_ex = "3 شهور"
      elif chk_4:
        selected_bf_ex = "4 شهور"
      elif chk_6:
        selected_bf_ex = "6 شهور"

      st.session_state[f"c_{col_name}"] = selected_bf_ex

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
            st.session_state.get("c_الطول (سم)", ""),
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
                if "نصف" in next_visit_name:
                  days_to_add = 30 * 30
                else:
                  y_num = int(
                      "".join(
                          filter(lambda x: x.isdigit(), next_visit_name)
                      )
                      or 1
                  )
                  days_to_add = y_num * 365

          next_visit_date = base_date + datetime.timedelta(days=days_to_add)
          st.session_state[f"c_{col_name}"] = str(next_visit_date)
        except Exception:
          pass
        st.text_input(
            f"{col_name} [محسوب تلقائياً بناءً على الزيارة التالية والتاريخ]",
            key=f"c_{col_name}",
        )
      else:
        st.text_input(col_name, key=f"c_{col_name}")

  if st.button("💾 حفظ بيانات الطفل في Supabase", use_container_width=True):
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

    try:
      supabase.table("children_records").insert(final_child_data).execute()
      st.success("تم حفظ بيانات الطفل في Supabase بنجاح! ✨")
    except Exception as e:
      st.error(f"حدث خطأ أثناء الحفظ في قاعدة البيانات: {e}")


# ==================== 2. استعراض البيانات والداشبورد ====================
elif menu == "استعراض البيانات والداشبورد":
  st.markdown(
      "<h2>📊 لوحة المؤشرات واستعراض البيانات المبسطة</h2>",
      unsafe_allow_html=True,
  )

  db_table_name = "children_records"

  try:
    response = supabase.table(db_table_name).select("*").execute()
    df_view = pd.DataFrame(response.data) if response.data else pd.DataFrame()
  except Exception as e:
    st.error(f"خطأ في جلب البيانات من القاعدة: {e}")
    df_view = pd.DataFrame()

  filtered_df = df_view.copy()
  date_col = (
      "تاريخ الزيارة"
      if not df_view.empty and "تاريخ الزيارة" in df_view.columns
      else "تاريخ التسجيل"
  )

  if not df_view.empty and date_col in df_view.columns:
    try:
      df_view["_temp_date"] = pd.to_datetime(
          df_view[date_col], errors="coerce"
      ).dt.date
      valid_dates = df_view["_temp_date"].dropna()

      min_d = valid_dates.min() if not valid_dates.empty else datetime.date.today()
      max_d = valid_dates.max() if not valid_dates.empty else datetime.date.today()

      col_start, col_end, col_user_filter = st.columns(3)
      with col_start:
        start_date = st.date_input(
            "📅 من تاريخ:", value=min_d, key="filter_start_date"
        )
      with col_end:
        end_date = st.date_input(
            "📅 إلى تاريخ:", value=max_d, key="filter_end_date"
        )
      with col_user_filter:
        if "اسم المستخدم" in df_view.columns:
          users_list = [
              "الكل"
          ] + list(df_view["اسم المستخدم"].dropna().unique())
          selected_user_filter = st.selectbox(
              "👩‍⚕️ تصفية حسب الطبيبة:", users_list, key="filter_user_selectbox"
          )
        else:
          selected_user_filter = "الكل"

      filtered_df = df_view[
          (df_view["_temp_date"] >= start_date)
          & (df_view["_temp_date"] <= end_date)
      ].copy()
      filtered_df = filtered_df.drop(columns=["_temp_date"], errors="ignore")
    except Exception:
      filtered_df = df_view.copy()
      selected_user_filter = "الكل"
  else:
    selected_user_filter = "الكل"

  if selected_user_filter != "الكل" and "اسم المستخدم" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["اسم المستخدم"] == selected_user_filter]

  st.markdown("---")
  st.markdown("### 👶 ملخص مؤشرات الأداء والخدمات للأطفال")
  total_child_cases = len(filtered_df)

  def count_match(df, col_name, target_val):
    if col_name in df.columns and not df.empty:
      return (
          df[col_name].fillna("").astype(str).str.strip().eq(target_val).sum()
      )
    return 0

  incubator_count = count_match(filtered_df, "دخول الحضانة", "تم")
  skin_contact_count = count_match(
      filtered_df, "ملامسة الجلد فى الساعة الذهبية الأولى", "تم"
  )
  bf_golden_count = count_match(
      filtered_df, "الرضاعة الطبيعية فى الساعة الذهبية الأولى", "تم"
  )
  exclusive_bf_6m_count = 0
  if "رضاعة طبيعية مطلقة" in filtered_df.columns and not filtered_df.empty:
    exclusive_bf_6m_count = (
        filtered_df["رضاعة طبيعية مطلقة"]
        .fillna("")
        .astype(str)
        .str.strip()
        .isin(["3 شهور", "4 شهور", "6 شهور"])
        .sum()
    )

  family_planning_child_count = count_match(
      filtered_df, "تحويل الى عيادة تنظيم الاسره", "تم"
  )

  summary_df = pd.DataFrame({
      "البيان": [
          "إجمالي عدد حالات الأطفال",
          "عدد حالات دخول الحضانة",
          "عدد حالات ملامسة الجلد فى الساعة الذهبية الأولى",
          "عدد حالات الرضاعة الطبيعية فى الساعة الذهبية الأولى",
          "رضاعة طبيعية مطلقة (3-6 شهور)",
          "عدد حالات تحويل الى عيادة تنظيم الاسره",
      ],
      "الرقم": [
          int(total_child_cases),
          int(incubator_count),
          int(skin_contact_count),
          int(bf_golden_count),
          int(exclusive_bf_6m_count),
          int(family_planning_child_count),
      ],
  })
  st.dataframe(summary_df, use_container_width=True, hide_index=True)
  st.markdown("---")

  col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
  with col_kpi1:
    st.metric(label="📁 إجمالي الحالات بالفترة", value=total_child_cases)
  with col_kpi2:
    unique_users_count = (
        filtered_df["اسم المستخدم"].nunique()
        if "اسم المستخدم" in filtered_df.columns
        else 0
    )
    st.metric(label="👩‍⚕️ الطبيبات المشاركات", value=unique_users_count)
  with col_kpi3:
    st.metric(label="📑 السجل الحالي", value="سجل الأطفال")

  st.markdown("---")
  search_query = st.text_input("🔍 بحث سريع إضافي:")
  if search_query:
    mask = filtered_df.apply(
        lambda row: row.astype(str)
        .str.contains(search_query, case=False, na=False)
        .any(),
        axis=1,
    )
    filtered_df = filtered_df[mask]

  st.dataframe(filtered_df, use_container_width=True)

  if st.session_state.role == "admin":
    st.markdown("---")
    st.markdown("### 🗑️ لوحة التحكم الإدارية (حذف السجلات من Supabase)")
    st.error(
        "⚠️ تنبيه هامة: خيار الحذف متاح فقط لحساب المشرف (Admin) ويقوم بحذف"
        " البيانات نهائياً من قاعدة بيانات Supabase."
    )

    nat_id_to_delete = st.text_input(
        "أدخل الرقم القومي للأم المراد حذفه بالكامل:",
        max_chars=14,
        key="admin_del_nat_id",
    )
    if st.button("🗑️ حذف السجل من القاعدة بالرقم القومي"):
      cleaned_del_id = clean_digits(nat_id_to_delete, 14)
      if len(cleaned_del_id) == 14:
        try:
          supabase.table(db_table_name).delete().eq(
              "الرقم القومى للام", cleaned_del_id
          ).execute()
          st.success("تم الحذف من قاعدة بيانات Supabase بنجاح! ✨")
          st.rerun()
        except Exception as e:
          st.error(f"حدث خطأ أثناء الحذف: {e}")
      else:
        st.warning("يرجى إدخال رقم قومي صحيح يتكون من 14 رقماً.")

  st.markdown("---")
  if not filtered_df.empty:
    csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 تحميل البيانات المعروضة (CSV / Excel)",
        data=csv_data,
        file_name="children_records_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
  else:
    st.info("لا توجد بيانات مسجلة حتى الآن.")


# ==================== 3. إدارة المستخدمين ====================
elif menu == "إدارة المستخدمين" and st.session_state.role == "admin":
  st.markdown("<h2>⚙️ إدارة المستخدمين والصلاحيات</h2>", unsafe_allow_html=True)
  st.write("إدارة حسابات الطبيبات وصلاحيات الوصول للنظام.")

  users_data = []
  for username, info in DEFAULT_USERS.items():
    users_data.append({
        "اسم المستخدم (Username)": username,
        "اسم الطبيبة": info["name"],
        "الصلاحية": info["role"],
    })
  st.dataframe(pd.DataFrame(users_data), use_container_width=True, hide_index=True)
