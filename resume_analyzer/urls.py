from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.resume_upload_view, name='resume_upload'),
    path('result/', views.resume_result_view, name='resume_result'),
]
