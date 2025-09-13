import sys
import json

# --- BM25 functions ---
from collections import defaultdict

import re
import string

def simple_tokenize(text):
    # Enlève la ponctuation et met en minuscules
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    return text.split()

def tokenize_and_clean(text):
    # Enlève les mots vides manuellement (sans NLTK)
    stopwords = {"and", "or", "the", "of", "a", "in", "on", "to", "for", "is", "with", "by"}
    return [word for word in simple_tokenize(text) if word and word not in stopwords]

def lemmatization(tokens):
    # Pas de lemmatization réelle ici pour rester simple
    return tokens  # Optionnel : ajoute un stemming très simple si besoin

 #Extraction automatique des mots-clés pertinents à partir de la sortie textuelle du script treatment_recommender.py
def extract_query_terms_from_output(output_text):
    """
    Extrait les mots-clés et noms de médicaments depuis le texte de sortie de treatment_recommender.py.
    """
    keywords = []
    in_keywords = False
    for line in output_text.split('\n'):
        line = line.strip()
        if line.startswith("Keywords:"):
            in_keywords = True
            keyword_line = line[len("Keywords:"):].strip()
            keywords.extend([kw.strip().lower() for kw in keyword_line.split(',') if kw.strip()])
        elif in_keywords:
            if line.startswith("Decision Path:") or not line:
                in_keywords = False
            else:
                keywords.extend([kw.strip().lower() for kw in line.split(',') if kw.strip()])
    text = " ".join(keywords)
    tokens = tokenize_and_clean(text)
    return lemmatization(tokens)

def bm25_score(query_tokens, doc_tf, doc_len, avg_doc_len, idf, k=1.5, b=0.75):
    score = 0.0
    for term in query_tokens:
        if term not in idf or term not in doc_tf:
            continue
        tf = doc_tf[term]
        numerator = tf * (k + 1)
        denominator = tf + k * (1 - b + b * (doc_len / avg_doc_len))
        score += idf[term] * (numerator / denominator)
    return score

def rank_documents_bm25(query_tokens, documents, enriched_index):
    """
    query_tokens : liste de tokens de la requête
    documents : liste de (nom_doc, liste_tokens)
    enriched_index : {terme: {doc_name: (tf, idf), ...}, ...}
    """
    N = len(documents)
    avg_doc_len = sum(len(tokens) for _, tokens in documents) / N

    doc_scores = []

    for doc_name, tokens in documents:
        score = 0.0
        doc_len = len(tokens)
        for term in query_tokens:
            if term not in enriched_index:
                continue
            if doc_name not in enriched_index[term]:
                continue
            tf, idf = enriched_index[term][doc_name]
            numerator = tf * (1.5 + 1)
            denominator = tf + 1.5 * (1 - 0.75 + 0.75 * doc_len / avg_doc_len)
            partial_score = idf * (numerator / denominator)
            #print(f"Doc: {doc_name}, Term: '{term}' → tf: {tf}, idf: {idf:.3f}, score: {partial_score:.4f}")
            score += partial_score

        doc_scores.append((doc_name, score))


    return sorted(doc_scores, key=lambda x: x[1], reverse=True)

def rank_boolean_results(query_terms, matching_docs, index):
    scores = []
    for doc in matching_docs:
        score = sum(1 for term in query_terms if doc in index.get(term, {}))
        scores.append((doc, score))
    return sorted(scores, key=lambda x: x[1], reverse=True)


# --- Evidence Curator ---
def evidence_curator(query_tokens, documents, enriched_index, top_k=15):
    """
    Classe les documents par pertinence et sélectionne les top_k documents.
    """
    ranked = rank_documents_bm25(query_tokens, documents, enriched_index)
    return ranked[:top_k]


if __name__ == "__main__":
    with open("index.json", "r") as f:
        enriched_index = json.load(f)

    # Construire les documents
    doc_tokens = {}
    for term, doc_data in enriched_index.items():
        for doc_name in doc_data:
            doc_tokens.setdefault(doc_name, []).append(term)

    documents = [(doc, tokens) for doc, tokens in doc_tokens.items()]

    