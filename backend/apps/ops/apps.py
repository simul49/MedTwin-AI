from django.apps import AppConfig


class OpsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.ops"
    label = "ops"
    verbose_name = "Audit, governance and administration"
