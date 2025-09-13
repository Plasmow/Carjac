import json
from drug_gene_interactions.genes_treatment import *
from pertinence.pertinence_vectorielle import *
from pertinence.pertinence_word2vec import *
from pertinence.retour_doc import *


def interaction(dico):
    medic_vu = {}
    for medic, liste in dico.items():
        for gene, interaction, bdd, date in liste:
            if interaction == "NULL":
                medic_vu[medic] = True
                print(f"No interaction found for {medic} on {gene}. Source : {bdd} Date : {date}")
            else:
                medic_vu[medic] = True
                print(f"Drug {medic} has {interaction} effect on {gene}. Source : {bdd} Date : {date}")
    for medic in dico.keys():
        if medic not in medic_vu:
            print(f"{medic} has no effect on biomarkers")

def message(dico_traitements, dico, genes_desc, docs_abstract, docs_date, docs_name):
    print("Tested biomarkers : ")
    genes_vu = {}
    for gene, (type, desc) in genes_desc.items():
        print(f"{gene} ({type}) : {desc}")
    print()
    for traitement, (evidence_level, recommendation_strength, rationale) in dico_traitements.items():
        
        print(f"traitement recommandé : {traitement}, evidence level : {evidence_level}, recommendation strength : {recommendation_strength}")
        print(rationale)
        print()
    interaction(dico)
    print()
    print("Documents supplémentaires : ")

    for i in range(len(docs_abstract)):
        print(f"{docs_name[i]}, date : {docs_date[i]}")   
        print()
        print(f"{docs_abstract[i]}")


#output file est le fichier json recommendation_MBC_001
def json_message(output_file, patient_id):
    
    with open(output_file, "r") as f:
        data = json.load(f)
    reco = data["recommendations"]
    #utilisation du modèle vectoriel
    docs = doc_pertinents_vectoriel(output_file)
    #utilisation du modèle word2wec
    #docs = run_word2vec_recommendations(output_file)
    recommendations = {}
    dico, genes_desc = gene_interaction(output_file)
    print(len(reco))
    for i in range(len(reco)):
        dico_traitements = {}
        dico_traitements['treatment_title'] = reco[i]['treatment']
        dico_traitements['evidence_level'] = reco[i]['evidence_level']
        dico_traitements['recommendation_strength'] = reco[i]['recommendation_strength']
        dico_traitements['rationale'] = reco[i]['rationale']
        dico_traitements['description_genes'] = []
        
        for gene, (type, desc) in genes_desc.items():
            dico_aux = {}
            dico_aux['gene'] = gene
            dico_aux['type'] = type
            dico_aux['desc'] = desc
            dico_traitements['description_genes'].append(dico_aux)
            
        dico_traitements['interaction'] = []
        dico_aux = {}
        for medic, liste in dico[i].items():
            dico_aux[medic] = {}
            for genes, type, bdd, date in liste:
                dico_aux[medic]['gene'] = gene
                dico_aux[medic]['type'] = type
                dico_aux[medic]['source'] = bdd
                dico_aux[medic]['date'] = date
        dico_traitements['interaction'].append(dico_aux)
        dico_traitements['docs'] = []
        for elem in docs:
            if elem['treatment'] == reco[i]['treatment']:
                docs_abstract, docs_date, docs_author, docs_score = doc_description(elem['results'])
                # Itérer sur chaque doc pour associer titre, date et abstract ensemble
                for j in range(len(docs_author)):
                    dico_aux_doc = {}
                    dico_aux_doc['traitement'] = elem['treatment']
                    dico_aux_doc['doc_author'] = docs_author[j] if j < len(docs_author) else "Aucun auteur trouvé."
                    dico_aux_doc['date'] = docs_date[j] if j < len(docs_date) else "Aucune date trouvée."
                    dico_aux_doc['abstract'] = docs_abstract[j] if j < len(docs_abstract) else "Aucun abstract trouvé."
                    dico_aux_doc['title'] =  extract_title_from_filename(elem['results'][j][0]) if j < len(elem['results']) else "Aucun titre trouvé"
                    dico_aux_doc['score'] = docs_score[j] if j < len(docs_score) else "Aucun score trouvé"
                    print(dico_aux_doc['title'])
                    dico_traitements['docs'].append(dico_aux_doc)

        recommendations[f'traitement {i}'] = dico_traitements

    with open(f"affichage_{patient_id[4:]}.json", "w", encoding="utf-8") as f:
        json.dump(recommendations, f, indent=4, ensure_ascii=False)




    
    
    
    

def main():
    file = "recommendations_MBC_005.json"
    with open(file, "r") as f:
        data = json.load(f)
    f.close()
    reco = data["recommendations"]
    dico_traitements = {}
    for i in range(len(reco)):
        dico_traitements['treatment_title'] = reco[i]['treatment']
        dico_traitements['evidence_level'] = reco[i]['evidence_level']
        dico_traitements['recommendation_strength'] = reco[i]['recommendation_strength']
        dico_traitements['rationale'] = reco[i]['rationale']

    

    dico, genes_desc = gene_interaction(file)
    docs = doc_pertinents_vectoriel(file)
    docs_abstract, docs_date, docs_name = doc_description(docs) 
    message(dico_traitements, dico, genes_desc, docs_abstract, docs_date, docs_name)

    


