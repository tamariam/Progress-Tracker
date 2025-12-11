# from django.contrib import admin # This line should already be here
# Import SummernoteModelAdmin to enable rich text editing in the admin
# from django_summernote.admin import SummernoteModelAdmin 
# from django.core.mail import send_mail
# from django.conf import settings
# from django.urls import reverse
# from .models import Theme, Objective, Action, ActionStatus # This line should already be here

from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin 
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags # <--- ADDED THIS IMPORT
from .models import Theme, Objective, Action, ActionStatus # <--- ENSURE ActionStatus IS IMPORTED


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "title",)
    search_fields = ("title",)


@admin.register(Objective)
class ObjectiveAdmin(SummernoteModelAdmin):
    list_display = ("title", "theme")
    list_filter = ("theme",)
    search_fields = ("title", "description")
    summernote_fields = ('description',)


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
    list_filter = ("objective", "status",  "is_approved", "updated_by")
    search_fields = ("title", "small_description", "description", "update")
    # list_editable removed to control approval status programmatically
    # list_editable = ("is_approved",) 
    # Attribution and timestamps are managed automatically, so set them as read-only
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    summernote_fields = ('description', 'update') # Enable Summernote for these fields
    
    def save_model(self, request, obj, form, change):
        """
        Custom save logic: Superusers auto-approve, others require manual approval 
        and trigger an email notification. Also manages status based on update field.
        """
        # Determine user status early
        is_super = request.user.is_superuser

        # 1. Set attribution fields
        if not change and obj.created_by is None:
            # Set creator only on the first save (creation)
            obj.created_by = request.user
        
        # Always set the last updater to the current user
        obj.updated_by = request.user

        # 2. Implement automatic status change logic (The key logic you requested)
        user_selected_status = form.cleaned_data.get('status')
        # Use strip_tags to determine if the summernote field actually has content, ignoring empty HTML
        plain_update_text = strip_tags(form.cleaned_data.get('update') or "").strip()
        
        # Only override the status IF the user did not explicitly select 'Completed' manually
        if user_selected_status != ActionStatus.COMPLETED:
            if plain_update_text:
                # If there is meaningful text in the update field, mark as in progress
                obj.status = ActionStatus.IN_PROGRESS
            else:
                # If the update field is empty, default to not started (overrides 'In Progress' if update text is empty)
                obj.status = ActionStatus.NOT_STARTED
        
        # If the user selected 'Completed' manually, we respect that choice.


        # 3. Implement the approval logic based on the user's status
        if is_super:
            # Superusers automatically approve their own changes/creations
            obj.is_approved = True
        else:
            # Regular users require approval (set to False)
            obj.is_approved = False

        # 4. Save first so obj.pk is available for the URL
        super().save_model(request, obj, form, change)

        # 5. Send notification ONLY when a regular user makes a change that needs approval
        if not is_super:
            # Build admin change URL for quick review
            try:
                change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,))
                full_url = request.build_absolute_uri(change_url)
            except Exception:
                full_url = "(open admin and review)"

            send_mail(
                subject=f'Approval needed: "{obj.title}" was updated',
                message=(
                    f'User {request.user.get_username()} updated the action "{obj.title}".\n'
                    f'It requires approval.\n\n'
                    f'Open: {full_url}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[
                    # !!! CRITICAL: Change this to the email address of your approver(s) !!!
                    'superuser@meathcoco.ie' 
                ],
                fail_silently=True,
            )

    def get_queryset(self, request):
        """
        Filter the admin list view: Regular users only see approved items.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(is_approved=True)
        return qs
