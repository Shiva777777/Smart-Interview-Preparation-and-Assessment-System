from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('resume/', include('resume_analyzer.urls')),
    path('quiz/', include('quiz.urls')),
    path('coding/', include('coding.urls')),
    path('hr/', include('hr_interview.urls')),
    path('recommendation/', include('recommendation.urls')),
    path('roadmap/', include('roadmap.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('certificates/', include('certificates.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
