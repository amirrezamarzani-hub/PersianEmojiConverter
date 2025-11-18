# app.py (نسخهٔ مقاوم و اصلاح‌شده)
import streamlit as st
import json
import os
from datetime import datetime
import traceback

# تلاش برای import ماژول‌های engine (پشتیبانی هم از import با/بدون پوشه)
model_loader = None
init_concept_bank = None
map_poem_to_emojis = None
_import_errors = []

try:
    from engineembeddings import load_model as load_model_func
    model_loader = load_model_func
except Exception as e:
    _import_errors.append(f"engine.embeddings import error: {e}")
    try:
        # fallback to single-file name if user named it engineembeddings.py
        from engineembeddings import load_model as load_model_func
        model_loader = load_model_func
    except Exception as e2:
        _import_errors.append(f"engineembeddings import error: {e2}")

try:
    from enginemapper import init_concept_bank as init_cb_func, map_poem_to_emojis as map_fn
    init_concept_bank = init_cb_func
    map_poem_to_emojis = map_fn
except Exception as e:
    _import_errors.append(f"engine.mapper import error: {e}")
    try:
        from enginemapper import init_concept_bank as init_cb_func, map_poem_to_emojis as map_fn
        init_concept_bank = init_cb_func
        map_poem_to_emojis = map_fn
    except Exception as e2:
        _import_errors.append(f"enginemapper import error: {e2}")

# ------------ تنظیمات UI ------------
st.set_page_config(page_title="Persian Emoji Converter", layout="centered")
st.title("🔶 Persian Emoji Converter — نسخهٔ پیشرفته (مقاوم)")

# نمایش خطاهای import در صفحه (در صورت وجود) ولی نه مزاحم برای کاربر
if _import_errors:
    with st.expander("⚠️ هشدار: مشکلات ماژول/بارگذاری (برای دیباگ)"):
        for it in _import_errors:
            st.text(it)

# ------------ loader با کش برای مدل ------------
@st.cache_resource
def load_model_cached():
    if model_loader is None:
        return None, "model_loader_not_found"
    try:
        model = model_loader()
        return model, None
    except Exception as e:
        # بازگرداندن پیغام خطا برای نمایش کاربر
        return None, str(e)

# ------------ یک mapper fallback ساده (اگر module اصلی نیامد) ------------
SIMPLE_MAP = {
    "عشق": "❤️", "دل": "💓", "پارسی": "📜", "ایران": "🇮🇷",
    "رنج": "💪", "سال": "📅", "زنده": "🌱", "می": "🍷", "ماه": "🌙",
    "خورشید": "☀️", "دریا": "🌊", "کوه": "⛰️", "گل": "🌹",
}

def simple_map_poem_to_emojis(poem: str):
    import re
    from hazm import Normalizer
    normalizer = Normalizer()
    t = normalizer.normalize(poem)
    toks = re.split(r"\s+", t)
    mapped = []
    explanations = []
    for tok in toks:
        if not tok:
            continue
        found = False
        for k, v in SIMPLE_MAP.items():
            if k in tok:
                mapped.append(v)
                explanations.append({"token": tok, "concept": k, "emoji": v, "sim": 1.0})
                found = True
                break
        if not found:
            if len(tok) <= 2:
                mapped.append("·")
                explanations.append({"token": tok, "concept": None, "emoji": "·", "sim": 0.0})
            else:
                mapped.append("❓")
                explanations.append({"token": tok, "concept": None, "emoji": "❓", "sim": 0.0})
    return mapped, explanations

# ------------ بارگذاری مدل و init concept bank (آهسته) ------------
with st.spinner("در حال بارگذاری مدل و بانک مفاهیم (در صورت وجود)... ⏳"):
    model, load_err = load_model_cached()
    if model is not None:
        try:
            if init_concept_bank:
                init_concept_bank(model)
            model_status = "✅ مدل بارگذاری شد."
        except Exception as e:
            model_status = f"⚠️ مدل بارگذاری شد اما init_concept_bank خطا داد: {e}"
    else:
        model_status = f"❌ مدل بارگذاری نشد. با خطا: {load_err}"

# وضعیت مدل را نمایش بده
st.info(model_status)

# ------------ ورودی کاربر ------------
poem = st.text_area(
    "شعر خود را وارد کنید:",
    height=220,
    placeholder="مثال:\nبسی رنج بردم در این سال سی\nعجم زنده کردم بدین پارسی",
)

col1, col2 = st.columns([1, 1])
with col1:
    threshold = st.slider("آستانهٔ شباهت (similarity)", 0.30, 0.90, 0.52, 0.01)
with col2:
    show_explanations = st.checkbox("نمایش توضیحات نگاشت", value=True)

# ------------ دکمه اجرا ------------
if st.button("تبدیل کن 🚀"):
    if not poem or not poem.strip():
        st.warning("لطفاً شعری وارد کنید.")
    else:
        with st.spinner("در حال تجزیه و نگاشت معنایی..."):
            try:
                # اگر mapper اصلی موجود و مدل نیز بارگذاری شده -> از آن استفاده کن
                if map_poem_to_emojis and model is not None:
                    mapped, explanations = map_poem_to_emojis(
                        poem, model=model, similarity_threshold=threshold
                    )
                    used_engine = "semantic"
                # اگر mapper موجود اما مدل حذف/نیامد -> تلاش کن با mapper بدون مدل (ممکنه خطا بده)
                elif map_poem_to_emojis and model is None:
                    try:
                        mapped, explanations = map_poem_to_emojis(
                            poem, model=None, similarity_threshold=threshold
                        )
                        used_engine = "mapper_no_model"
                    except Exception:
                        mapped, explanations = simple_map_poem_to_emojis(poem)
                        used_engine = "fallback_simple"
                else:
                    # هیچ یک از اجزا حاضر نیست -> fallback ساده
                    mapped, explanations = simple_map_poem_to_emojis(poem)
                    used_engine = "fallback_simple"

                # نمایش خروجی
                st.subheader("🎭 خروجی ایموجی:")
                emoji_text = " ".join(mapped)
                st.markdown(
                    f"<div style='font-size:1.8em; direction: rtl; text-align: center;'>{emoji_text}</div>",
                    unsafe_allow_html=True,
                )

                # نمایش توضیحات
                if show_explanations:
                    st.subheader("🧩 توضیحات نگاشت:")
                    st.write({"engine": used_engine, "explanations": explanations})

                # ذخیرهٔ خروجی در تاریخچه فقط وقتی تبدیل موفق اجرا شد
                try:
                    history_dir = "history"
                    os.makedirs(history_dir, exist_ok=True)
                    filename = os.path.join(
                        history_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(
                            {"poem": poem, "emoji": emoji_text, "explanations": explanations, "engine": used_engine},
                            f,
                            ensure_ascii=False,
                            indent=2,
                        )
                    st.success(f"✅ خروجی ذخیره شد در فایل: {filename}")
                except Exception as e:
                    st.warning(f"خروجی تولید شد اما ذخیره نشد: {e}")

            except Exception as e:
                # لاگ خطا را در صفحه بفرست تا بتوانی دیباگ کنی
                st.error("❌ خطا در پردازش شعر — جزئیات در زیر:")
                st.text(traceback.format_exc())
