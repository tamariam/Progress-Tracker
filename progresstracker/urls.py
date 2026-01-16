"""
URL configuration for progresstracker project.

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
from django.urls import path,include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

# urlpatterns = [
#     path('i18n/', include('django.conf.urls.i18n')),  #for language switching
#     path('admin/', admin.site.urls),
#     path('summernote/', include('django_summernote.urls')),
#     path('', include('tracker_app.urls')),
# ]

# 2. URLs that NEVER change (The language switcher logic)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Serve static files here!

# 3. URLs that WILL change (Your Home Page)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('', include('tracker_app.urls')), # This is your Home Page
    prefix_default_language=True # This forces /en/ or /ga/ to show in the bar
)
