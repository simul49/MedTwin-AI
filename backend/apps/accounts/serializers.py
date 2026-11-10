from apps.core.serialize import iso, num


def serialize_user(user, *, detailed: bool = False) -> dict:
    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone or "",
        "avatarColor": user.avatar_color,
        "initials": user.initials,
        "language": user.language,
        "isActive": bool(user.is_active),
        "isVerified": bool(user.is_verified),
        "createdAt": iso(user.created_at),
        "lastLoginAt": iso(user.last_login),
    }
    if not detailed:
        return payload

    profile = getattr(user, "patient_profile", None)
    if profile is not None:
        payload["patientProfile"] = {
            "dateOfBirth": iso(profile.date_of_birth),
            "age": profile.age,
            "gender": profile.gender,
            "bloodType": profile.blood_type or "",
            "heightCm": num(profile.height_cm),
            "weightKg": num(profile.weight_kg),
            "city": profile.city or "",
            "emergencyContact": profile.emergency_contact or "",
            "summary": profile.summary or "",
        }

    doctor_profile = getattr(user, "doctor_profile", None)
    if doctor_profile is not None:
        payload["doctorProfile"] = {
            "specialization": doctor_profile.specialization or "",
            "licenseNumber": doctor_profile.license_number or "",
            "hospital": doctor_profile.hospital or "",
            "department": doctor_profile.department or "",
            "bio": doctor_profile.bio or "",
            "verificationStatus": doctor_profile.verification_status,
        }

    payload["grantedRoles"] = [ur.role.code for ur in user.granted_roles.select_related("role")]
    return payload


def serialize_doctor(doctor) -> dict:
    profile = getattr(doctor, "doctor_profile", None)
    return {
        "id": doctor.id,
        "name": doctor.name,
        "email": doctor.email,
        "initials": doctor.initials,
        "avatarColor": doctor.avatar_color,
        "specialization": (profile.specialization if profile else "") or "",
        "hospital": (profile.hospital if profile else "") or "",
        "department": (profile.department if profile else "") or "",
        "verificationStatus": (profile.verification_status if profile else "PENDING"),
    }
