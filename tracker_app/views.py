
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
# Prefetch was added to these imports:
from django.db.models import Count, Q, Prefetch 
from .models import Theme, Action, ActionStatus 


# Create your views here.
def home(request):
    # This view displays the main home page
    return render(request, 'tracker_app/home.html', {})


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