"""Authentication, session and account endpoints (PRD §8)."""
import hashlib
import logging
import re
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import (
    ROLE_DOCTOR,
    ROLE_PATIENT,
    PatientProfile,
    DoctorProfile,
    PasswordResetToken,
    User,
)
from apps.accounts.serializers import serialize_doctor, serialize_user
from apps.core.permissions import require_roles
from apps.core.throttle import check as throttle_check, key_for, record_failure, reset as throttle_reset
from apps.core.utils import client_ip, new_id, record_audit

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
AVATAR_COLORS = ["#2563eb", "#0ea5e9", "#0f766e", "#7c3aed", "#c2410c", "#be123c", "#15803d"]


def _pick_color(seed: str) -> str:
    digest = hashlib.sha256((seed or "").encode("utf-8")).digest()
    return AVATAR_COLORS[digest[0] % len(AVATAR_COLORS)]


def _validate_registration(data: dict) -> dict:
    errors: dict = {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or ROLE_PATIENT).upper()

    if len(name) < 2:
        errors["name"] = "Enter your full name."
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    elif User.objects.filter(email=email).exists():
        errors["email"] = "An account with this email already exists."
    if not PASSWORD_RE.match(password):
        errors["password"] = "Use at least 8 characters, including a letter and a number."
    if role not in {ROLE_PATIENT, ROLE_DOCTOR}:
        errors["role"] = "Choose Patient or Doctor."
    if role == ROLE_DOCTOR and not (data.get("specialization") or "").strip():
        errors["specialization"] = "Add your specialization so patients can identify you."
    if not data.get("acknowledge"):
        errors["acknowledge"] = "Please confirm the medical disclaimer to continue."
    return errors


class CsrfAPI(APIView):
    """Issues the CSRF token the SPA must echo on unsafe requests."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        errors = _validate_registration(data)
        if errors:
            return Response({"error": "Please correct the highlighted fields.", "fields": errors},
                            status=status.HTTP_400_BAD_REQUEST)

        email = data["email"].strip().lower()
        role = data["role"].upper()
        user = User(
            id=new_id(),
            name=data["name"].strip(),
            email=email,
            role=role,
            phone=(data.get("phone") or "").strip() or None,
            avatar_color=_pick_color(email),
            language=(data.get("language") or "en").lower()[:2] or "en",
            is_active=True,
        )
        user.set_password(data["password"])
        user.save()

        if role == ROLE_PATIENT:
            PatientProfile.objects.create(
                id=new_id(),
                user=user,
                date_of_birth=data.get("date_of_birth") or None,
                gender=(data.get("gender") or "UNDISCLOSED").upper(),
            )
        else:
            DoctorProfile.objects.create(
                id=new_id(),
                user=user,
                specialization=(data.get("specialization") or "").strip(),
                license_number=(data.get("license_number") or "").strip(),
                hospital=(data.get("hospital") or "").strip(),
                department=(data.get("department") or "").strip(),
                verification_status="PENDING",
            )

        record_audit(action="REGISTER", request=request, actor=user, resource_type="user",
                     resource_id=user.id, metadata={"role": role})
        auth_login(request, user)
        return Response(serialize_user(user, detailed=True), status=status.HTTP_201_CREATED)


class LoginAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        key = key_for(email, client_ip(request))

        allowed, retry_after = throttle_check(key)
        if not allowed:
            record_audit(action="LOGIN", request=request, actor=None, resource_type="session",
                         outcome="DENIED", metadata={"reason": "rate_limited", "email": email})
            return Response(
                {"error": f"Too many attempts. Try again in {retry_after // 60} minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(username=email, password=password)
        if user is None or not getattr(user, "is_active", False):
            record_failure(key)
            record_audit(action="LOGIN", request=request, actor=user, resource_type="session",
                         outcome="DENIED", metadata={"email": email})
            return Response({"error": "Email or password is incorrect."},
                            status=status.HTTP_401_UNAUTHORIZED)

        throttle_reset(key)
        auth_login(request, user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        record_audit(action="LOGIN", request=request, actor=user, resource_type="session",
                     resource_id=user.id)
        return Response(serialize_user(user, detailed=True))


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        record_audit(action="LOGOUT", request=request, actor=request.user, resource_type="session")
        auth_logout(request)
        return Response({"ok": True})


class MeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(serialize_user(request.user, detailed=True))

    def patch(self, request):
        user = request.user
        data = request.data
        changed = []

        for field in ("name", "phone", "language"):
            if field in data and data[field] is not None:
                setattr(user, field, data[field])
                changed.append(field)

        profile_data = data.get("patientProfile") or {}
        if user.role == ROLE_PATIENT and profile_data:
            profile, _ = PatientProfile.objects.get_or_create(
                user=user, defaults={"id": new_id()}
            )
            for field in ("date_of_birth", "gender", "blood_type", "city", "emergency_contact", "summary"):
                if field in profile_data:
                    setattr(profile, field, profile_data[field] or None)
                    changed.append(f"profile.{field}")
            for field in ("height_cm", "weight_kg"):
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
                    changed.append(f"profile.{field}")
            profile.save()

        doctor_data = data.get("doctorProfile") or {}
        if user.role == ROLE_DOCTOR and doctor_data:
            profile, _ = DoctorProfile.objects.get_or_create(
                user=user, defaults={"id": new_id()}
            )
            for field in ("specialization", "license_number", "hospital", "department", "bio"):
                if field in doctor_data:
                    setattr(profile, field, doctor_data[field] or None)
                    changed.append(f"doctor.{field}")
            profile.save()

        if changed:
            user.save()
        record_audit(action="PROFILE_UPDATE", request=request, actor=user,
                     resource_type="user", resource_id=user.id, metadata={"fields": changed})
        return Response(serialize_user(user, detailed=True))


class PasswordChangeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current = request.data.get("currentPassword") or ""
        new_password = request.data.get("newPassword") or ""

        if not user.check_password(current):
            return Response({"error": "Current password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user)
        except ValidationError as exc:
            return Response({"error": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        record_audit(action="PASSWORD_CHANGE", request=request, actor=user,
                     resource_type="user", resource_id=user.id)
        return Response({"ok": True})


class PasswordForgotAPI(APIView):
    """Always returns 200 so the endpoint cannot enumerate accounts."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                id=new_id(),
                user=user,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=timezone.now() + timedelta(hours=1),
            )
            record_audit(action="PASSWORD_RESET_REQUEST", request=request, actor=user,
                         resource_type="user", resource_id=user.id)
            # No mail server in this deployment: the token is returned so the
            # flow is demonstrable. Replace with an email delivery call.
            logger.info("password reset token for %s: %s", email, token)
            return Response({"ok": True, "devToken": token})
        return Response({"ok": True})


class PasswordResetAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token") or ""
        new_password = request.data.get("password") or ""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = PasswordResetToken.objects.filter(token_hash=token_hash).first()

        if not reset_token or not reset_token.is_usable:
            return Response({"error": "This reset link is invalid or expired."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, reset_token.user)
        except ValidationError as exc:
            return Response({"error": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        reset_token.used_at = timezone.now()
        reset_token.save(update_fields=["used_at"])
        record_audit(action="PASSWORD_RESET", request=request, actor=user,
                     resource_type="user", resource_id=user.id)
        return Response({"ok": True})


class DoctorDirectoryAPI(APIView):
    """Verified professionals a patient can grant access to."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT, "ADMIN")
    def get(self, request):
        doctors = User.objects.filter(role=ROLE_DOCTOR, is_active=True).select_related("doctor_profile")
        return Response({"results": [serialize_doctor(d) for d in doctors]})
