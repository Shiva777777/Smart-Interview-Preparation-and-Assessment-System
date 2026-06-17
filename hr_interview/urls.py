from django.urls import path
from . import views

urlpatterns = [
    path('', views.hr_home_view, name='hr_home'),
    path('session/<int:question_id>/', views.hr_session_view, name='hr_session'),
    path('tts/<int:question_id>/', views.hr_tts_view, name='hr_tts'),
    path('stt/', views.hr_stt_view, name='hr_stt'),
    path('evaluate/<int:question_id>/', views.hr_evaluate_view, name='hr_evaluate'),
]
