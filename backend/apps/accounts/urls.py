from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("auth/csrf/", views.CsrfAPI.as_view(), name="api_csrf"),
    path("auth/register/", views.RegisterAPI.as_view(), name="api_register"),
    path("auth/login/", views.LoginAPI.as_view(), name="api_login"),
    path("auth/logout/", views.LogoutAPI.as_view(), name="api_logout"),
    path("auth/password/change/", views.PasswordChangeAPI.as_view(), name="api_password_change"),
    path("auth/password/forgot/", views.PasswordForgotAPI.as_view(), name="api_password_forgot"),
    path("auth/password/reset/", views.PasswordResetAPI.as_view(), name="api_password_reset"),
    path("me/", views.MeAPI.as_view(), name="api_me"),
    path("doctors/", views.DoctorDirectoryAPI.as_view(), name="api_doctors"),
]
