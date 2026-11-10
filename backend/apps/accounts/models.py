"""Identity, roles and profiles.

Every model mirrors ``db/schema.sql`` exactly and is therefore ``managed =
False``: Django never issues DDL for these tables.
"""
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.db import models
from django.utils import timezone

ROLE_PATIENT = "PATIENT"
ROLE_DOCTOR = "DOCTOR"
ROLE_ADMIN = "ADMIN"
ROLE_CHOICES = [
    (ROLE_PATIENT, "Patient"),
    (ROLE_DOCTOR, "Doctor"),
    (ROLE_ADMIN, "Administrator"),
]

GENDER_CHOICES = [
    ("FEMALE", "Female"),
    ("MALE", "Male"),
    ("NON_BINARY", "Non-binary"),
    ("UNDISCLOSED", "Undisclosed"),
]


class User(AbstractBaseUser):
    """Account identity.

    Extends ``AbstractBaseUser`` so Django's PBKDF2 hasher, session auth and
    ``check_password`` are reused instead of being reimplemented (PRD §8.1:
    never store plaintext passwords).
    """

    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=190, unique=True)
    password = models.CharField("password", max_length=255, db_column="password_hash")
    objects = UserManager()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_PATIENT)
    phone = models.CharField(max_length=40, null=True, blank=True)
    avatar_color = models.CharField(max_length=20, default="#2563eb")
    language = models.CharField(max_length=2, default="en")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True, db_column="last_login_at")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        managed = False
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} <{self.email}>"

    @property
    def is_staff(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def initials(self) -> str:
        parts = [p for p in (self.name or "").split() if p]
        if not parts:
            return (self.email or "?")[:2].upper()
        return "".join(p[0] for p in parts[:2]).upper()


class Role(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "roles"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class UserRole(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="granted_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column="role_id")
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_column="granted_by",
        null=True,
        blank=True,
        related_name="+",
    )
    granted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "user_roles"


class PasswordResetToken(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="reset_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "password_reset_tokens"

    @property
    def is_usable(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()


class PatientProfile(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column="user_id", related_name="patient_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, default="UNDISCLOSED")
    blood_type = models.CharField(max_length=8, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    city = models.CharField(max_length=80, null=True, blank=True)
    emergency_contact = models.CharField(max_length=120, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "patient_profiles"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class DoctorProfile(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, db_column="user_id", related_name="doctor_profile"
    )
    specialization = models.CharField(max_length=120, null=True, blank=True)
    license_number = models.CharField(max_length=60, null=True, blank=True)
    hospital = models.CharField(max_length=160, null=True, blank=True)
    department = models.CharField(max_length=120, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    verification_status = models.CharField(max_length=10, default="PENDING")
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "doctor_profiles"
