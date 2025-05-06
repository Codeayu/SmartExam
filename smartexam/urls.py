"""
URL configuration for smartexam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path as url_path  # Renamed to avoid potential conflicts
from core.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url_path('admin/', admin.site.urls),
    url_path('', home, name='home'),  # Home page URL
    url_path('login/', login1, name='login'),  # Login page URL
    url_path('register/', register, name='register'),  # Registration page URL
    url_path('logout/', logout_view, name='logout'),  # Logout URL
    url_path('result/', result, name='result'),  # Results page URL
    url_path('dashboard/', dashboard, name='dashboard'),  # Dashboard URL
    url_path('about/', about, name='about'),  # About page URL (same as home for now)
    url_path('features/', features, name='features'),  # Features page URL
    url_path('pricing/', pricing, name='pricing'),  # Pricing page URL
    url_path('support/', support, name='support'),  # Support page URL
    url_path('contact/', contact, name='contact'),  # Contact page URL
    
    # New URLs for enhanced functionality
    url_path('save-question/', save_question, name='save_question'),  # Save question URL
    url_path('add-note/<int:question_id>/', add_note, name='add_note'),  # Add note to saved question
    url_path('delete-question/<int:question_id>/', delete_saved_question, name='delete_question'),  # Delete saved question
    url_path('export-questions/<int:history_id>/', export_questions, name='export_questions'),  # Export questions as PDF
    url_path('connection-limit/', connection_limit, name='connection_limit'),  # Connection limit page
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)