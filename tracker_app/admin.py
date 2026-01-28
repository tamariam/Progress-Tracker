from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin 
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags 
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import Theme, Objective, Action, ActionStatus 


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
        "is_approved",
        "updated_by",
        "updated_at",
    )
    
    list_filter = ("objective", "status", "is_approved", "updated_by") 
    search_fields = ("title", "small_description", "description", "update",
                     "small_description_ga", "description_ga", "update_ga")
    
    # Base readonly fields for everyone
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    
    summernote_fields = ('description', 'update', 'description_ga', 'update_ga') 

    fieldsets = (
        (None, {'fields': ('title',)}),
        (_('English Content'), {'fields': ('small_description', 'description', 'update')}),
        (_('Irish Content'), {'fields': ('small_description_ga', 'description_ga', 'update_ga')}),
        (_('System Status & Attribution'), {'fields': ('status', 'objective', 'is_approved', 'created_by', 'updated_by', 'created_at', 'updated_at')}),
    )

    # 1. PERMISSIONS: Lock strategy fields for regular users
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            # Regular users can ONLY edit the 'update' and 'update_ga' boxes
            readonly.extend([
                'title', 'objective', 'status', 'is_approved', 
                'small_description', 'small_description_ga', 
                'description', 'description_ga'
            ])
        return readonly

    # 2. THE COMPLETE SAVE LOGIC
    def save_model(self, request, obj, form, change):
        is_super = request.user.is_superuser

        # A. Attribution (Who did it)
        if not change and obj.created_by is None:
            obj.created_by = request.user
        obj.updated_by = request.user

        # B. Status Automation: Set "In Progress" if EITHER language has text
        user_selected_status = form.cleaned_data.get('status')
        plain_update_en = strip_tags(form.cleaned_data.get('update') or "").strip()
        plain_update_ga = strip_tags(form.cleaned_data.get('update_ga') or "").strip()
        
        if user_selected_status != ActionStatus.COMPLETED:
            if plain_update_en or plain_update_ga:
                obj.status = ActionStatus.IN_PROGRESS
            else:
                obj.status = ActionStatus.NOT_STARTED

        # C. THE FIREWALL LOGIC: Superuser vs Staff
        if is_super:
            # If YOU (Superuser) save, it is approved INSTANTLY
            obj.is_approved = True
        else:
            # If STAFF saves, it is hidden for your review
            obj.is_approved = False
        
        # D. Save to Database
        super().save_model(request, obj, form, change)

        # E. Notification: Trigger email ONLY if the ENGLISH 'update' changed
        if not is_super:
            if change and 'update' in form.changed_data:
                subject = f"Action Update Pending Approval: {obj.title}"
                
                # Build the direct admin link
                admin_url = request.build_absolute_uri(
                    reverse('admin:tracker_app_action_change', args=[obj.id])
                )
                
                message = (
                    f"User {request.user.username} has updated the ENGLISH progress for: {obj.title}.\n\n"
                    f"Please review and approve the update here: {admin_url}\n\n"
                    f"Note: Updates are hidden from the public until you click Save."
                )

                superusers = get_user_model().objects.filter(is_superuser=True).values_list('email', flat=True)
                
                if superusers:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        list(superusers),
                        fail_silently=True
                    )
    def get_queryset(self, request):
    # This ensures everyone (Superusers AND Staff) can see the list of Actions
    # even if the 'Update' is still waiting for approval.
        return super().get_queryset(request)
