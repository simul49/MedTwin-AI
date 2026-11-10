"""Patient-to-doctor access grants (PRD §8.3).

A grant records who gave access, to whom, for what scope, until when, and in
which status. Nothing in the platform authorises a doctor without one.
"""
from django.db import models
from django.utils import timezone

GRANT_STATUS = [
    ("PENDING", "Awaiting patient decision"),
    ("ACTIVE", "Active"),
    ("REJECTED", "Rejected by patient"),
    ("REVOKED", "Revoked by patient"),
    ("EXPIRED", "Expired"),
]

# Data categories a patient may include in a grant (PRD §9.1).
SCOPE_OPTIONS = [
    "profile",
    "conditions",
    "medications",
    "allergies",
    "lab_results",
    "documents",
    "timeline",
]


class ConsentGrant(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    patient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="patient_id", related_name="grants_given"
    )
    doctor = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="doctor_id", related_name="grants_received"
    )
    scope = models.JSONField(default=list)
    purpose = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=GRANT_STATUS, default="PENDING")
    granted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "consent_grants"
        ordering = ["-created_at"]

    def is_effective(self) -> bool:
        """A grant authorises access only while ACTIVE and not expired."""
        if self.status != "ACTIVE":
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    def allows(self, category: str) -> bool:
        scope = self.scope or []
        return "all" in scope or category in scope
