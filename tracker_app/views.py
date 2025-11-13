from django.shortcuts import render,get_object_or_404
from django.template.loader import render_to_string
from.models import Theme, Action ,Objective  
from django.http import JsonResponse 



# Create your views here.
def home(request):
    return render(request, 'tracker_app/home.html', {})


# def get_theme_details(request, theme_id):
#     print(f"--- Fetching theme ID: {theme_id} ---") # Added print
#     theme = get_object_or_404(Theme.objects.prefetch_related('objectives__actions'), pk=theme_id)
#     print(f"--- Theme found: {theme.title} ---") # Added print
    
#     html_content = render_to_string(
#         'tracker_app/modal_content_fragment.html', 
#         {'theme': theme},
#         request=request
#     )
#     print("--- Template rendered successfully ---") # This likely won't print before crash
    
#     return JsonResponse({'html_content': html_content, 'title': theme.title})

# tracker_app/views.py

def get_theme_details(request, theme_id):
    """ 
    API endpoint to fetch a single theme's details and return HTML/JSON.
    Returns a custom message if the theme ID is not found.
    """
    # Use filter() instead of get_object_or_404(). .first() returns None if not found.
    theme = Theme.objects.filter(pk=theme_id).prefetch_related(
       'objectives__actions'
    ).first()
    
    # If the theme doesn't exist, return a generic "Not Found" JSON response
    if not theme:
        return JsonResponse({
            'html_content': '<p>This strategic theme does not exist or has been removed.</p>',
            'title': 'Theme Not Found'
        }, status=404) # It's still good practice to return a 404 HTTP status code

    # --- MANUAL DATA FILTERING START (as before) ---
    for objective in theme.objectives.all():
        objective.active_actions = objective.actions.filter(is_progress=True)
    # --- MANUAL DATA FILTERING END ---

    html_content = render_to_string(
        'tracker_app/modal_content_fragment.html', 
        {'theme': theme},
        request=request
    )
    
    return JsonResponse({'html_content': html_content, 'title': theme.title})