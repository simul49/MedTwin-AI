"""Messaging, appointments and notifications (PRD §18).

A patient and a doctor can only share a conversation while an effective consent
grant exists; the check happens server-side on every request.
"""
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ROLE_DOCTOR, ROLE_PATIENT, User
from apps.accounts.serializers import serialize_doctor
from apps.connect.models import Appointment, Conversation, Message, Notification
from apps.core.permissions import grant_is_live, active_grant, require_roles
from apps.core.serialize import iso
from apps.core.utils import new_id, record_audit

APPOINTMENT_STATUSES = {"REQUESTED", "CONFIRMED", "DECLINED", "COMPLETED", "CANCELLED"}


def serialize_conversation(conversation, *, viewer) -> dict:
    other = conversation.doctor if viewer.role == ROLE_PATIENT else conversation.patient
    last = conversation.messages.order_by("-created_at").first()
    return {
        "id": conversation.id,
        "title": conversation.title or (other.name if other else "Conversation"),
        "channel": conversation.channel,
        "counterpart": (
            {
                "id": other.id,
                "name": other.name,
                "initials": other.initials,
                "avatarColor": other.avatar_color,
                "specialization": getattr(getattr(other, "doctor_profile", None), "specialization", "") or "",
            }
            if other
            else None
        ),
        "lastMessage": last.body[:160] if last else "",
        "lastMessageAt": iso(last.created_at) if last else None,
        "unread": conversation.messages.filter(read_at__isnull=True).exclude(sender=viewer).count(),
        "updatedAt": iso(conversation.updated_at),
    }


def serialize_message(message) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "body": message.body,
        "senderId": message.sender_id,
        "senderName": message.sender.name if message.sender_id else "MedTwin AI",
        "createdAt": iso(message.created_at),
        "readAt": iso(message.read_at),
    }


def serialize_appointment(appointment) -> dict:
    return {
        "id": appointment.id,
        "patientId": appointment.patient_id,
        "doctorId": appointment.doctor_id,
        "patientName": appointment.patient.name if appointment.patient_id else "",
        "doctorName": appointment.doctor.name if appointment.doctor_id else "",
        "scheduledAt": iso(appointment.scheduled_at),
        "durationMin": appointment.duration_min,
        "timezone": appointment.timezone,
        "reason": appointment.reason or "",
        "status": appointment.status,
        "notes": appointment.notes or "",
        "createdAt": iso(appointment.created_at),
    }


def serialize_notification(notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "body": notification.body or "",
        "link": notification.link or "",
        "isRead": notification.is_read,
        "createdAt": iso(notification.created_at),
    }


class ConversationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == ROLE_PATIENT:
            conversations = Conversation.objects.filter(patient=user).exclude(channel="PATIENT_AI")
        elif user.role == ROLE_DOCTOR:
            conversations = Conversation.objects.filter(doctor=user).exclude(channel="PATIENT_AI")
        else:
            conversations = Conversation.objects.none()
        conversations = conversations.select_related("patient", "doctor")
        return Response(
            {"results": [serialize_conversation(c, viewer=user) for c in conversations]}
        )

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        doctor_id = request.data.get("doctorId") or ""
        try:
            doctor = User.objects.get(pk=doctor_id, role=ROLE_DOCTOR, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

        if not grant_is_live(active_grant(doctor, request.user)):
            record_audit(action="ACCESS_DENIED", request=request, actor=request.user,
                         resource_type="conversation", outcome="DENIED",
                         metadata={"reason": "no_active_grant", "doctorId": doctor.id})
            return Response(
                {"error": "Grant access to this doctor before starting a conversation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        conversation, _ = Conversation.objects.get_or_create(
            patient=request.user,
            doctor=doctor,
            channel="PATIENT_DOCTOR",
            defaults={"id": new_id(), "title": doctor.name},
        )
        return Response(serialize_conversation(conversation, viewer=request.user),
                        status=status.HTTP_201_CREATED)


class ConversationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.select_related("patient", "doctor").get(pk=conversation_id)
        except Conversation.DoesNotExist:
            raise Http404
        user = request.user
        if user.role == ROLE_PATIENT and conversation.patient_id != user.id:
            raise Http404
        if user.role == ROLE_DOCTOR and conversation.doctor_id != user.id:
            raise Http404
        return conversation

    def get(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        messages = conversation.messages.select_related("sender").all()[:300]
        conversation.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
            read_at=timezone.now()
        )
        return Response(
            {
                "id": conversation.id,
                "title": conversation.title,
                "messages": [serialize_message(m) for m in messages],
            }
        )

    def post(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        body = (request.data.get("body") or "").strip()
        if not body:
            return Response({"error": "Write a message first."}, status=status.HTTP_400_BAD_REQUEST)

        # A doctor must still hold an effective grant to reply.
        if request.user.role == ROLE_DOCTOR and not grant_is_live(
            active_grant(request.user, conversation.patient)
        ):
            return Response({"error": "Your access to this patient is no longer active."},
                            status=status.HTTP_403_FORBIDDEN)

        message = Message.objects.create(
            id=new_id(),
            conversation=conversation,
            sender=request.user,
            role="DOCTOR" if request.user.role == ROLE_DOCTOR else "USER",
            body=body[:4000],
        )
        Conversation.objects.filter(pk=conversation.id).update(updated_at=timezone.now())
        return Response(serialize_message(message), status=status.HTTP_201_CREATED)


class AppointmentListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == ROLE_PATIENT:
            appointments = Appointment.objects.filter(patient=user)
        elif user.role == ROLE_DOCTOR:
            appointments = Appointment.objects.filter(doctor=user)
        else:
            appointments = Appointment.objects.none()
        return Response({"results": [serialize_appointment(a) for a in appointments.select_related(
            "patient", "doctor")[:50]]})

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        data = request.data
        doctor_id = data.get("doctorId") or ""
        try:
            doctor = User.objects.get(pk=doctor_id, role=ROLE_DOCTOR, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)
        if not data.get("scheduledAt"):
            return Response({"error": "Choose a date and time."}, status=status.HTTP_400_BAD_REQUEST)

        appointment = Appointment.objects.create(
            id=new_id(),
            patient=request.user,
            doctor=doctor,
            scheduled_at=data["scheduledAt"],
            duration_min=int(data.get("durationMin") or 30),
            timezone=(data.get("timezone") or "UTC")[:60],
            reason=(data.get("reason") or "")[:255] or None,
            status="REQUESTED",
        )
        Notification.objects.create(
            id=new_id(),
            user=doctor,
            type="APPOINTMENT_REQUEST",
            title="New appointment request",
            body=f"{request.user.name} requested an appointment.",
            link="/doctor/appointments",
        )
        record_audit(action="APPOINTMENT_CREATE", request=request, actor=request.user,
                     resource_type="appointment", resource_id=appointment.id)
        return Response(serialize_appointment(appointment), status=status.HTTP_201_CREATED)


class AppointmentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(pk=appointment_id)
        except Appointment.DoesNotExist:
            raise Http404
        user = request.user
        if user.role == ROLE_PATIENT and appointment.patient_id != user.id:
            raise Http404
        if user.role == ROLE_DOCTOR and appointment.doctor_id != user.id:
            raise Http404
        return appointment

    def patch(self, request, appointment_id):
        appointment = self._get(request, appointment_id)
        next_status = (request.data.get("status") or "").upper()
        if next_status not in APPOINTMENT_STATUSES:
            return Response({"error": "Unknown appointment status."},
                            status=status.HTTP_400_BAD_REQUEST)
        appointment.status = next_status
        if "notes" in request.data:
            appointment.notes = (request.data["notes"] or "")[:4000]
        if "scheduledAt" in request.data and request.data["scheduledAt"]:
            appointment.scheduled_at = request.data["scheduledAt"]
        appointment.save()

        counterpart = appointment.doctor if request.user.role == ROLE_PATIENT else appointment.patient
        if counterpart:
            Notification.objects.create(
                id=new_id(),
                user=counterpart,
                type="APPOINTMENT_UPDATE",
                title=f"Appointment {next_status.lower()}",
                body=f"Appointment on {appointment.scheduled_at:%Y-%m-%d %H:%M} is now {next_status.lower()}.",
                link="/appointments",
            )
        record_audit(action="APPOINTMENT_UPDATE", request=request, actor=request.user,
                     resource_type="appointment", resource_id=appointment.id,
                     metadata={"status": next_status})
        return Response(serialize_appointment(appointment))


class NotificationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = request.user.notifications.all()[:50]
        return Response(
            {
                "unread": request.user.notifications.filter(is_read=False).count(),
                "results": [serialize_notification(n) for n in items],
            }
        )


class NotificationReadAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        updated = request.user.notifications.filter(pk=notification_id).update(
            is_read=True
        )
        if not updated:
            raise Http404
        return Response({"ok": True})


class NotificationReadAllAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({"ok": True})
