from django.urls import path

from apps.connect import views

urlpatterns = [
    path("conversations/", views.ConversationListAPI.as_view(), name="api_conversations"),
    path("conversations/<str:conversation_id>/", views.ConversationDetailAPI.as_view(),
         name="api_conversation_detail"),
    path("appointments/", views.AppointmentListAPI.as_view(), name="api_appointments"),
    path("appointments/<str:appointment_id>/", views.AppointmentDetailAPI.as_view(),
         name="api_appointment_detail"),
    path("notifications/", views.NotificationListAPI.as_view(), name="api_notifications"),
    path("notifications/read-all/", views.NotificationReadAllAPI.as_view(), name="api_notifications_read_all"),
    path("notifications/<str:notification_id>/read/", views.NotificationReadAPI.as_view(),
         name="api_notification_read"),
]
