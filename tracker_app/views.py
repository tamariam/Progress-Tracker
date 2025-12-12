
from django.shortcuts import render,    get_object_or_404   
from django.template.loader import render_to_string
from django.http import JsonResponse
# Prefetch was added to these imports:
from django.db.models import Count, Q, Prefetch 
from .models import Theme, Action, ActionStatus 


# Create your views here.
def home(request):
    # This view displays the main home page
    return render(request, 'tracker_app/home.html', {})

def get_actions_by_status(request, theme_id, status_filter):
    """
    API endpoint to fetch actions for a theme filtered by status.
    Returns HTML/JSON for a unified table modal.
    """
    PUBLIC_ACTIONS_FILTER = Q(is_approved=True)
    
    # Ensure the status filter provided is valid (using the internal database values)
    valid_statuses = [choice[0] for choice in ActionStatus.choices] # Use choice[0] to get the value
    if status_filter not in valid_statuses:
        return JsonResponse({'error': 'Invalid status filter provided.'}, status=400)

    # Fetch approved actions matching the theme and status
    actions_list = Action.objects.filter(
        objective__theme_id=theme_id
    ).filter(
        PUBLIC_ACTIONS_FILTER
    ).filter(
        status=status_filter
    ).order_by(
        'title' # Order alphabetically
    )

    theme = get_object_or_404(Theme, pk=theme_id)
    
    # Render the new actions.html template file
    html_content = render_to_string(
        'tracker_app/actions.html', 
        {'actions_list': actions_list, 'theme': theme, 'status_filter': status_filter},
        request=request
    )
    
    # Use ActionStatus.choices to get the professional display name
    status_display_name = dict(ActionStatus.choices)[status_filter]

    return JsonResponse({
        'html_content': html_content, 
        'title': f'{theme.title} | {status_display_name} Actions'
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