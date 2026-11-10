"""AI knowledge base, interaction logs and recommendations (PRD §12–§17)."""
from django.db import models
from django.utils import timezone


class KnowledgeSource(models.Model):
    """Registered, reviewed source used for retrieval (PRD §14.2).

    Patient documents are never part of this corpus: private uploads stay
    isolated from the general knowledge base.
    """

    id = models.CharField(primary_key=True, max_length=36)
    title = models.CharField(max_length=255)
    publisher = models.CharField(max_length=160, null=True, blank=True)
    version = models.CharField(max_length=60, null=True, blank=True)
    source_url = models.CharField(max_length=500, null=True, blank=True)
    category = models.CharField(max_length=60, null=True, blank=True)
    license_status = models.CharField(max_length=12, default="UNKNOWN")
    review_status = models.CharField(max_length=10, default="PENDING")
    ingested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "knowledge_sources"
        ordering = ["title"]


class KnowledgeChunk(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    source = models.ForeignKey(
        KnowledgeSource, on_delete=models.CASCADE, db_column="source_id", related_name="chunks"
    )
    chunk_index = models.IntegerField(default=0)
    title = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField()
    tokens = models.IntegerField(default=0)
    access_classification = models.CharField(max_length=12, default="PUBLIC")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "knowledge_chunks"
        ordering = ["chunk_index"]


class AiInteraction(models.Model):
    """One assistant turn, with intent, sources and the safety evaluation.

    Prompts and answers are stored only for the account owner; sensitive
    content is minimised in logs (PRD §20.2).
    """

    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        db_column="user_id",
        null=True,
        blank=True,
        related_name="ai_interactions",
    )
    conversation_id = models.CharField(max_length=36, null=True, blank=True)
    request_type = models.CharField(max_length=40, default="CHAT")
    prompt = models.TextField()
    answer = models.TextField(null=True, blank=True)
    intent = models.CharField(max_length=60, null=True, blank=True)
    risk_category = models.CharField(max_length=15, default="NORMAL")
    model_name = models.CharField(max_length=80, null=True, blank=True)
    model_version = models.CharField(max_length=40, null=True, blank=True)
    sources = models.JSONField(null=True, blank=True)
    safety = models.JSONField(null=True, blank=True)
    trust_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    trace_id = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "ai_interactions"
        ordering = ["-created_at"]


class Recommendation(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="user_id", related_name="recommendations"
    )
    type = models.CharField(max_length=20, default="EDUCATION")
    title = models.CharField(max_length=200)
    body = models.TextField(null=True, blank=True)
    basis = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, default="ACTIVE")
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "recommendations"
        ordering = ["-created_at"]
