from django.urls import path

from apps.consent import views

urlpatterns = [
    path("consent/grants/", views.ConsentGrantListAPI.as_view(), name="api_consent_list"),
    path("consent/requests/", views.ConsentRequestAPI.as_view(), name="api_consent_request"),
    path("consent/grants/new/", views.ConsentGrantAPI.as_view(), name="api_consent_grant_new"),
    path("consent/grants/<str:grant_id>/decision/", views.ConsentDecisionAPI.as_view(), name="api_consent_decision"),
    path("consent/grants/<str:grant_id>/revoke/", views.ConsentRevokeAPI.as_view(), name="api_consent_revoke"),
]
