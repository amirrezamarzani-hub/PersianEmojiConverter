# engine/preprocessing.py
from hazm import Normalizer, word_tokenize
import re


normalizer = Normalizer()


def normalize_text(text: str) -> str:
    t = normalizer.normalize(text)
    # حذف کوتیشن‌ها و کاراکترهای خاص غیرضروری
    t = re.sub(r"[«»\"]", "", t)
    # حذف بیش از یک فاصله
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def tokenize(text: str):
    t = normalize_text(text)
    # ابتدا عبارات مرکب موجود در data/phrases.txt می‌توانند جایگزین شوند (پیاده‌سازی بعدی)
    return word_tokenize(t)