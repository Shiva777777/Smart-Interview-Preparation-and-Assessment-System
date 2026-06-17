from django.urls import path
from . import views

urlpatterns = [
    path('', views.roadmap_view, name='roadmap_display'),
    path('toggle/<int:milestone_id>/', views.toggle_milestone_view, name='toggle_milestone'),
]
