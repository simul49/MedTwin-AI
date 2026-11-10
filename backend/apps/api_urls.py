from django.urls import include, path

urlpatterns = [
    path("v1/", include("apps.accounts.urls")),
    path("v1/", include("apps.twin.urls")),
    path("v1/", include("apps.consent.urls")),
    path("v1/", include("apps.ai.urls")),
    path("v1/", include("apps.connect.urls")),
    path("v1/", include("apps.ops.urls")),
]
