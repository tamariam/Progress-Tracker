
from django.shortcuts import render, get_object_or_404   
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch 
from django.db.models.functions import TruncMonth
from django.utils import timezone
import calendar
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


def _build_roadmap_payload(year_param):
    """Builds Roadmap chart + KPI payload for a given year."""
    current_year = timezone.now().year
    default_year = 2026 if current_year >= 2026 else current_year
    try:
        chart_year = int(year_param) if year_param else default_year
    except ValueError:
        chart_year = default_year

    if chart_year < 2025 or chart_year > current_year:
        chart_year = default_year

    monthly_counts = (
        Action.objects.filter(
            is_approved=True,
            status__in=[ActionStatus.COMPLETED, ActionStatus.IN_PROGRESS],
            updated_at__year=chart_year,
        )
        .annotate(month=TruncMonth("updated_at"))
        .values("month", "status")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    completed_totals = {}
    in_progress_totals = {}
    for item in monthly_counts:
        month_value = item["month"].month if item["month"] else None
        if not month_value:
            continue
        if item["status"] == ActionStatus.COMPLETED:
            completed_totals[month_value] = item["total"]
        elif item["status"] == ActionStatus.IN_PROGRESS:
            in_progress_totals[month_value] = item["total"]

    labels_en = [calendar.month_name[i] for i in range(1, 13)]
    labels_ga = [
        "Eanáir",
        "Feabhra",
        "Márta",
        "Aibreán",
        "Bealtaine",
        "Meitheamh",
        "Iúil",
        "Lúnasa",
        "Meán Fómhair",
        "Deireadh Fómhair",
        "Samhain",
        "Nollaig",
    ]
    chart_data_completed = [completed_totals.get(i, 0) for i in range(1, 13)]
    chart_data_in_progress = [in_progress_totals.get(i, 0) for i in range(1, 13)]
    completed_total_year = sum(chart_data_completed)
    in_progress_total_year = sum(chart_data_in_progress)

    return {
        "chart_year": chart_year,
        "chart_labels_en": labels_en,
        "chart_labels_ga": labels_ga,
        "chart_data_completed": chart_data_completed,
        "chart_data_in_progress": chart_data_in_progress,
        "completed_total_year": completed_total_year,
        "in_progress_total_year": in_progress_total_year,
        "year_options": list(range(2025, current_year + 1)),
    }


def home(request):
    """Render the public-facing home page template."""
    roadmap_payload = _build_roadmap_payload(request.GET.get("year"))
    return render(request, 'tracker_app/home.html', roadmap_payload)


def get_roadmap_data(request):
    """Return Roadmap chart data for AJAX year changes."""
    payload = _build_roadmap_payload(request.GET.get("year"))
    return JsonResponse(payload)




def get_filtered_actions_by_status(request, status):
    """Return paginated actions for a given status, with bilingual fallback handling."""


    # Map URL status tokens to ActionStatus values used in the database.
    status_map = {
        'completed': ActionStatus.COMPLETED,
        'in_progress': ActionStatus.IN_PROGRESS,
        'not_started': ActionStatus.NOT_STARTED,
    }
    target_status = status_map.get(status.lower())
    
    # Base queryset for the requested status, optionally scoped by theme.
    actions_list = Action.objects.filter(status=target_status)
    theme_id = request.GET.get('theme_id')
    if theme_id:
        actions_list = actions_list.filter(objective__theme_id=theme_id)
    actions_list = actions_list.order_by('id')
    
    # Paginate results for incremental loading in the modal list.
    paginator = Paginator(actions_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Dual-language behavior: prefer Irish content when language is Irish and approved.
    current_lang = get_language()
    is_ga = current_lang == 'ga'

    # Build the JSON payload with safe bilingual fallbacks.
    data = []
    for action in page_obj:
        # Use Irish only when on the Irish site and the translation is approved.
        show_ga = is_ga and action.is_ga_approved

        data.append({
            'id': action.id,
            'title': action.title,  # Remains same for both
            # Prefer Irish fields when approved, otherwise fallback to English.
            'small_description': action.small_description_ga if show_ga and action.small_description_ga else action.small_description,
            'description': action.description_ga if show_ga and action.description_ga else action.description,
            # .get_status_display() uses the translated label from the .po file.
            'status': action.get_status_display(),
            'objective_title': action.objective.title,
            'update': action.update_ga if show_ga and action.update_ga else (action.update if action.update else "")
        })

    # Return the payload expected by the modal UI.
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
    """Return the HTML fragment and localized title for a single theme modal."""
    PUBLIC_ACTIONS_FILTER = Q()
    current_language = get_language()
    
    # Fetch theme with prefetched approved actions for modal rendering.
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

    # Calculate counts for the status cards inside the modal.
    theme_actions = Action.objects.filter(objective__theme=theme).filter(PUBLIC_ACTIONS_FILTER)
    action_counts = theme_actions.aggregate(
        completed=Count('id', filter=Q(status=ActionStatus.COMPLETED)),
        in_progress=Count('id', filter=Q(status=ActionStatus.IN_PROGRESS)),
        not_started=Count('id', filter=Q(status=ActionStatus.NOT_STARTED)),
    )
    
    # Activate translation so the fragment template renders in the correct language.
    translation.activate(current_language)
    
    html_content = render_to_string(
        'tracker_app/modal_content_fragment.html',
        {'theme': theme, 'counts': action_counts},
        request=request
    )
    
    # Localize the modal header title with Irish fallback when available.
    theme_title = theme.title_ga if current_language == 'ga' and theme.title_ga else theme.title
    
    translation.deactivate()
    
    return JsonResponse({'html_content': html_content, 'title': theme_title})


def preview_404(request):
    return render(request, '404.html', status=404)


def preview_403(request):
    return render(request, '403.html', status=403)


def preview_500(request):
    return render(request, '500.html', status=500)