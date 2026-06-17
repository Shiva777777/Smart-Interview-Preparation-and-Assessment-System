from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_certificates_view, name='certificates_list'),
    path('generate/<int:attempt_id>/', views.generate_certificate_view, name='generate_certificate'),
]
