
#Importations nécessaires
from django.shortcuts import render, redirect, reverse
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
import json
import subprocess
import os

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from affichage_web.text_response import json_message



#vue correspondant à la page résultat
def resultats_patient(request, patient_id):
    guidelines_file = "../guidelines_metastatic.json"
    patient_file = os.path.join(settings.BASE_DIR, "../patients", f"patient_{patient_id[4:]}.json")

    if not os.path.exists(patient_file):
        # Renvoie une page d’erreur personnalisée
        return render(request, "patients/identifiant_non_utilise.html", {"patient_id": patient_id})
    
    else:
        # Exécuter le script complet
        cmd = ["python", "../treatment_recommender.py", guidelines_file, patient_file]
        subprocess.run(cmd, check=True)
        output_file = f"recommendations_{patient_id}.json"
        json_message(output_file, patient_id)
        affichage = f"affichage_{patient_id[4:]}.json"
        with open(affichage, 'r', encoding='utf-8') as g:
            data_affichage = json.load(g)
        affichage_bis = list(data_affichage.values())


        return render(request, "patients/resultats.html", {
            "nom": patient_id,
            "recommandations" : affichage_bis
        })


#vue correspondant à la page d'accueil
def home(request):
    return render(request, "patients/home.html")


#vue correspondant à la page formulaire
def formulaire_patient(request):
    if request.method == "POST":
        # Récupération des données du formulaire
        patient_id = request.POST.get("patient_id")
        age = int(request.POST.get("age"))
        gender = request.POST.get("gender")
        performance_status = int(request.POST.get("performance_status") or 0)
        cancer_type = request.POST.get("cancer_type")
        stage = request.POST.get("stage")  # renamed to disease_stage
        histology = request.POST.get("histology")
        grade = int(request.POST.get("grade") or 0)
        biomarkers = {
            "ER": request.POST.get("ER"),
            "PgR": request.POST.get("PgR"),
            "HER2": request.POST.get("HER2"),
            "PIK3CA": request.POST.get("PIK3CA"),
            "BRCA1": request.POST.get("BRCA1"),
            "BRCA2": request.POST.get("BRCA2"),
            "PALB2": request.POST.get("PALB2"),
            "ESR1": request.POST.get("ESR1"),
            "PD_L1": request.POST.get("PD_L1"),
            "MSI": request.POST.get("MSI"),
            "TMB": float(request.POST.get("TMB") or 0),
            "NTRK": request.POST.get("NTRK"),
        }
        treatment_history = [
            {
                "line": 1,
                "regimen": request.POST.get("regime"),
                "response": request.POST.get("response"),
                "duration_months": int(request.POST.get("month_duration") or 0),
                "progression": True if request.POST.get("progression") == "positive" else False
            }
        ]
        lab_values = {
            "HbA1c": float(request.POST.get("HbA1c") or 0),
            "fasting_glucose": int(request.POST.get("fasting_glucose") or 0),
            "creatinine": float(request.POST.get("creatinine") or 0),
            "bilirubin": float(request.POST.get("bilirubin") or 0)
        }
        metastatic_sites = [site.strip() for site in request.POST.get("metastatic_sites", "").split(",") if site.strip()]
        contraindications = [request.POST.get("contraindications")] if request.POST.get("contraindications") else []

        # Créer la structure JSON
        patient_data = {
            "patient_id": patient_id,
            "demographics": {
                "age": age,
                "gender": gender,
                "performance_status": performance_status
            },
            "diagnosis": {
                "cancer_type": cancer_type,
                "stage": stage,
                "histology": histology,
                "grade": grade
            },
            "biomarkers": biomarkers,
            "treatment_history": treatment_history,
            "lab_values": lab_values,
            "metastatic_sites": metastatic_sites,
            "contraindications": contraindications
        }

        # Sauvegarder le JSON dans un fichier
        output_filename = f"../patients/patient_{patient_id[4:]}.json"
        with open(output_filename, "w") as f:
            json.dump(patient_data, f, indent=2)

        return redirect("resultats_patient", patient_id=patient_id)

    # GET = afficher le formulaire
    return render(request, "patients/formulaire.html")


#vue correspondant à la page identifiant du patient
def patient_id_input(request):
    if request.method == "POST":
        # Récupère l'ID entré par l'utilisateur
        patient_id = request.POST.get("patient_id")
        # Redirige vers la page de résultats du patient
        return redirect(reverse('resultats_patient', kwargs={'patient_id': patient_id}))
    
    return render(request, "patients/patient_id_input.html")


#vue pour charger un fichier json
def upload_json(request):
    if request.method == "POST":
        json_file = request.FILES.get("json_file")
        if json_file:
            try:
                # Lire le contenu du fichier uploadé (en bytes), puis décoder
                file_data = json_file.read().decode('utf-8')
                json_data = json.loads(file_data)

                # Vérifie qu'il y a un patient_id
                patient_id = json_data.get("patient_id")
                if not patient_id:
                    return render(request, "patients/upload_json.html", {
                        "error": "Le fichier JSON ne contient pas de champ 'patient_id'."
                    })

                # Créer le dossier patients/ si nécessaire
                patients_dir = os.path.join(settings.BASE_DIR, "..", "patients")
                patients_dir = os.path.abspath(patients_dir)  # Normaliser le chemin absolu
                os.makedirs(patients_dir, exist_ok=True)

                # Préparer le nom du fichier
                id_numerique = patient_id[4:]  # ex : MBC_010 → 010
                file_path = os.path.join(patients_dir, f"patient_{id_numerique}.json")

                # Sauvegarder le fichier JSON
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                print(f"JSON sauvegardé dans: {file_path}")

                # Rediriger vers la page résultats
                return redirect("resultats_patient", patient_id=patient_id)

            except json.JSONDecodeError:
                return render(request, "patients/upload_json.html", {
                    "error": "Le fichier n'est pas un JSON valide."
                })

        return render(request, "patients/upload_json.html", {
            "error": "Aucun fichier sélectionné."
        })

    return render(request, "patients/upload_json.html")

