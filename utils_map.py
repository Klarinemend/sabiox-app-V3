# utils_map.py
from __future__ import annotations
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOPWORDS = {
    "a","o","os","as","um","uma","uns","umas","de","do","da","dos","das","em","no","na","nos","nas",
    "e","ou","para","por","com","sem","sobre","entre","ao","aos","à","às","que","se","ser","estar",
    "deve","devem","permitir","permite","permitam","sistema","aplicacao","aplicativo","usuario","usuarios"
}

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def tokenize_to_str(text: str) -> str:
    """Modificado para retornar string limpa para o TfidfVectorizer"""
    text = strip_accents((text or "").lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    toks = [t for t in text.split() if t and t not in STOPWORDS and len(t) >= 3]
    return " ".join(toks)


def map_fr_to_cq(fr_list, cq_list, top_k=2, threshold=0.18):
    if not fr_list or not cq_list:
        return fr_list

    cq_texts = [cq['question'] for cq in cq_list]
    cq_ids = [cq['id'] for cq in cq_list]

    vectorizer = TfidfVectorizer()
    all_texts = cq_texts + [fr['description'] for fr in fr_list]
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    cq_vectors = tfidf_matrix[:len(cq_list)]
    fr_vectors = tfidf_matrix[len(cq_list):]

    for i, fr in enumerate(fr_list):

        # Procura por "CQ-01", "CQ 01", "[CQ-01]" no texto do FR
        found_ids = re.findall(r'CQ-?\s?(\d+)', fr['description'], re.IGNORECASE)
        
        # Converte os números achados de volta para o formato "CQ-01"
        explicit_links = [f"CQ-{int(num):02d}" for num in found_ids]
        

        similarities = cosine_similarity(fr_vectors[i], cq_vectors).flatten()
        related_indices = similarities.argsort()[::-1]
        
        ai_links = []
        for idx in related_indices:
            if similarities[idx] >= threshold and len(ai_links) < top_k:
                ai_links.append(cq_ids[idx])

        # Une as duas listas e remove duplicatas
        # Prioriza o que a IA escreveu explicitamente no relatório
        fr['related_cq'] = list(dict.fromkeys(explicit_links + ai_links))

    return fr_list