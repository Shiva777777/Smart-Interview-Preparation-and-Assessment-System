from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_home_view, name='quiz_home'),
    path('manual-skills/', views.manual_skill_select_view, name='manual_skill_select'),
    path('generate/', views.generate_personalized_quiz_view, name='quiz_generate_from_skills'),
    path('start/', views.start_quiz_session_view, name='quiz_start'),
    path('session/', views.quiz_session_view, name='quiz_session'),
    path('submit/', views.quiz_submit_view, name='quiz_submit'),
    path('result/<int:attempt_id>/', views.quiz_result_view, name='quiz_result'),
]
