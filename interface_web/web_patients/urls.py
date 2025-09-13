from django.urls import path
from . import views

urlpatterns = [
    path('/formulaire', views.formulaire_patient, name="formulaire_patient"),
    path('', views.home, name='home'),
    path('resultats/<str:patient_id>/', views.resultats_patient, name='resultats_patient'),
    path('/patient_id_input', views.patient_id_input, name="patient_id_input"),
    path('upload_json/', views.upload_json, name='upload_json'),
]