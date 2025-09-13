
# But : créer une fonction qui prend en entrée le traitement recommandé pour un patient et qui renvoie
# les gènes qui sont en interaction avec ce traitement

import json
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Ne pas se limiter sur l'affichage des colonnes pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)  


def traitements_proposes(reco_data,path):
# Renvoie une liste de liste avec les médicaments pour chaque traitement
    with open(path, "r") as f:
        data = json.load(f)
    reco = data["recommendations"]
    traitements = [reco[i]['treatment'] for i in range(len(reco))]
    return [traitements[i].split(' + ') for i in range(len(traitements))]



def biomarkers_genes(reco_data):
# Renvoie les biomarkers du patient dans une liste de la forme {gene:mutation}
    biomarkers= reco_data["biomarker_summary"]
    return(biomarkers)


#######
#######    Affichage de {gene:(mutation,desc)}
#######


def genes_biomarkers_concernes(traitement,df,reco_data):
    

# Retourne la liste des gènes concernés par le traitement ET présents dans les biomarqueurs du patient.
    
    biomarkers=biomarkers_genes(reco_data)
    biomarkers_names=list(biomarkers.keys())

# Filtrer pour ne garder que les gènes agissant sur la maladie présents dans les biomarqueurs du patient
    
    filtered_df = df[(df["drug_name"].str.lower() == traitement.lower()) ]

    genes = filtered_df["gene_name"].dropna().unique().tolist()
# Filtrer pour ne garder que les gènes présents dans les biomarqueurs du patient
    genes_biomarkers = [g for g in genes if g in biomarkers_names]

    return genes_biomarkers



def genes_biomarkers_concernes_global(traitement_reco,df,reco_data,path):
    genes=[]
    traitement_reco=traitements_proposes(reco_data,path)
    for reco in traitement_reco:
        for med in reco:
            genes=genes+genes_biomarkers_concernes(med,df,reco_data)
        
    return(list(set(genes)))


def gene_info(df_info,df,reco_data,path):
    """
    Retourne un dictionnaire {gene: (mutation,desc)} pour chaque gène de la liste.
    Si plusieurs interaction_type existent pour un même gène, seul le premier trouvé est pris.
    """
    genes_biomarkers=genes_biomarkers_concernes_global(traitements_proposes,df,reco_data,path)

    doublets = {}
    for gene in genes_biomarkers:
        # Récupérer la description
        desc_row = df_info[df_info["Symbol"] == gene]
        description = desc_row["description"].values[0] if not desc_row.empty else "NULL"
        doublets[gene] = (biomarkers_genes(reco_data)[gene], description)
        
    return doublets




#######
#######    Affichage de {med:(gene,interaction)}
#######



def biomarkers_traitement(traitements_reco,df,reco_data):
    """
    Retourne une liste de dictionnaires {medicament: [(gene, interaction_type, interaction_source_db_name, interaction_source_db_version), ...]} pour chaque traitement.
    """
    reco = []
    for recommendation in traitements_reco:
        dico_reco={}
        for medicament in recommendation:
            genes = genes_biomarkers_concernes(medicament,df,reco_data)
            gene_interactions = []
            for gene in genes:
                # Harmoniser la casse pour la comparaison
                mask = (
                    (df["drug_name"].str.lower().str.strip() == medicament.lower().strip()) &
                    (df["gene_name"].str.upper().str.strip() == gene.upper().strip())
                )
                
                
                sub_df = df[mask]

                if not sub_df.empty:
                    for _, row in sub_df.iterrows():
                        interaction_type = row["interaction_type"] if pd.notnull(row["interaction_type"]) else "NULL"
                        source = row["interaction_source_db_name"] if pd.notnull(row["interaction_source_db_name"]) else "NULL"
                        date = row["interaction_source_db_version"] if pd.notnull(row["interaction_source_db_version"]) else "NULL"
                        gene_interactions.append((gene, interaction_type, source, date))

                else:
                    gene_interactions.append((gene, "NA", "NA", "NA"))
                dico_reco[medicament] = gene_interactions
        reco.append(dico_reco)
    return reco

#######
#######    Affichage final
#######


def gene_interaction(path_file):
    """
    Outputs:
    {med:(gene,interaction,db_name,db_date)}

    {gene:(mutation,desc)}
    """
    # Ouvrir le fichier des reco
    with open(path_file, "r") as f:
        reco_data = json.load(f)

    # Fichiers d'interaction
    file_path_interactions = BASE_DIR + '/interactions.tsv'
    file_path_gene_info = BASE_DIR + '/gene_info.csv'

    df = pd.read_csv(file_path_interactions, sep='\t')
    df_info = pd.read_csv(file_path_gene_info)

    return (biomarkers_traitement(traitements_proposes(reco_data, path_file), df, reco_data),
            gene_info(df_info, df, reco_data, path_file))