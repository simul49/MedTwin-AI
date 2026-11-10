from django.urls import path

from apps.ai import views

urlpatterns = [
    path("ai/chat/", views.ChatAPI.as_view(), name="api_ai_chat"),
    path("ai/conversations/", views.AiConversationListAPI.as_view(), name="api_ai_conversations"),
    path("ai/conversations/<str:conversation_id>/", views.AiConversationDetailAPI.as_view(),
         name="api_ai_conversation_detail"),
    path("ai/history/", views.AiHistoryAPI.as_view(), name="api_ai_history"),
    path("recommendations/", views.RecommendationListAPI.as_view(), name="api_recommendations"),
    path("recommendations/<str:recommendation_id>/feedback/", views.RecommendationFeedbackAPI.as_view(),
         name="api_recommendation_feedback"),
    path("safety/evaluate/", views.SafetyEvaluateAPI.as_view(), name="api_safety_evaluate"),
    path("content-analysis/", views.ContentAnalysisAPI.as_view(), name="api_content_analysis"),
]
