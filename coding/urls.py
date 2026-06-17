from django.urls import path
from . import views

urlpatterns = [
    path('', views.coding_home_view, name='coding_home'),
    path('session/<int:question_id>/', views.coding_session_view, name='coding_session'),
    path('run/<int:question_id>/', views.coding_run_view, name='coding_run'),
    path('submit/<int:question_id>/', views.coding_submit_view, name='coding_submit'),
]
