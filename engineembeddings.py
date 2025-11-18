# engine/embeddings.py
import sentence_transformers
import numpy

_model = None


def load_model():
    local_path = "models/paraphrase-multilingual-MiniLM-L12-v2"
    try:
        model = sentence_transformers.SentenceTransformer(local_path)
    except:
        model = sentence_transformers.SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        model.save(local_path)
    return model


def embed_texts(texts, model=None):
    model = model or load_model()
    vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # normalize
    norms = numpy.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    return vecs / norms