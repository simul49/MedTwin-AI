from django.urls import path

from apps.twin import views

urlpatterns = [
    # Patient — Digital Twin
    path("patient/digital-twin/", views.DigitalTwinAPI.as_view(), name="api_digital_twin"),
    path("patient/records/", views.RecordListAPI.as_view(), name="api_records"),
    path("patient/records/<str:record_id>/", views.RecordDetailAPI.as_view(), name="api_record_detail"),
    path("patient/timeline/", views.TimelineAPI.as_view(), name="api_timeline"),
    path("patient/observations/", views.ObservationListAPI.as_view(), name="api_observations"),
    path("patient/allergies/", views.AllergyListAPI.as_view(), name="api_allergies"),
    path("patient/allergies/<str:allergy_id>/", views.AllergyDetailAPI.as_view(), name="api_allergy_detail"),
    path("patient/medications/", views.MedicationListAPI.as_view(), name="api_medications"),
    path("patient/medications/<str:medication_id>/", views.MedicationDetailAPI.as_view(), name="api_medication_detail"),
    path("patient/documents/", views.DocumentListAPI.as_view(), name="api_documents"),
    path("patient/documents/<str:document_id>/", views.DocumentDetailAPI.as_view(), name="api_document_detail"),
    path("patient/documents/<str:document_id>/file/", views.DocumentFileAPI.as_view(), name="api_document_file"),
    path(
        "patient/documents/<str:document_id>/extractions/<str:extraction_id>/review/",
        views.ExtractionReviewAPI.as_view(),
        name="api_extraction_review",
    ),
    path("patient/export/", views.PatientExportAPI.as_view(), name="api_patient_export"),
    path("patient/data/", views.PatientDeleteDataAPI.as_view(), name="api_patient_delete"),

    # Doctor — authorised patients only
    path("doctor/authorized-patients/", views.AuthorizedPatientsAPI.as_view(), name="api_authorized_patients"),
    path("doctor/patients/<str:patient_id>/summary/", views.DoctorPatientSummaryAPI.as_view(), name="api_doctor_summary"),
    path("doctor/patients/<str:patient_id>/records/", views.DoctorPatientRecordsAPI.as_view(), name="api_doctor_records"),
    path("doctor/patients/<str:patient_id>/documents/", views.DoctorPatientDocumentsAPI.as_view(), name="api_doctor_documents"),
    path("doctor/patients/<str:patient_id>/timeline/", views.DoctorPatientTimelineAPI.as_view(), name="api_doctor_timeline"),
]
