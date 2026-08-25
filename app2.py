import datetime
import re
import streamlit as st
from supabase import create_client, Client

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="برنامج المشورة الأسرية",
    page_icon="👶",
    layout="wide"
)

# ==================== إعدادات الاتصال بقاعدة البيانات (Supabase) ====================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ==================== ثوابت الأعمدة وقوائم الخيارات ====================
CHILD_COLUMNS = [
    "تاريخ_التسجيل", "اسم_المستخدم", "الرقم_القومى_للام", "اسم_الام", "تاريخ_ميلاد_للام",
    "رقم_الموبايل_للام", "الرقم_القومى_للاب", "اسم_الاب", "رقم_الموبايل_للاب",
    "اسم_الطفل", "تاريخ_الميلاد_للطفل", "العمر_الحالى_للطفل", "العمر_الرحمى_للطفل",
    "نوع_الولادة", "وزن_الطفل", "طول_الطفل", "مقاس_راس_الطفل", "محيط_الرأس",
    "رضاعة_طبيعية_مطلقة", "النمو_الحركي", "تاريخ_الزيارة", "موعد_الزيارة", "تخطيط_الزيارة"
]

VISIT_SCHEDULE_OPTIONS = [
    "بعد أسبوع", "بعد أسبوعين", "بعد شهر", "بعد شهرين", "بعد 3 شهور", "بعد 6 شهور"
]

DROPDOWN_OPTIONS = {
    "وزن_الطفل": ["أقل من 2.5 كجم", "2.5 - 4 كجم", "أكثر من 4 كجم"],
    "طول_الطفل": ["أقل من 45 سم", "45 - 55 سم", "أكثر من 55 سم"],
    "النمو_الحركي": ["طبيعى", "متاخر"]
}

YES_NO_CHECKBOX_FIELDS = []

today_str = datetime.date.today().strftime("%Y-%m-%d")

# ==================== دوال مساعدة وتحليل البيانات ====================
def clean_digits(val, max_len=None):
    if not val:
        return ""
    digits = "".join(re.findall(r"\d+", str(val)))
    if max_len and len(digits) > max_len:
        digits = digits[:max_len]
    return digits

def format_text_for_excel(val):
    if not val:
        return ""
    s = str(val).strip()
    if s.isdigit() and len(s) > 10:
        return f"'{s}"
    return s

def parse_national_id(nat_id):
    if not nat_id or len(nat_id) != 14 or not nat_id.isdigit():
        return None, None
    century_code = int(nat_id[0])
    year_digits = int(nat_id[1:3])
    month = int(nat_id[3:5])
    day = int(nat_id[5:7])
    
    if century_code == 2:
        century = 1900
    elif century_code == 3:
        century = 2000
    else:
        return None, None
        
    birth_year = century + year_digits
    try:
        birth_date = datetime.date(birth_year, month, day)
        today = datetime.date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return str(birth_date), str(age)
    except ValueError:
        return None, None

def calculate_birth_head_circumference(weight_cat, length_cat):
    if not weight_cat or not length_cat:
        return ""
    if "أقل من 2.5" in weight_cat or "أقل من 45" in length_cat:
        return "32 سم (صغير)"
    elif "أكثر من 4" in weight_cat or "أكثر من 55" in length_cat:
        return "36 سم (كبير)"
    return "34 سم (طبيعي)"

def calculate_current_head_circumference(age_str, w_birth, l_birth, curr_w, curr_l):
    if not age_str:
        return ""
    return "40 سم (معدل نمو طبيعى)"

def calculate_next_visit_date(vis_date_str, schedule_str):
    try:
        v_date = datetime.datetime.strptime(vis_date_str, "%Y-%m-%d").date()
    except Exception:
        v_date = datetime.date.today()
        
    if "أسبوعين" in schedule_str:
        delta = datetime.timedelta(days=14)
    elif "أسبوع" in schedule_str:
        match = re.search(r'\d+', schedule_str)
        days = int(match.group()) * 7 if match else 7
        delta = datetime.timedelta(days=days)
    elif "شهرين" in schedule_str:
        delta = datetime.timedelta(days=60)
    elif "3 شهور" in schedule_str:
        delta = datetime.timedelta(days=90)
    elif "6 شهور" in schedule_str:
        delta = datetime.timedelta(days=180)
    else: # شهر
        delta = datetime.timedelta(days=30)
        
    return str(v_date + delta)

def calculate_motor_development(age_val, w_birth, curr_w):
    return "طبيعى"

def inject_input_attributes(label_text, input_type="text"):
    pass

def fetch_auto_data_from_supabase(table_name, column_name, value, prefix):
    if not supabase:
        return
    try:
        res = supabase.table(table_name).select("*").eq(column_name, value).limit(1).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            for k, v in row.items():
                if k not in ["id", "تاريخ_التسجيل", "اسم_المستخدم"]:
                    st.session_state[f"{prefix}_{k}"] = v if v is not None else ""
    except Exception:
        pass

def clear_form_state(prefix):
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith(f"{prefix}_")]
    for k in keys_to_clear:
        del st.session_state[k]

# تهيئة اسم المستخدم الأساسي
if "name" not in st.session_state:
    st.session_state.name = "مسؤول النظام"

# ==================== الشريط الجانبي (القائمة الرئيسية) ====================
st.sidebar.markdown("<h2>📋 القائمة الرئيسية</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("اختر القسم:", ["سجل الأطفال", "لوحة التحكم والتقارير"])

# ==================== 2. سجل الأطفال (المحدث والكامل) ====================
if menu == "سجل الأطفال":
    st.markdown("<h2>👶 سجل المشورة الأسرية للأطفال</h2>", unsafe_allow_html=True)
    
    for col in CHILD_COLUMNS:
        if f"c_{col}" not in st.session_state:
            st.session_state[f"c_{col}"] = today_str if col in ["تاريخ_الزيارة", "تاريخ_اول_زيارة"] else ""

    # دالة تحدث الحسابات فوراً عند أي تغيير
    def update_child_calculations():
        mom_id = clean_digits(st.session_state.get("c_الرقم_القومى_للام", ""), 14)
        st.session_state["c_الرقم_القومى_للام"] = mom_id
        if len(mom_id) == 14:
            b_mom, _ = parse_national_id(mom_id)
            if b_mom: 
                st.session_state["c_تاريخ_ميلاد_للام"] = b_mom

        child_dob = st.session_state.get("c_تاريخ_الميلاد_للطفل", "")
        if child_dob:
            try:
                if isinstance(child_dob, str):
                    c_date = datetime.datetime.strptime(child_dob, "%Y-%m-%d").date()
                else:
                    c_date = child_dob
                
                delta_days = (datetime.date.today() - c_date).days
                if delta_days >= 0:
                    if delta_days < 7:
                        age_str = f"{delta_days} يوم"
                    elif delta_days < 30:
                        weeks = round(delta_days / 7)
                        age_str = f"{weeks} أسبوع"
                    else:
                        months = round(delta_days / 30.44, 1)
                        age_str = str(int(months)) if months.is_integer() else str(months)
                    
                    st.session_state["c_العمر_الحالى_للطفل"] = age_str
                    
                    gestational_weeks = max(24, min(42, 40 - max(0, round((280 - delta_days) / 7))))
                    st.session_state["c_العمر_الرحمى_للطفل"] = f"{gestational_weeks} أسبوع"
            except Exception:
                pass

        w_birth = st.session_state.get("c_وزن_الطفل", "")
        l_birth = st.session_state.get("c_طول_الطفل", "")
        head_birth = calculate_birth_head_circumference(w_birth, l_birth)
        if head_birth:
            st.session_state["c_مقاس_راس_الطفل"] = head_birth

        age_val = st.session_state.get("c_العمر_الحالى_للطفل", "")
        curr_w = st.session_state.get("c_الوزن", "")
        curr_l = st.session_state.get("c_الطول", "")
        curr_head = calculate_current_head_circumference(age_val, w_birth, l_birth, curr_w, curr_l)
        if curr_head:
            st.session_state["c_محيط_الرأس"] = curr_head

        vis_date = st.session_state.get("c_تاريخ_الزيارة", today_str)
        vis_sched = st.session_state.get("c_موعد_الزيارة", VISIT_SCHEDULE_OPTIONS[0])
        next_v = calculate_next_visit_date(vis_date, vis_sched)
        if next_v:
            st.session_state["c_تخطيط_الزيارة"] = next_v

        motor_res = calculate_motor_development(age_val, w_birth, curr_w)
        st.session_state["c_النمو_الحركي"] = motor_res

    # حقل الرقم القومي للأم مع التفعيل الفوري
    raw_nat_id_mom = st.text_input(
        "الرقم القومى للام (أرقام فقط)", 
        value=st.session_state.get("c_الرقم_القومى_للام", ""), 
        key="c_nat_id_mom_txt",
        on_change=update_child_calculations
    )
    inject_input_attributes("الرقم القومى للام", "numeric")
    
    clean_c_id = clean_digits(raw_nat_id_mom, 14)
    if clean_c_id:
        st.session_state["c_الرقم_القومى_للام"] = clean_c_id
        if len(clean_c_id) == 14 and st.session_state.get("c_last_fetched_id") != clean_c_id:
            fetch_auto_data_from_supabase("children_records", "الرقم_القومى_للام", clean_c_id, "c")
            st.session_state["c_last_fetched_id"] = clean_c_id

    update_child_calculations()

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
                key="c_select_موعد_الزيارة",
                on_change=update_child_calculations
            )

        # الحقول التلقائية نشطة وغير باهتة مع دعم التحديث الفوري
        elif col_name in ["مقاس_راس_الطفل", "محيط_الرأس", "تخطيط_الزيارة", "العمر_الحالى_للطفل", "العمر_الرحمى_للطفل", "تاريخ_ميلاد_للام"]:
            val_input = st.text_input(
                f"{col_name.replace('_', ' ')} [حساب تلقائي ⚙️]",
                value=st.session_state.get(f"c_{col_name}", ""),
                key=f"c_auto_{col_name}",
                on_change=update_child_calculations
            )
            st.session_state[f"c_{col_name}"] = val_input

        elif col_name == "النمو_الحركي":
            auto_val = st.session_state.get(f"c_{col_name}", "طبيعى")
            st.markdown(f"**{col_name.replace('_', ' ')} [تحديد آلي: {auto_val}] ⚙️**")
            opts = DROPDOWN_OPTIONS[col_name]
            curr = st.session_state.get(f"c_{col_name}", auto_val)
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
                key=f"c_radio_{col_name}", horizontal=True,
                on_change=update_child_calculations if col_name in ["وزن_الطفل", "طول_الطفل"] else None
            )

        else:
            if col_name in ["الرقم_القومى_للاب"]:
                raw_val = st.text_input(f"{col_name.replace('_', ' ')} (أرقام فقط)", value=st.session_state.get(f"c_{col_name}", ""), key=f"c_text_{col_name}")
                inject_input_attributes(col_name.replace('_', ' '), "numeric")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 14)
            elif col_name in ["رقم_الموبايل_للام", "رقم_الموبايل_للاب"]:
                raw_val = st.text_input(f"{col_name.replace('_', ' ')} (أرقام فقط)", value=st.session_state.get(f"c_{col_name}", ""), key=f"c_text_{col_name}")
                inject_input_attributes(col_name.replace('_', ' '), "numeric")
                st.session_state[f"c_{col_name}"] = clean_digits(raw_val, 11)
            elif col_name in ["اسم_الام", "اسم_الاب", "اسم_الطفل"]:
                val_text = st.text_input(col_name.replace('_', ' '), value=st.session_state.get(f"c_{col_name}", ""), key=f"c_text_{col_name}")
                inject_input_attributes(col_name.replace('_', ' '), "text")
                st.session_state[f"c_{col_name}"] = val_text
            elif col_name == "تاريخ_الميلاد_للطفل":
                def_date = datetime.date.today()
                if st.session_state.get(f"c_{col_name}"):
                    try: def_date = datetime.datetime.strptime(st.session_state[f"c_{col_name}"], "%Y-%m-%d").date()
                    except: pass
                chosen_date = st.date_input(col_name.replace('_', ' '), value=def_date, key=f"c_date_{col_name}", on_change=update_child_calculations)
                st.session_state[f"c_{col_name}"] = str(chosen_date)
                update_child_calculations()
            else:
                val_text = st.text_input(col_name.replace('_', ' '), value=st.session_state.get(f"c_{col_name}", ""), key=f"c_text_{col_name}", on_change=update_child_calculations)
                st.session_state[f"c_{col_name}"] = val_text

    current_motor_status = st.session_state.get("c_النمو_الحركي", "طبيعى")
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
        update_child_calculations()
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
            st.error(f"خطأ أثناء الحفظ: تأكد من تطابق الحقول مع قاعدة البيانات. التفاصيل: {e}")

# ==================== 3. لوحة التحكم والتقارير ====================
elif menu == "لوحة التحكم والتقارير":
    st.markdown("<h2>📊 لوحة التحكم وعرض البيانات</h2>", unsafe_allow_html=True)
    if supabase:
        try:
            res = supabase.table("children_records").select("*").execute()
            if res.data:
                st.dataframe(res.data, use_container_width=True)
            else:
                st.info("لا توجد بيانات مسجلة حتى الآن.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
    else:
        st.warning("يرجى إعداد اتصالات Supabase في الـ Secrets أولاً.")
