from django.apps import AppConfig


class ConsentConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.consent"
    label = "consent"
    verbose_name = "Consent and access grants"
