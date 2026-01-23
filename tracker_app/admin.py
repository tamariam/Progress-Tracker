from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin 
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags 
# NEW IMPORT: Necessary for custom admin labels
from django.utils.translation import gettext_lazy as _

# Ensure all your models and ActionStatus are imported correctly
from .models import Theme, Objective, Action, ActionStatus 


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "title_ga") # ADDED: Show both titles
    search_fields = ("title", "title_ga") # ADDED: Search both titles


@admin.register(Objective)
class ObjectiveAdmin(SummernoteModelAdmin):
    list_display = ("title", "theme")
    list_filter = ("theme",)
    search_fields = ("title", "description", "description_ga") # ADDED: Search both descriptions
    summernote_fields = ('description', 'description_ga') # ADDED: Summernote for Irish


@admin.register(Action)
class ActionAdmin(SummernoteModelAdmin):
    list_display = (
        "title",
        "small_description",
        "objective",
        "status",
        "is_approved",
        "is_ga_approved", # ADDED: Show Irish approval status in list
        "updated_by",
        "updated_at",
    )
    list_filter = ("objective", "status", "is_approved", "is_ga_approved", "updated_by") # ADDED: Filter by Irish status
    search_fields = ("title", "small_description", "description", "update",
                     "small_description_ga", "description_ga", "update_ga") # ADDED: Search both languages
    
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    
    # ADDED: Enable Summernote for BOTH languages
    summernote_fields = ('description', 'update', 'description_ga', 'update_ga') 

    # ADDED: Organize the edit page for dual language clarity
    fieldsets = (
        (None, {'fields': ('title',)}),
        (_('English Content (Standard Approval)'), {'fields': ('small_description', 'description', 'update')}),
        (_('Irish Content (Superuser Approval Required)'), {'fields': ('is_ga_approved', 'small_description_ga', 'description_ga', 'update_ga')}),
        (_('System Status & Attribution'), {'fields': ('status', 'objective', 'is_approved', 'created_by', 'updated_by', 'created_at', 'updated_at')}),
    )
    

    def save_model(self, request, obj, form, change):
        is_super = request.user.is_superuser

        # 1. Attribution (Existing Logic)
        if not change and obj.created_by is None:
            obj.created_by = request.user
        obj.updated_by = request.user

        # 2. THE DUAL-LANGUAGE STATUS LOGIC (New Logic)
        # Automatic Status Switch: Set "In Progress" if EITHER language has an update
        user_selected_status = form.cleaned_data.get('status')
        plain_update_en = strip_tags(form.cleaned_data.get('update') or "").strip()
        plain_update_ga = strip_tags(form.cleaned_data.get('update_ga') or "").strip()
        
        if user_selected_status != ActionStatus.COMPLETED:
            if plain_update_en or plain_update_ga:
                obj.status = ActionStatus.IN_PROGRESS
            else:
                obj.status = ActionStatus.NOT_STARTED

        # 3. IRISH APPROVAL FIREWALL (New Logic)
        if not is_super:
            # If a regular user touches ANY Irish field, we reset approval to False
            irish_fields = ['small_description_ga', 'description_ga', 'update_ga', 'title_ga']
            if any(field in form.changed_data for field in irish_fields):
                obj.is_ga_approved = False
            
            # Standard English approval logic stays the same
            obj.is_approved = False
        # If it is a superuser, they manually use the checkbox to approve the content

        # 4. Save first for the email URL (Existing Logic)
        super().save_model(request, obj, form, change)

        # 5. Send Notification (Existing Logic)
        if not is_super:
            # ... (keep your existing send_mail code here) ...
            pass
            
    # You had a get_queryset method here, I kept it as you wrote it
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(is_approved=True)
        return qs

