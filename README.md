
# 🏥 CARJAC: Recommandation de traitement fondée sur des données probantes pour le cancer du sein métastatique

## 📄 Overview

Ce projet vise à créer un outil léger d’aide à la décision pour les oncologues afin qu’ils puissent faire des choix de traitement fondés sur des données probantes pour le cancer du sein métastatique pendant les examens cliniques. 🏥 L’outil traite les données des patients et les lignes directrices de l’ESMO pour fournir des recommandations de traitement adaptées, étayées par des preuves scientifiques. 🔬

## 📂 Structure du projet

```diff
.
├── carjac
│   ├── drug_gene_interactions
│   ├── interface_web
│   ├── patients
│   ├── pertinence
│   ├── pubmed_articles
│   ├── static
│   ├── .gitignore
│   ├── recommendations
│   ├── guidelines_metastatic.json
│   ├── treatment_recommender.py
│   ├── README.md
│   │
│   ├── download_nltk_data.py
│   └── requirements.txt
```

## 🛠️ Tutoriel simple de configuration accessible à tous !

### 📋 Prérequis

- Python 3.8 ou supérieur (https://www.python.org/downloads/) 🐍
- pip (programme d’installation du paquet Python)

### 🔧 Installation

0. Installer bash et lancer un terminal (https://git-scm.com/downloads/win)

1. Cloner le dépôt:

   ```bash
   git clone https://gitlab-student.centralesupelec.fr/jeanne.lorton/carjac.git
   ```

2. Accédez au répertoire du projet :

   ```bash
   cd carjac/
   ```

3. Installer les paquets requis:

   ```bash
   pip install -r requirements.txt
   ```
4. Installer le vocabulaire avec la commande suivante et suivre les insructions de la fenêtre (pas de panique c'est intuitif !):

   ```bash
   py download_nltk_data.py
   ```

## 🚀 Utilisation

#### Préparez vos données d’entrée :
   - Assurez-vous d’avoir un fichier JSON patient prêt ou au moins les informations du JSON. Vous trouverez ci-dessous un modèle de JSON valide:
     ```json
     {
       "patient_id": "MBC_001",
       "demographics": {
         "age": 58,
         "gender": "female",
         "performance_status": 1
       },
       "diagnosis": {
         "cancer_type": "breast",
         "stage": "metastatic",
         "histology": "invasive_ductal_carcinoma",
         "grade": 2
       },
       "biomarkers": {
         "ER": "positive",
         "PgR": "positive",
         "HER2": "negative",
         "PIK3CA": "mutant",
         "BRCA1": "wild_type",
         "BRCA2": "wild_type",
         "PALB2": "wild_type",
         "ESR1": "wild_type",
         "PD_L1": "negative",
         "MSI": "stable",
         "TMB": 3.2,
         "NTRK": "negative"
       },
       "treatment_history": [
         {
           "line": 1,
           "regimen": "CDK4/6 inhibitor + aromatase inhibitor",
           "response": "partial_response",
           "duration_months": 14,
           "progression": true
         }
       ],
       "lab_values": {
         "HbA1c": 6.8,
         "fasting_glucose": 105,
         "creatinine": 0.9,
         "bilirubin": 1.2
       },
       "metastatic_sites": ["bone", "liver"],
       "contraindications": []
     }
     ```
   - Lancer le site web à l'aide de la commande suivante sur le terminal
     ```bash
     cd interface_web
     py manage.py runserver
     ```

2. Se rendre sur http://127.0.0.1:8000/ et suivre les directives : **🌟NOUVEAU**: un formulaire est maintenant disponible 

## 📊 Description des données

- `guidelines metastatic.json` : arbre de décision de l'ESMO sur le cancer du sein métastatique.
- `pubmed_articles/` : Répertoire contenant des PDF en texte intégral de PubMed.
- `drug_gene_interactions/` : Tables d’interaction médicament-gène et de description des gènes ainsi que le fichier python de gestion associé
- `gene_info.csv` : Table d'informations sur les gènes.
- `affichage.json` : Fichier temporaire d'interaction entre tous les fichiers python qui génère le JSON du traitement.
- `pertinence/` : Répertoire contenant les méthodes de recherche d'information.
- `patients/` : Dossier contenant un échantillon de JSON de patients test.
- `interface_web/` : Gestion de l'application web
- `recommendations` : Dossier contenant un échantillon des JSON de traitements test
- `indexation` : Répertoire contenant les fichiers de gestion de l'index inversé

## 🐍 Scripts Python

- `treatment_recommender.py`: Ce fichier permet de générer les traitements recommandés pour un patient précis avec des informations supplémentaires comme les biomarqueurs pertinents, l'efficacité du traitement (Strong, Moderate, Weak), le niveau de justification (1 à 3) ou des mots clés.
- `indexation.py`: Ce fichier génère un index inversé (fichier index.json) avec pour chaque terme du vocabulaire créé à partir du corpus, tf (fréquence d'un terme dans un document) et idf (mesure de l'importance d'un terme dans tout le corpus) pour chaque document dans un dictionnaire de la forme
  ```python
  final_index = {term: {doc_name: (tf, idf)}}
  ```
- `download_nltk_data.py`: permet de gérer l'installation da la bilbiothèque de gestion des mots pour la recherche d'information
- `genes_treatment.py`: Ce fichier se charge d'identifier et de décrire (type de mutation et molécule) les gènes biomarqueurs sur lesquels agissent un traitement.
- `request_tokenize.py`:gestion de la tokenization de la requête
- etc.
## 🤝 Contribution

1. Bifurquer le dépôt.
2. Créer une nouvelle branche pour votre fonctionnalité ou correction de bogue.
   ```bash
   git checkout -b nom_de_votre_branche
   ```
3. Valider vos modifications avec des messages descriptifs.
   ```bash
   git add *
   git commit -m "message lié à votre modification"
   git push
   ```


## 📧 Contact

Pour toute question ou suggestion, contacter les modérateurs du projet.

### Remarques sur le contexte du projet:
Notre projet a été réalisé en 1 semaine lors d'un travail co-encadré par Centrale Supélec, le MICS et l'IHU PRISM 🏫

#### Chronologie du développement du projet

| Jour | Tâches |
|------|--------|
| 🌞 Jour 1 | **Adam et Romain** : Chargement des PDF sous forme de dictionnaire, tokenisation des textes, lemmatisation, création de l'index inversé. Test d'un vocabulaire spécifique à la médecine (PubMed MeSH). |
| | **Clara** : Étude des fichiers TSV et CSV (tableaux d'interactions) et utilisation de ces tableaux pour renvoyer les gènes en interaction avec les traitements proposés pour chaque patient. |
| | **Jeanne et Adèle** : Création du classement des documents pertinents en fonction d'une requête, avec le modèle vectoriel et le modèle Okapi BM25. |
| 🌞 Jour 2 | **Adèle** : Adaptation des modèles booléen, vectoriel et probabiliste à l'index inversé et tests réalisés. Début d'implémentation d'un LLM pour retourner les documents les plus pertinents. |
| | **Romain et Adam** : Fin du vocabulaire (tokens) et début de création du message renvoyé par le programme. |
| | **Jeanne** : Présentation des documents renvoyés (meilleur classement) : renvoi de l'abstract, description, etc. |
| | **Clara** : Création d'une interface web avec une page formulaire pour récupérer les informations sur le patient et les convertir en JSON, et une page résultats pour afficher les traitements recommandés et les justifications scientifiques. |
| 🌞 Jour 3 | **Jeanne** : Finalisation de la présentation des documents renvoyés, incluant l'abstract, la date et le nom des chercheurs. |
| | **Romain** : Mise en commun de fonctions de tous les membres pour afficher le message de traitement récapitulatif dans le terminal |
| | **Clara** : Poursuite du travail sur l'interface web |
| | **Adèle** : Travail sur le modèle vectoriel principalement. Début d'implémentation de Word2Vec|
| | **Adam** : |
| 🌞 Jour 4 | **Jeanne** : Derniers ajustements sur les documents renovyés, travail sur la présentation |
| | **Romain** : Intégration des codes entre eux |
| | **Clara** : Finalisation de l'interface web et intégration|
| | **Adèle** : Finalisation de Word2Vec |
| | **Adam** : Participation à l'intégration des codes et réalisation du README |

| 🔮 Améliorations futures potentielles |
|--------------------------------|
| Extension du corpus de documents |
| Implémentation de davantages de modèles de classement de pertinence |
| Prise en compte des du contexte des mots de manière plus rigide |
