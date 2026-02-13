# tracker_app/urls.py
from django.urls import path
from .views import (
    get_filtered_actions_by_status,
    get_roadmap_data,
    get_theme_details,
    home,
    preview_403,
    preview_404,
    preview_500,
)

app_name = 'tracker_app' # <-- This is vital

urlpatterns = [
    path('', home, name='home'),
    path('api/roadmap-data/', get_roadmap_data, name='roadmap_data'),
    path('api/theme-details/<int:theme_id>/', get_theme_details, name='get_theme_details'),
    path('api/actions/filter/<str:status>/', get_filtered_actions_by_status, name='filter_actions_by_status'),

    # Temporary preview routes for error pages (safe to remove later)
    path('debug/preview-403/', preview_403, name='preview_403'),
    path('debug/preview-404/', preview_404, name='preview_404'),
    path('debug/preview-500/', preview_500, name='preview_500'),
    
    
]
