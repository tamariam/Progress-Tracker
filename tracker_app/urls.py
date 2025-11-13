# tracker_app/urls.py
from django.urls import path
from .views import home, get_theme_details 

app_name = 'tracker_app' # <-- This is vital

urlpatterns = [
    path('', home, name='home'),
    path('api/theme-details/<int:theme_id>/', get_theme_details, name='get_theme_details'),
]
