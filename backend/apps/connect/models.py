"""Messaging, appointments and notifications (PRD §18).

Messaging is only possible where a conversation relationship exists, and the
conversation is validated against an active consent grant for doctor channels.
"""
from django.db import models

# Aliased: `Appointment.timezone` is a column name and would shadow the module.
from django.utils import timezone as django_timezone


class Conversation(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    patient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="patient_id", related_name="conversations"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        db_column="doctor_id",
        null=True,
        blank=True,
        related_name="doctor_conversations",
    )
    title = models.CharField(max_length=160, null=True, blank=True)
    channel = models.CharField(max_length=20, default="PATIENT_DOCTOR")
    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        managed = False
        db_table = "conversations"
        ordering = ["-updated_at"]


class Message(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, db_column="conversation_id", related_name="messages"
    )
    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        db_column="sender_id",
        null=True,
        blank=True,
        related_name="+",
    )
    role = models.CharField(max_length=10, default="USER")
    body = models.TextField()
    attachments = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=django_timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "messages"
        ordering = ["created_at"]


class Appointment(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    patient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="patient_id", related_name="appointments"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        db_column="doctor_id",
        null=True,
        blank=True,
        related_name="doctor_appointments",
    )
    scheduled_at = models.DateTimeField()
    duration_min = models.IntegerField(default=30)
    timezone = models.CharField(max_length=60, default="UTC")
    reason = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, default="REQUESTED")
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        managed = False
        db_table = "appointments"
        ordering = ["scheduled_at"]


class Notification(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, db_column="user_id", related_name="notifications"
    )
    type = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    body = models.TextField(null=True, blank=True)
    link = models.CharField(max_length=200, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        managed = False
        db_table = "notifications"
        ordering = ["-created_at"]
