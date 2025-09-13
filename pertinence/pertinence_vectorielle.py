"""
Forme de results où on sépare les traitements
[
  {
    "treatment": "Fulvestrant",
    "node_path": "ER+ → HER2- → Visceral metastases",
    "results": [
      ("doc1.txt", 0.45),
      ("doc7.txt", 0.33),
      ...
    ]
  },
  {
    "treatment": "Palbociclib + Letrozole",
    "node_path": "ER+ → HER2- → Bone-only disease",
    "results": [
      ("doc3.txt", 0.52),
      ("doc4.txt", 0.41),
      ...
    ]
  }
]"""






import re
import math
import json
from retour_doc import extract_abstract_preview, extract_first_date, extract_first_author

import nltk
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
import string
#problèmes : patient 3 (aucune correspondance pour les mots clefs) et patient 4 : pas de mots clefs donc ne sait pas gérer ce cas


def cosine_similarity(vec1, vec2):
    # Produit scalaire
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Normes des vecteurs
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    

    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


# --- Recherche vectorielle avec similarité cosinus ---

def tfidf_vector(term_list, doc_tokens, enriched_index, doc_name=None, is_query=False):
    """Construit un vecteur TF-IDF pour un document ou une requête."""
    vector = []
    for term in term_list:
        tf_idf = 0
        if term in enriched_index:
            if is_query:
                tf = doc_tokens.count(term)
            else:
                tf = enriched_index[term].get(doc_name, (0, 0))[0] if doc_name else 0
            idf_values = []
            for val in enriched_index[term].values():
                if isinstance(val, (list, tuple)) and len(val) == 2:
                    tf_, idf = val
                    if isinstance(idf, (float, int)):
                        idf_values.append(idf)
            
            idf = sum(idf_values) / len(idf_values) if idf_values else 0
            tf_idf = tf * idf
            
        vector.append(tf_idf)
        
    return vector


def rank_documents_vectoriel(query_tokens, documents, enriched_index):
    """Classe les documents en fonction de la similarité cosinus entre la requête et chaque document."""
    all_terms = list(set(enriched_index.keys()) & set(query_tokens))
    query_vec = tfidf_vector(all_terms, query_tokens, enriched_index, is_query=True)
    

    doc_scores = []
    for doc_name, tokens in documents:
        doc_vec = tfidf_vector(all_terms, tokens, enriched_index, doc_name=doc_name)
        if not any(doc_vec):
            pass
        score = cosine_similarity(query_vec, doc_vec)
        doc_scores.append((doc_name, score))
        

    return sorted(doc_scores, key=lambda x: x[1], reverse=True)


def construire_vecteurs_documents(index):
    """
    Construit des vecteurs TF-IDF pour tous les documents à partir d'un index inversé enrichi.
    Retourne un dictionnaire : {doc_name: [vecteur tf-idf aligné avec les termes de l'index]}
    """
    termes = list(index.keys())
    vecteurs = {}

    for terme in termes:
        for doc, value in index[terme].items():
            if doc not in vecteurs:
                vecteurs[doc] = [0.0] * len(termes)
            try:
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    tf, idf = value
                    vecteurs[doc][termes.index(terme)] = tf * idf
                else:
                    vecteurs[doc][termes.index(terme)] = float(value)
            except Exception:
                pass

    return termes, vecteurs

#tokenization de la requête : idem que pour la tokenization des docs

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def preprocess_query(text):
    tokens = word_tokenize(text)
    tokens = [t.lower() for t in tokens]
    tokens = [t for t in tokens if t.isalnum()]
    tokens = [t for t in tokens if t not in stopwords.words('english')]
    tokens = lemmatization(tokens)
    return tokens


# Extraction automatique des mots-clés pertinents à partir de la sortie textuelle du script treatment_recommender.py
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
    return keywords  # conserve les doublons






def tokenize_and_clean(tokenized_text):
    tokenized_text=[t.lower() for t in tokenized_text]
    stop_words = set(stopwords.words('english'))
    tokens = [
        t for t in tokenized_text
        if t.isalnum() and t not in stop_words
    ]
    return tokens


def lemmatization(text):
    lemmatizer = WordNetLemmatizer()

    # Fonction utilitaire pour convertir POS vers WordNet
    def get_wordnet_pos(treebank_tag):
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN  # défaut

    
    tagged = pos_tag(text)      
    return [lemmatizer.lemmatize(word, get_wordnet_pos(pos)) for word, pos in tagged]

def tokenized_request(request):
    # Appeler word_tokenize(request) avant tokenize_and_clean
    word_tokenize(request)
    tokens = word_tokenize(request)
    request = lemmatization(tokenize_and_clean(tokens))
    index = {}
    for term in request:
        if term not in index:
            index[term] = 0
    for token in request:
        index[token] += 1

    return index



# --- Fonction pour trouver les documents pertinents à partir d'un fichier patient ---
def doc_pertinents_vectoriel(filename):
    with open("../indexation/index.json", "r", encoding="utf-8") as f:
        enriched_index = json.load(f)
        for term in enriched_index:
            for doc in enriched_index[term]:
                entry = enriched_index[term][doc]
                if isinstance(entry, list) and len(entry) == 2:
                    enriched_index[term][doc] = tuple(entry)

    doc_tokens = {}
    for term, doc_infos in enriched_index.items():
        for doc, (tf, _) in doc_infos.items():
            if tf > 0:
                doc_tokens.setdefault(doc, []).extend([term] * tf)

    documents = [(doc, tokens) for doc, tokens in doc_tokens.items()]

    try:
        with open(filename, "r") as f:
            patient_data = json.load(f)
    except FileNotFoundError:
        print(f"Fichier patient non trouvé : {filename}")
        return []

    if not patient_data.get("recommendations"):
        print("Aucun traitement recommandé dans ce fichier patient.")
        return []

    # Remplacement du traitement d'une seule recommandation par une boucle sur toutes les recommandations
    all_results = []
    for reco in patient_data["recommendations"]:
        node_path_cleaned = reco.get("node_path", "")
        node_path_cleaned = node_path_cleaned.replace("‑", "-").replace("→", " ").replace(">", " ")
        node_path_cleaned = " ".join(node_path_cleaned.split())

        fields = reco.get("keywords", []) + [
            reco.get("treatment", ""),
            reco.get("rationale", ""),
            reco.get("subtype", ""),
            reco.get("biomarker_summary", ""),
            node_path_cleaned
        ]
        keywords_text = " ".join(fields)

        request_index = tokenized_request(keywords_text)
        query_tokens = list(request_index.keys())
        results = rank_documents_vectoriel(query_tokens, documents, enriched_index)

        all_results.append({
            "treatment": reco.get("treatment", ""),
            "node_path": node_path_cleaned,
            "results": results
        })
    return all_results

# exemple d'appel de la fonction dans un autre script ou en fin de pertinence_vectorielle.py
results = doc_pertinents_vectoriel("/Users/adele/Documents/CS/EI_ST4/carjac/recommendations/recommendations_MBC_005.json")

# Afficher les résultats de manière lisible
for reco in results:
    print(f"\nTraitement proposé : {reco['treatment']}")
    print(f"Chemin de décision : {reco['node_path']}")
    for doc, score in reco["results"]:
        print(f"{doc} → Score : {score:.4f}")



