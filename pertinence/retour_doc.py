import fitz  # PyMuPDF
import re
import requests
from xml.etree import ElementTree as ET

def extract_abstract_preview2(pdf_path, n_words=100):
    doc = fitz.open(pdf_path)
    abstract_text = ""

    for page_num in range(min(3, len(doc))):
        page = doc[page_num]
        text = page.get_text()

        # Version normalisée : minuscule, espaces multiples remplacés par un seul espace
        clean_text = re.sub(r'\s+', ' ', text).lower()

        # Cherche "abstract" ou "a b s t r a c t"
        start_idx = -1
        if "abstract" in clean_text:
            start_idx = clean_text.find("abstract")
        elif "a b s t r a c t" in clean_text:
            start_idx = clean_text.find("a b s t r a c t")

        if start_idx != -1:
            # Reprend la même position dans le texte original pour capturer la mise en forme originale
            original_text = re.sub(r'\s+', ' ', text)
            abstract_text = original_text[start_idx:].strip()
            break

    doc.close()

    if not abstract_text:
        return "Aucun abstract trouvé."

    # Limiter aux 100 premiers mots
    words = abstract_text.split()
    first_100_words = ' '.join(words[:n_words]) + ('...' if len(words) > n_words else '')

    return first_100_words


def extract_abstract_preview(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        abstract_text = root.find(".//AbstractText")
        if abstract_text is not None:
            return abstract_text.text.strip()
    return "Aucun abstract trouvé."


def extract_first_date2(pdf_path):
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



def extract_first_author(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        author_list = root.find(".//AuthorList")
        if author_list is not None:
            first_author = author_list.find("Author")
            if first_author is not None:
                last = first_author.find("LastName").text
                first = first_author.find("ForeName").text
                return f"{first} {last} et al."
    return "Auteur non trouvé."

def extract_first_date(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        date_elem = root.find(".//PubDate")
        if date_elem is not None:
            # Essaie de trouver l'année complète ou le mois + année
            year = date_elem.find("Year")
            month = date_elem.find("Month")
            if year is not None and month is not None:
                return f"{month.text} {year.text}"
            elif year is not None:
                return year.text
    return "Aucune date trouvée."

def doc_description(Doc_name):
    Doc_score=[]
    for i in range(len(Doc_name)):
        Doc_score.append(Doc_name[i][1])
    Doc_author=[]
    Doc_date=[]
    Doc_abstract=[]
    for i in range(5):
        pdf_file = "pubmed_articles/" + Doc_name[i][0]
        Doc_abstract.append(extract_abstract_preview(pdf_file))
        Doc_date.append(extract_first_date(pdf_file))
        Doc_author.append(extract_first_author(pdf_file))
    return Doc_abstract, Doc_date, Doc_author, Doc_score

def extract_title_from_filename(filename):
    if filename.endswith('.pdf'):
        filename = filename[:-4]
    parts = filename.split('_')
    if len(parts) > 2: #on enleve le PMID + le num du doc
        title_parts = parts[2:]
        title = ' '.join(title_parts)
        return title
    else:
        return "Titre non trouvé"
