from django.apps import AppConfig


class ConnectConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.connect"
    label = "connect"
    verbose_name = "Messages, appointments and notifications"
