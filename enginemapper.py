# engine/mapper.py
from enginepreprocessing import tokenize
from engineconcept_bank import ConceptBank


cb = None


def init_concept_bank(model=None):
    global cb
    cb = ConceptBank(model=model)
    return cb


def map_poem_to_emojis(poem, model=None, similarity_threshold=0.52):
    if cb is None:
        init_concept_bank(model)
    tokens = tokenize(poem)
    mapped = []
    explanations = []
    for t in tokens:
    # نادیده‌گیری حروف ربط کوتاه
        if len(t.strip()) == 0:
            continue
    # جستجوی بهترین کانسپت
        results = cb.find_best(t, top_k=3)
        best_concept, best_score = None, 0.0
        if results:
            best_concept, best_score = results[0]
        if best_score >= similarity_threshold and best_concept:
            emojis = best_concept.get("emoji", ["❓"])
            mapped.append(emojis[0])
            explanations.append({"token": t, "concept": best_concept["id"], "label": best_concept["label"], "sim": best_score, "emoji": emojis})
        else:
            if len(t) <= 2:
                mapped.append("·")
                explanations.append({"token": t, "concept": None, "label": "connector/stop", "sim": best_score, "emoji": "·"})
            else:
                mapped.append("❓")
                explanations.append({"token": t, "concept": None, "label": "unknown", "sim": best_score, "emoji": "❓"})
    return mapped, explanations