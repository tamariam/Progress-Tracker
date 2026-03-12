from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin 
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags 
from django.contrib.auth import get_user_model

from .models import Theme, Objective, Action, ActionStatus 
from datetime import date


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "title_ga")
    search_fields = ("title", "title_ga")


@admin.register(Objective)
class ObjectiveAdmin(SummernoteModelAdmin):
    list_display = ("title", "theme")
    list_filter = ("theme",)
    search_fields = ("title", "description", "description_ga")
    summernote_fields = ('description', 'description_ga')


@admin.register(Action)
class ActionAdmin(SummernoteModelAdmin):
    list_display = (
        "title",
        "small_description",
        "objective",
        "status",
        "progress_started_at",
        "is_approved",
        "updated_by",
        "updated_at",
    )
    
    list_filter = ("objective", "status", "progress_started_at", "is_approved", "updated_by") 
    search_fields = ("title", "small_description", "description", "update",
                     "small_description_ga", "description_ga", "update_ga")
    
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    summernote_fields = ('description', 'update', 'description_ga', 'update_ga') 

    fieldsets = (
        (None, {'fields': ('title',)}),
        ('English Content', {'fields': ('small_description', 'description', 'update')}),
        ('Irish Content', {'fields': ('small_description_ga', 'description_ga', 'update_ga')}),
        ('System Status & Attribution', {'fields': ('status', 'progress_started_at', 'objective', 'is_approved', 'created_by', 'updated_by', 'created_at', 'updated_at')}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.extend([
                'title', 'objective', 'status', 'is_approved', 
                'small_description', 'small_description_ga', 
                'description', 'description_ga'
            ])
        return readonly

    def save_model(self, request, obj, form, change):
        is_super = request.user.is_superuser

        if not change and obj.created_by is None:
            obj.created_by = request.user
        obj.updated_by = request.user

        plain_update_en = strip_tags(form.cleaned_data.get('update') or "").strip()
        plain_update_ga = strip_tags(form.cleaned_data.get('update_ga') or "").strip()
        user_selected_status = form.cleaned_data.get('status')

        if is_super:
            obj.is_approved = True
            if user_selected_status != ActionStatus.COMPLETED:
                if plain_update_en or plain_update_ga:
                    obj.status = ActionStatus.IN_PROGRESS
                else:
                    obj.status = ActionStatus.NOT_STARTED
        else:
            obj.is_approved = False
            if user_selected_status != ActionStatus.COMPLETED:
                obj.status = ActionStatus.NOT_STARTED
        
        # If status has become In Progress and no start date is set, record it once.
        if obj.status == ActionStatus.IN_PROGRESS and not obj.progress_started_at:
            obj.progress_started_at = date.today()

        # If an action is marked completed, ensure it's approved so it appears
        # immediately on public charts and KPI totals.
        if obj.status == ActionStatus.COMPLETED:
            obj.is_approved = True

        super().save_model(request, obj, form, change)

        # THE NOTIFICATION LOGIC
        if not is_super:
            update_changed = 'update' in form.changed_data
            update_ga_changed = 'update_ga' in form.changed_data

            if change and (update_changed or update_ga_changed):
                subject = f"Meath County Council – Action Update Pending Approval: {obj.title}"
                
                admin_url = request.build_absolute_uri(
                    reverse('admin:tracker_app_action_change', args=[obj.id])
                )

                if update_changed and update_ga_changed:
                    update_note = "ENGLISH and IRISH"
                elif update_ga_changed:
                    update_note = "IRISH"
                else:
                    update_note = "ENGLISH"
                
                message = (
                    "Meath County Council – Digital and ICT Strategy Tracker\n\n"
                    f"User {request.user.username} has updated the {update_note} progress for: {obj.title}.\n\n"
                    f"Please review and approve the update here: {admin_url}\n\n"
                    f"Note: Updates are hidden from the public until you click Save."
                )

                # FIND THE BOSS: Get all superuser emails
                superusers = get_user_model().objects.filter(is_superuser=True).values_list('email', flat=True)
                
                if superusers:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        list(superusers),
                        fail_silently=True
                    )

    # FIXED INDENTATION: This is now correctly a method of ActionAdmin
    def get_queryset(self, request):
        return super().get_queryset(request)
