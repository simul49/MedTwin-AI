from django.apps import AppConfig


class TwinConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.twin"
    label = "twin"
    verbose_name = "Digital Twin"
