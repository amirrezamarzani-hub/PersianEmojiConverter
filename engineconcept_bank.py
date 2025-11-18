# engineconcept_bank.py
# یا اگر ساختار پروژه‌ات engine/concept_bank.py است،
# نام فایل را به concept_bank.py تغییر بده و این محتوا را قرار بده.

import json
import os
from engineembeddings import embed_texts, load_model  # اگر نام ماژولت engine.embeddings است، خط را اصلاح کن
# اگر در پروژه‌ات فایل embeddings در مسیر engine/ بود، از: from engine.embeddings import embed_texts, load_model
# اگر نام فایلهای تو متفاوت است (مثلاً engineembeddings.py)، این import را مطابق نام فایلت تنظیم کن.

import numpy as np

# مسیر پیش‌فرض فایل concepts.json — در صورت نیاز آن را اصلاح کن
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "concepts.json")

class ConceptBank:
    def __init__(self, model=None, concepts_path=None):
        """
        model: instance of SentenceTransformer (یا معادل)
        concepts_path: مسیر دلخواه به فایل concepts.json (اختیاری)
        """
        self.model = model or load_model()
        if concepts_path:
            self.data_path = concepts_path
        else:
            # مسیر نسبت به این فایل
            self.data_path = DATA_PATH
        self.concepts = []
        self.vecs = None
        # بارگذاری کانسپت‌ها
        self.load()

    def load(self):
        """بارگذاری JSON کانسپت‌ها و ساخت بردارهای میانگین برای هر کانسپت"""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Concept file not found: {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.concepts = json.load(f)
        self._build_vectors()

    def _build_vectors(self):
        """برای هر کانسپت، بردار میانگین نمونه‌ها را می‌سازد و نرمالایز می‌کند"""
        texts = []
        for c in self.concepts:
            samples = c.get("examples", [])
            if not samples:
                samples = [c.get("label", "")]
            # join نمونه‌ها تا بتوانیم یک embedding میانگین بگیریم
            texts.append(" . ".join(samples))
        if len(texts) == 0:
            self.vecs = np.zeros((0, 768))
            return
        self.vecs = embed_texts(texts, self.model)  # انتظار می‌رود embed_texts نرمالایز هم برگرداند
        # اگر embed_texts خروجی نرمالایز نشده برگرداند، نرمالایز می‌کنیم:
        norms = np.linalg.norm(self.vecs, axis=1, keepdims=True) + 1e-9
        self.vecs = self.vecs / norms

    def find_best(self, text, top_k=3):
        """برای یک متن (کلمه/عبارت)، نزدیک‌ترین کانسپت‌ها را برمی‌گرداند"""
        if self.vecs is None or len(self.vecs) == 0:
            return []
        v = embed_texts([text], self.model)[0]
        v = v / (np.linalg.norm(v) + 1e-9)
        sims = (self.vecs @ v)
        idxs = np.argsort(-sims)[:top_k]
        results = []
        for i in idxs:
            results.append((self.concepts[i], float(sims[i])))
        return results

    def add_concept(self, concept: dict):
        """اضافه کردن کانسپت جدید و بازسازی بردارها"""
        self.concepts.append(concept)
        self._build_vectors()

    def save(self, path=None):
        """ذخیرهٔ concepts به فایل JSON"""
        save_path = path or self.data_path
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.concepts, f, ensure_ascii=False, indent=2)
