
from django.shortcuts import render, get_object_or_404   
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch 
from .models import Theme, Action, ActionStatus 
from django.utils.html import strip_tags 
from django.core.paginator import Paginator
from django.http import JsonResponse

PUBLIC_ACTIONS_FILTER = Q(is_approved=True)


def home(request):
    # This view displays the main home page
    return render(request, 'tracker_app/home.html', {})


def get_filtered_actions_by_status(request, status):
    # Mapping and filtering
    status_map = {
        'completed': ActionStatus.COMPLETED,
        'in_progress': ActionStatus.IN_PROGRESS,
        'not_started': ActionStatus.NOT_STARTED,
    }
    target_status = status_map.get(status.lower())
    
    # Order by ID or date to ensure consistent pagination
    actions_list = Action.objects.filter(is_approved=True, status=target_status).order_by('id')
    
    # Paginate: 10 actions per page
    paginator = Paginator(actions_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    data = [{
        'id': action.id,
        'title': action.title,
        'small_description': action.small_description,
        'description': action.description,
        'status': action.status,
        'objective_title': action.objective.title,
        'update': action.update  if action.update else ""
    } for action in page_obj]

    return JsonResponse({
        'status_title': status.replace('_', ' ').title(),
        'actions': data,
        'count': paginator.count,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })

def get_theme_details(request, theme_id):
    """ 
    API endpoint to fetch a single theme's details and return HTML/JSON.
    Fetches ONLY approved actions that are ready for public view.
    """
    
    # Define a base queryset filter for  publicly visible actions
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

    # 2. Calculate counts based only  on the publicly visible actions
    
    theme_actions = Action.objects.filter(objective__theme=theme).filter(PUBLIC_ACTIONS_FILTER)
    action_counts = theme_actions.aggregate(
        completed=Count('id', filter=Q(status=ActionStatus.COMPLETED)),
        in_progress=Count('id', filter=Q(status=ActionStatus.IN_PROGRESS)),
        not_started=Count('id', filter=Q(status=ActionStatus.NOT_STARTED)),
    )
    
    # Render the HTML fragment using the theme object and the counts
    html_content = render_to_string(
        'tracker_app/modal_content_fragment.html',
        {'theme': theme, 'counts': action_counts},
        request=request
    )
    
    return JsonResponse({'html_content': html_content, 'title': theme.title})