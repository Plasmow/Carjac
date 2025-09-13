import sys
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import fitz  
from pathlib import Path

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDINGS_FILE = "doc_embeddings.pkl"

def process_patient_file(patient_file):
    print("Chargement du modèle d'embedding pour la requête...")
    model = SentenceTransformer(MODEL_NAME)
    # Chargement des embeddings des documents
    with open(EMBEDDINGS_FILE, "rb") as f:
        doc_embeddings = pickle.load(f)
    doc_names = list(doc_embeddings.keys())
    doc_vectors = list(doc_embeddings.values())
    print("Bienvenue ! Tapez vos mots-clés pour rechercher les articles pertinents (ou 'exit' pour quitter).")

    # Fonction pour générer une requête optimisée (version ultra simplifiée sans LLM)
    def generate_optimized_query(keywords):
        return " ".join(keywords.split())

    # Si patient_file est fourni, on le traite une fois comme entrée utilisateur
    if patient_file.lower().endswith(".json"):
        try:
            import json
            with open(patient_file, "r") as f:
                patient_data = json.load(f)
        except Exception as e:
            print(f"Erreur d'ouverture ou de lecture du fichier : {e}")
            return
        if not patient_data.get("recommendations"):
            print("❌ Aucun traitement recommandé dans ce fichier.")
            return

        reco = patient_data["recommendations"][0]
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
        raw_text = " ".join(fields)
        user_input = raw_text
    else:
        raw_text = patient_file
        user_input = raw_text

    # Extraction de mots à partir du texte brut
    keywords = [t.strip(" .,…") for t in raw_text.split()]

    # Permet à l'utilisateur d'assigner des poids : metastatic:2 tel:1
    terms = user_input.split()
    weighted_terms = []
    for term in terms:
        if ":" in term:
            word, weight = term.split(":")
            try:
                weight = float(weight)
            except ValueError:
                weight = 1.0
        else:
            word = term
            weight = 1.0
        weighted_terms.extend([word] * int(weight))
    weighted_query = " ".join(weighted_terms)

    query = generate_optimized_query(weighted_query)
    print(f"\nRequête générée : {query}\n")

    query_embedding = model.encode(query)
    similarities = cosine_similarity([query_embedding], doc_vectors)[0]

    # Top 5 documents
    top_docs = sorted(zip(doc_names, similarities), key=lambda x: x[1], reverse=True)[:5]

    # --- Analyse métadonnées sémantiques et temporelles ---
    import datetime

    
    current_year = datetime.datetime.now().year

    def recency_weight(year, current_year, min_year=2015):
        if not year or year < min_year:
            return 0
        # pondération linéaire décroissante de 1 (année actuelle) à 0.5 (min_year)
        return 0.5 + 0.5 * ((year - min_year) / (current_year - min_year)) if current_year > min_year else 1.0

    # --- Fin analyse métadonnées ---

    # Filtrer les documents validés
    VALIDATION_THRESHOLD = 0.2
    NON_REDUNDANCY_THRESHOLD = 0.9

    validated_docs = []
    for name, score in top_docs:
        year_str = extract_first_date(str(Path("pubmed_articles") / name))
        try:
            year = int(re.search(r"\d{4}", year_str).group()) if year_str else None
        except:
            year = None

        if year and year < 2015:
            continue  # on ignore les vieux documents

        if score < VALIDATION_THRESHOLD:
            continue

        combined_score = score * recency_weight(year, current_year)

        is_redundant = any(
            cosine_similarity([doc_embeddings[name]], [doc_embeddings[existing]])[0][0] > NON_REDUNDANCY_THRESHOLD
            for existing, _ in validated_docs
        )
        if not is_redundant:
            validated_docs.append((name, combined_score))

    # trier les documents validés par score combiné
    validated_docs = sorted(validated_docs, key=lambda x: x[1], reverse=True)

    print("Top documents les plus pertinents :")
    for name, combined_score in validated_docs:
        pdf_path = Path("pubmed_articles") / name
        publication_date = extract_first_date(str(pdf_path))
        print(f"{name} → Date : {publication_date} | Score combiné : {combined_score:.4f}")

    if not validated_docs:
        print("⚠️ Aucun document validé. Voici les scores et années des documents proposés :")
        for name, score in top_docs:
            year = extract_year_from_filename(name)
            adjusted_score = score * recency_weight(year, current_year)
            print(f"{name} ({year}) → Score : {score:.4f} | Score ajusté : {adjusted_score:.4f}")

def extract_first_date(pdf_path):
    doc = fitz.open(pdf_path)
    text_all = ""
    
    # Parcours des 2 premières pages pour trouver la date
    for page_num in range(min(2, len(doc))):
        page = doc[page_num]
        text_all += page.get_text() + "\n"
    
    doc.close()

    # Normaliser le texte
    text_all_lower = text_all.lower()

    # Mots-clés typiques qui précèdent la date
    keywords = ["received", "accepted", "published", "available online"]
    date_regex = r'(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{4}|\d{4})'
    
    for keyword in keywords:
        idx = text_all_lower.find(keyword)
        if idx != -1:
            snippet = text_all[idx:idx+100]
            match = re.search(date_regex, snippet)
            if match:
                return match.group(0).strip()
    
    return "Aucune date trouvée."


# Ancienne boucle interactive déplacée dans une fonction si besoin
def main_interactive():
    print("Chargement du modèle d'embedding pour la requête...")
    model = SentenceTransformer(MODEL_NAME)
    # Chargement des embeddings des documents
    with open(EMBEDDINGS_FILE, "rb") as f:
        doc_embeddings = pickle.load(f)
    doc_names = list(doc_embeddings.keys())
    doc_vectors = list(doc_embeddings.values())
    print("Bienvenue ! Tapez vos mots-clés pour rechercher les articles pertinents (ou 'exit' pour quitter).")

    def generate_optimized_query(keywords):
        return " ".join(keywords.split())

    while True:
        user_input = input("\nEntrez vos mots-clés (ou 'exit') : ").strip()
        if user_input.lower() == "exit":
            print("Fin de la session.")
            break

        if user_input.lower().endswith(".json") or "Treatment Recommendations" in user_input:
            if user_input.endswith(".json") and os.path.exists(user_input):
                with open(user_input, "r") as f:
                    raw_text = f.read()
            else:
                raw_text = user_input

            keyword_lines = re.findall(r"(?i)Keywords:\s*(.+)", raw_text)
            if not keyword_lines:
                keyword_lines = re.findall(r"(?i)Rationale:\s*(.*?)\n", raw_text)
            keywords = []
            for line in keyword_lines:
                terms = [t.strip(" .,…") for t in line.split(",")]
                keywords.extend(terms)
            important_keywords = ["metastatic", "alpelisib", "fulvestrant", "PI3K", "mTOR", "breast cancer"]
            weighted_terms = []
            for kw in keywords:
                weight = 2 if any(imp in kw.lower() for imp in important_keywords) else 1
                weighted_terms.extend([kw] * weight)
            user_input = " ".join(weighted_terms)
            print(f"\n Mots-clés extraits automatiquement : {user_input}")

        terms = user_input.split()
        weighted_terms = []
        for term in terms:
            if ":" in term:
                word, weight = term.split(":")
                try:
                    weight = float(weight)
                except ValueError:
                    weight = 1.0
            else:
                word = term
                weight = 1.0
            weighted_terms.extend([word] * int(weight))
        weighted_query = " ".join(weighted_terms)

        query = generate_optimized_query(weighted_query)
        print(f"\nRequête générée : {query}\n")

        query_embedding = model.encode(query)
        similarities = cosine_similarity([query_embedding], doc_vectors)[0]
        top_docs = sorted(zip(doc_names, similarities), key=lambda x: x[1], reverse=True)[:5]
        import datetime
        def extract_year_from_filename(name):
            match = re.search(r'PMID_(\d{8})', name)
            if match:
                pmid = match.group(1)
                year_prefix = int(pmid[:2])
                year = 2000 + (year_prefix if year_prefix < 50 else year_prefix - 100)
                return year
            return None
        current_year = datetime.datetime.now().year
        def recency_weight(year, current_year, min_year=2015):
            if not year or year < min_year:
                return 0
            return 0.5 + 0.5 * ((year - min_year) / (current_year - min_year)) if current_year > min_year else 1.0
        VALIDATION_THRESHOLD = 0.2
        NON_REDUNDANCY_THRESHOLD = 0.9
        validated_docs = []
        for name, score in top_docs:
            year = extract_year_from_filename(name)
            if year and year < 2015:
                continue
            if score < VALIDATION_THRESHOLD:
                continue
            combined_score = score * recency_weight(year, current_year)
            is_redundant = any(
                cosine_similarity([doc_embeddings[name]], [doc_embeddings[existing]])[0][0] > NON_REDUNDANCY_THRESHOLD
                for existing, _ in validated_docs
            )
            if not is_redundant:
                validated_docs.append((name, combined_score))
        validated_docs = sorted(validated_docs, key=lambda x: x[1], reverse=True)
        print("Top documents les plus pertinents :")
        for name, combined_score in validated_docs:
            year = extract_year_from_filename(name)
            print(f"{name} ({year}) → Score combiné : {combined_score:.4f}")
        if not validated_docs:
            print("Aucun document validé. Voici les scores et années des documents proposés :")
            for name, score in top_docs:
                year = extract_year_from_filename(name)
                adjusted_score = score * recency_weight(year, current_year)
                print(f"{name} ({year}) → Score : {score:.4f} | Score ajusté : {adjusted_score:.4f}")


# Ajout de l'appel explicite à la fin du fichier
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_patient_file(sys.argv[1])
    else:
        print("Usage: python llm_pertinence_v1.py <fichier_patient.json>")