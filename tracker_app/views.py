
from django.shortcuts import render, get_object_or_404   
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch 
from .models import Theme, Action, ActionStatus 
from django.utils.html import strip_tags 
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import translation
from django.utils.translation import get_language
# Change your translation import to this:
from django.utils.translation import gettext as _ 
from django.utils.translation import get_language, activate

PUBLIC_ACTIONS_FILTER = Q()


def home(request):
    # This view displays the main home page
    return render(request, 'tracker_app/home.html', {})




def get_filtered_actions_by_status(request, status):
    """
    Fetches filtered actions for the status cards (Completed, In Progress, etc.)
    with automatic Irish Fallback logic.
    """


    status_map = {
        'completed': ActionStatus.COMPLETED,
        'in_progress': ActionStatus.IN_PROGRESS,
        'not_started': ActionStatus.NOT_STARTED,
    }
    target_status = status_map.get(status.lower())
    
    actions_list = Action.objects.filter(status=target_status)
    theme_id = request.GET.get('theme_id')
    if theme_id:
        actions_list = actions_list.filter(objective__theme_id=theme_id)
    actions_list = actions_list.order_by('id')
    
    paginator = Paginator(actions_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 2026 Dual Language Logic
    current_lang = get_language()
    is_ga = current_lang == 'ga'

    data = []
    for action in page_obj:
        # FIREWALL: Use Irish only if on Irish site AND superuser approved the translation
        show_ga = is_ga and action.is_ga_approved

        data.append({
            'id': action.id,
            'title': action.title, # Remains same for both
            # DUALITY: Fetch _ga field if approved, else fallback to English
            'small_description': action.small_description_ga if show_ga and action.small_description_ga else action.small_description,
            'description': action.description_ga if show_ga and action.description_ga else action.description,
            # STATUS: .get_status_display() pulls the translation from your .po file automatically
            'status': action.get_status_display(),
            'objective_title': action.objective.title,
            'update': action.update_ga if show_ga and action.update_ga else (action.update if action.update else "")
        })

    return JsonResponse({
        'status_title': _(status.replace('_', ' ').title()),
        'actions': data,
        'count': paginator.count,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(), 
        'has_previous': page_obj.has_previous(),
    })

def get_theme_details(request, theme_id):
    """ 
    API endpoint to fetch a single theme's details.
    Handles the Irish Title and the Modal Accordion content.
    """
    PUBLIC_ACTIONS_FILTER = Q()
    current_language = get_language()
    
    # Fetch theme with prefetched approved actions
    theme = Theme.objects.filter(pk=theme_id).prefetch_related(
       Prefetch(
           'objectives__actions', 
           queryset=Action.objects.filter(PUBLIC_ACTIONS_FILTER),
           to_attr='approved_actions'
       )
    ).first()
    
    if not theme:
        return JsonResponse({
            'html_content': '<p>Strategic theme not found.</p>',
            'title': 'Error'
        }, status=404)

    # Calculate counts for the status cards inside the modal
    theme_actions = Action.objects.filter(objective__theme=theme).filter(PUBLIC_ACTIONS_FILTER)
    action_counts = theme_actions.aggregate(
        completed=Count('id', filter=Q(status=ActionStatus.COMPLETED)),
        in_progress=Count('id', filter=Q(status=ActionStatus.IN_PROGRESS)),
        not_started=Count('id', filter=Q(status=ActionStatus.NOT_STARTED)),
    )
    
    # Activate translation so the fragment template sees the correct language
    translation.activate(current_language)
    
    html_content = render_to_string(
        'tracker_app/modal_content_fragment.html',
        {'theme': theme, 'counts': action_counts},
        request=request
    )
    
    # DUALITY for the Modal Header Title
    theme_title = theme.title_ga if current_language == 'ga' and theme.title_ga else theme.title
    
    translation.deactivate()
    
    return JsonResponse({'html_content': html_content, 'title': theme_title})