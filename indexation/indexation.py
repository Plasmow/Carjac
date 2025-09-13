import nltk
import os
import fitz  # PyMuPDF
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import xml.etree.ElementTree as ET
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
import json

# -----------------------------
# Chargement des PDF
# -----------------------------
def load_pdf_corpus(folder_path):
    corpus = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            path = os.path.join(folder_path, filename)
            with fitz.open(path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                corpus[filename] = text
    return corpus

def tokenize_corpus(corpus):
    return {name:word_tokenize(text) for name, text in corpus.items()}

# -----------------------------
# Application
# -----------------------------



def read_corpus():
    
    folder = "pubmed_articles"
    corpus = load_pdf_corpus(folder)
    tokenized_corpus = tokenize_corpus(corpus)
    
    return tokenized_corpus



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




#Extraction du vocabulaire


def inverted_index():
    tokenized_corpus = read_corpus()
    tokenized_corpus = {name : tokenize_and_clean(text) for name,text in tokenized_corpus.items()}
    tokenized_corpus = {name : lemmatization(text) for name,text in tokenized_corpus.items()}
    
    index={}
    N=len(tokenized_corpus)
    idf={}
    for doc, text in tokenized_corpus.items():
        for term in text:
            if term not in index:
                index[term]={}
                idf[term] = 0
    for doc,tokens in tokenized_corpus.items():
        for token in tokens:
            if token in index:
                if doc in index[token]:
                    index[token][doc]+=1
                else:
                    index[token][doc]=1
                idf[token]+=1
    idf = dict(sorted(idf.items(), key=lambda item: item[1], reverse=True))
    
    idf = dict(list(idf.items())[1000:])
    idf={name:np.log(N/x) for name,x in idf.items() if x!=0}
    
    final_index={term:{ doc_name:(tf,idf[term]) for doc_name,tf in index[term].items() } for term in idf}
    return(final_index)





def save_inverted_index(index, index_path="indexation/index.json"):
    # Sauvegarde le dictionnaire d'index inversé
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)




if __name__ == "__main__":
    index = inverted_index()
    save_inverted_index(index)






def vocab_relevance():
    index=inverted_index()
    return({name:value for name,value in index.items() if value!={}})

