from apps.accounts.serializers import serialize_doctor
from apps.core.serialize import iso


def serialize_grant(grant) -> dict:
    return {
        "id": grant.id,
        "patientId": grant.patient_id,
        "doctorId": grant.doctor_id,
        "doctor": serialize_doctor(grant.doctor) if grant.doctor_id else None,
        "patient": (
            {
                "id": grant.patient.id,
                "name": grant.patient.name,
                "email": grant.patient.email,
                "initials": grant.patient.initials,
                "avatarColor": grant.patient.avatar_color,
            }
            if grant.patient_id
            else None
        ),
        "scope": grant.scope or [],
        "purpose": grant.purpose or "",
        "status": grant.status,
        "isEffective": grant.is_effective(),
        "grantedAt": iso(grant.granted_at),
        "expiresAt": iso(grant.expires_at),
        "revokedAt": iso(grant.revoked_at),
        "createdAt": iso(grant.created_at),
    }
