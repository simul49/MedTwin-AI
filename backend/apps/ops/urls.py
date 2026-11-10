from django.urls import path

from apps.ops import views

urlpatterns = [
    path("health/", views.HealthAPI.as_view(), name="api_health"),
    path("admin/users/", views.AdminUserListAPI.as_view(), name="api_admin_users"),
    path("admin/users/<str:user_id>/", views.AdminUserDetailAPI.as_view(), name="api_admin_user_detail"),
    path("admin/audit-logs/", views.AdminAuditLogAPI.as_view(), name="api_admin_audit"),
    path("admin/consent-grants/", views.AdminConsentAPI.as_view(), name="api_admin_consent"),
    path("admin/knowledge-sources/", views.KnowledgeSourceListAPI.as_view(), name="api_admin_sources"),
    path("admin/knowledge-sources/<str:source_id>/", views.KnowledgeSourceDetailAPI.as_view(),
         name="api_admin_source_detail"),
    path("admin/system/health/", views.SystemHealthAPI.as_view(), name="api_admin_health"),
    path("admin/feature-flags/", views.FeatureFlagListAPI.as_view(), name="api_admin_flags"),
    path("admin/feature-flags/<str:flag_id>/", views.FeatureFlagDetailAPI.as_view(),
         name="api_admin_flag_detail"),
]
