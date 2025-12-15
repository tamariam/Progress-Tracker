
from django.shortcuts import render, get_object_or_404   
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch 
# Ensure you import your models:
from .models import Theme, Action, ActionStatus 
from django.utils.html import strip_tags 


PUBLIC_ACTIONS_FILTER = Q(is_approved=True)

# Create your views here.
def home(request):
    # This view displays the main home page
    return render(request, 'tracker_app/home.html', {})


def get_filtered_actions_by_status(request, status):
    """
    API endpoint to fetch all approved actions matching a specific status 
    and return them as JSON data.
    """
    # Map the URL string identifier to the actual Django model choice value
    status_map = {
        'completed': ActionStatus.COMPLETED,
        'in_progress': ActionStatus.IN_PROGRESS,
        'not_started': ActionStatus.NOT_STARTED,
    }

    # Validate the status provided in the URL
    target_status = status_map.get(status.lower())
    if not target_status:
        return JsonResponse({'error': 'Invalid status provided.'}, status=400)

    # Fetch approved actions matching the status
    actions = Action.objects.filter(
        PUBLIC_ACTIONS_FILTER # from your existing views.py filter
    ).filter(
        status=target_status
    ).select_related('objective') # Optimise query to get objective title later

    # Format the data into a simple list of dictionaries for the frontend JS
    data = []
    for action in actions:
        data.append({
            'title': action.title,
            'small_description': action.small_description,
            # Use strip_tags because SummernoteTextField might contain HTML you don't want in a raw JSON list
            'description': strip_tags(action.description), 
            # Return the raw status code (e.g. NOT_STARTED, IN_PROGRESS, COMPLETED)
            # so the frontend can reliably build CSS classes like "status-in_progress".
            'status': action.status,
            'status_display': action.get_status_display(),
            'objective_title': action.objective.title, # Access the related objective title
        })

    return JsonResponse({
        'status_requested': status.lower(),
        'status_title': status.replace('_', ' ').title(),
        'count': len(data),
        'actions': data
    })

def get_theme_details(request, theme_id):
    """ 
    API endpoint to fetch a single theme's details and return HTML/JSON.
    Fetches ONLY approved actions that are ready for public view.
    """
    
    # Define a base queryset filter for "publicly visible" actions
    PUBLIC_ACTIONS_FILTER = Q(is_approved=True)

    # 1. Fetch the theme, but restrict the prefetched actions to only approved ones.
    # This uses the Prefetch object to apply the filter when fetching related data.
    theme = Theme.objects.filter(pk=theme_id).prefetch_related(
       Prefetch(
           'objectives__actions', 
           queryset=Action.objects.filter(PUBLIC_ACTIONS_FILTER), # Apply the approved filter here
           to_attr='approved_actions' # We use 'approved_actions' in the template now
       )
    ).first()
    
    if not theme:
        return JsonResponse({
            'html_content': '<p>This strategic theme does not exist or has been removed.</p>',
            'title': 'Theme Not Found'
        }, status=404)

    # 2. Calculate counts based *only* on the publicly visible actions
    # The counts here will match the totals displayed by the progress bars in the template
    theme_actions = Action.objects.filter(objective__theme=theme).filter(PUBLIC_ACTIONS_FILTER)
    action_counts = theme_actions.aggregate(
        completed=Count('id', filter=Q(status=ActionStatus.COMPLETED)),
        in_progress=Count('id', filter=Q(status=ActionStatus.IN_PROGRESS)),
        not_started=Count('id', filter=Q(status=ActionStatus.NOT_STARTED)),
    )
    
    # Render the HTML fragment using the theme object and the counts
    html_content = render_to_string(
        'tracker_app/modal_content_fragment.html', # <-- Make sure this is your correct template path
        {'theme': theme, 'counts': action_counts},
        request=request
    )
    
    return JsonResponse({'html_content': html_content, 'title': theme.title})