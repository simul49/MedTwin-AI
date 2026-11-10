from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.ai"
    label = "ai"
    verbose_name = "AI assistant, RAG and safety"
