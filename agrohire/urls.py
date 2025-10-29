"""
URL configuration for agrohire project.

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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls
from . import views
from users.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    # path('/http://127.0.0.1:8000/admin/', admin.site.urls),
    path('accounts/', include('users.urls')),
    # path('', include('users.urls')),
    path('', include('equipment.urls')),
    path('', include('bookings.urls')),
    path('', include('pricing.urls')),
    path('', include('payments.urls')),
    path('', include('notifications.urls')),
    path('maintenance/', include('maintenance.urls')),
    # path('api/docs/', include_docs_urls(title='AgroHire API')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "AgroHire Administration"
admin.site.site_title = "AgroHire Admin Portal"
admin.site.index_title = "Welcome to AgroHire Administration"
