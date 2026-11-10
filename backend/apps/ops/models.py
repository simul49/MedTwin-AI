"""Audit trail, model governance and system configuration (PRD §15, §19.3)."""
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    actor_id = models.CharField(max_length=36, null=True, blank=True)
    actor_email = models.CharField(max_length=190, null=True, blank=True)
    action = models.CharField(max_length=60)
    resource_type = models.CharField(max_length=60, null=True, blank=True)
    resource_id = models.CharField(max_length=36, null=True, blank=True)
    outcome = models.CharField(max_length=8, default="SUCCESS")
    ip_address = models.CharField(max_length=60, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    trace_id = models.CharField(max_length=40, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "audit_logs"
        ordering = ["-created_at"]


class ModelVersion(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=80)
    version = models.CharField(max_length=40)
    provider = models.CharField(max_length=80, null=True, blank=True)
    kind = models.CharField(max_length=10, default="LLM")
    config = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "model_versions"
        ordering = ["kind", "-created_at"]


class EvaluationRun(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        db_column="model_version_id",
        null=True,
        blank=True,
        related_name="runs",
    )
    dataset_version = models.CharField(max_length=40, null=True, blank=True)
    metrics = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, default="PENDING")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "evaluation_runs"
        ordering = ["-created_at"]


class DeepfakeAnalysis(models.Model):
    """Synthetic/manipulated-content analysis — experimental (PRD §16)."""

    id = models.CharField(primary_key=True, max_length=36)
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        db_column="owner_id",
        null=True,
        blank=True,
        related_name="deepfake_analyses",
    )
    file_name = models.CharField(max_length=255, null=True, blank=True)
    mime_type = models.CharField(max_length=120, null=True, blank=True)
    storage_path = models.CharField(max_length=400, null=True, blank=True)
    modality = models.CharField(max_length=10, default="IMAGE")
    model_version = models.CharField(max_length=40, null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    risk_level = models.CharField(max_length=8, default="UNKNOWN")
    uncertainty = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    limitations = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "deepfake_analyses"
        ordering = ["-created_at"]


class FeatureFlag(models.Model):
    """Feature status labels required by PRD §28: Planned / In Development /
    Implemented / Evaluated / Released."""

    id = models.CharField(primary_key=True, max_length=36)
    flag_key = models.CharField(max_length=60, unique=True)
    label = models.CharField(max_length=160, null=True, blank=True)
    description = models.CharField(max_length=400, null=True, blank=True)
    is_enabled = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="PLANNED")
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "feature_flags"
        ordering = ["flag_key"]
