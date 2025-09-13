

# """
# Forme de results : 
# [
#   {
#     "treatment": "Sacituzumab Govitecan",
#     "node_path": "Metastatic Breast Cancer → TNBC → Second-line",
#     "results": [
#       ("PMID_38658447_breast_cancer.pdf", 0.9987),
#       ("PMID_39966355_treatment_analysis.pdf", 0.9979),
#       ...
#     ]
#   },
#   {
#     "treatment": "Pembrolizumab",
#     "node_path": "Metastatic Breast Cancer → TMB-high",
#     "results": [
#       ("PMID_40169605_pembrolizumab_msi.pdf", 0.9961),
#       ...
#     ]
#   }
# ]"""


# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import json
# from gensim.models import Word2Vec
# from gensim.utils import simple_preprocess
# from nltk.corpus import stopwords
# from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np
# from django.conf import settings


# STOPWORDS = set(stopwords.words('english'))



# import fitz  # PyMuPDF
# import re


# # Extraction automatique des mots-clés pertinents à partir de la sortie textuelle du script treatment_recommender.py
# def extract_query_terms_from_output(output_text):
#     """
#     Extrait les mots-clés et noms de médicaments depuis le texte de sortie de treatment_recommender.py.
#     """
#     keywords = []
#     in_keywords = False
#     for line in output_text.split('\n'):
#         line = line.strip()
#         if line.startswith("Keywords:"):
#             in_keywords = True
#             keyword_line = line[len("Keywords:"):].strip()
#             keywords.extend([kw.strip().lower() for kw in keyword_line.split(',') if kw.strip()])
#         elif in_keywords:
#             if line.startswith("Decision Path:") or not line:
#                 in_keywords = False
#             else:
#                 keywords.extend([kw.strip().lower() for kw in line.split(',') if kw.strip()])
#     return keywords  # conserve les doublons


# def preprocess_text(text):
#     return [word.lower() for word in re.findall(r'\b\w+\b', text)]

# def train_word2vec_model(docs):
#     model = Word2Vec(sentences=docs, vector_size=100, window=5, min_count=1, workers=4)
#     return model

# def vectorize_document(model, doc, index, total_docs):
#     # doc is a list of tokens
#     tf = {}
#     for token in doc:
#         if token in model.wv:
#             tf[token] = tf.get(token, 0) + 1

#     doc_vec = np.zeros(model.vector_size)
#     weight_sum = 0

#     for token, freq in tf.items():
#         if token in model.wv and token in index:
#             df = len(index[token])
#             idf = np.log((total_docs + 1) / (df + 1)) + 1
#             weight = freq * idf
#             doc_vec += model.wv[token] * weight
#             weight_sum += weight

#     if weight_sum == 0:
#         return doc_vec
#     return doc_vec / weight_sum

# def load_documents_from_index(index_path):
#     with open(os.path.join(settings.BASE_DIR, index_path), 'r') as f:
#         index = json.load(f)
#     doc_texts = {}
#     for term, postings in index.items():
#         for doc, (tf, _) in postings.items():
#             doc_texts.setdefault(doc, []).extend([term] * tf)
#     return doc_texts  # retourne dict[str, list[str]]

# def find_similar_documents(query, index_path):
#     documents = load_documents_from_index(index_path)
#     model = train_word2vec_model(list(documents.values()))
#     index = json.load(open(index_path))
#     total_docs = len({doc for postings in index.values() for doc in postings})
#     query_tokens = preprocess_text(query)
#     query_vec = vectorize_document(model, query_tokens, index, total_docs)

#     results = []
#     for doc_name, content in documents.items():
#         doc_vec = vectorize_document(model, content, index, total_docs)
#         sim = cosine_similarity([query_vec], [doc_vec])[0][0]
#         results.append((doc_name, sim))

#     return sorted(results, key=lambda x: x[1], reverse=True)

# def build_query_text_from_keywords(patient_data):
#     """
#     Prend un dictionnaire patient contenant une clé 'recommendations'
#     et retourne une liste de tuples (treatment, path, query_text) au bon format.
#     Si aucun mot-clé n’est disponible, la requête est ignorée.
#     """
#     formatted_recommendations = []
#     if isinstance(patient_data, str):
#         patient_data = json.loads(patient_data)
#     for rec in patient_data.get("recommendations", []):
#         keywords = rec.get("keywords", [])
#         if not keywords:
#             continue  # Ignore les recommandations sans mots-clés
#         query_text = "Keywords: " + ", ".join(keywords)
#         formatted_recommendations.append((
#             rec["treatment"],
#             rec["node_path"],
#             query_text
#         ))
#     return formatted_recommendations

# def run_word2vec_recommendations(patient_recommendations):
#     index_file_path = "/carjac/indexation/index.json"
#     with open(patient_recommendations, 'r') as f:
#         patient_data = json.load(f)
#     treatments_with_paths = build_query_text_from_keywords(patient_data)
#     """
#     Arguments:
#         treatments_with_paths: list of tuples (treatment_name, node_path, query_text)
#         index_file_path: str, path to index.json

#     Returns:
#         list of dicts:
#             {
#                 "treatment": str,
#                 "node_path": str,
#                 "results": list of tuples (doc_name, score)
#             }
#     """
#     output = []
#     for treatment, path, query_text in treatments_with_paths:
#         results = find_similar_documents(query_text, index_file_path)
#         top_docs = results[:5]


#         output.append({
#             "treatment": treatment,
#             "node_path": path,
#             "results": top_docs
#         })

#     return output



# """Bloc de test"""
# if __name__ == "__main__":



#     # Appel à la fonction avec le bon chemin vers l’index
#     results = run_word2vec_recommendations("/Users/adele/Documents/CS/EI_ST4/carjac/recommendations/recommendations_MBC_003.json")

#     for group in results:
#         print(f"\nTreatment: {group['treatment']}")
#         print(f"Node path: {group['node_path']}")
#         for doc_name, score in group["results"]:
#             print(f"{doc_name} → Score: {score:.4f}")

""""