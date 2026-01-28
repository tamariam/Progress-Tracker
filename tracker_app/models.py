from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django_summernote.fields import SummernoteTextField
# NEW IMPORT: Necessary for marking text for the .po file
from django.utils.translation import gettext_lazy as _

class Theme(models.Model):
    title = models.CharField(max_length=200, unique=True)
    # New Irish field for Theme
    title_ga = models.CharField(max_length=200, unique=True, null=True, blank=True, verbose_name=_("Title (Irish)"))

    def __str__(self):
        return self.title


class Objective(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = SummernoteTextField(default="", blank=True)
    # New Irish field for Objective Description
    description_ga = SummernoteTextField(default="", blank=True, null=True, verbose_name=_("Description (Irish)"))
    
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='objectives')

    @property
    def display_title(self):
        """Returns Irish title if it exists, otherwise English."""
        from django.utils.translation import get_language
        # If we are in Irish hallway and Irish title is not empty
        if get_language() == 'ga' and hasattr(self, 'title_ga') and self.title_ga:
            return self.title_ga
        return self.title

    @property
    def display_description(self):
        """Returns Irish description if it exists, otherwise English."""
        from django.utils.translation import get_language
        if get_language() == 'ga' and self.description_ga:
            return self.description_ga
        return self.description

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class ActionStatus(models.TextChoices):
    # We wrap the labels in _() so they appear in your django.po file
    NOT_STARTED = "NOT_STARTED", _("Inactive")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED   = "COMPLETED",   _("Completed")


class Action(models.Model):
    title = models.CharField(max_length=200, unique=True)

    # --- Short summary for cards/lists ---
    small_description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Short summary (max 255 characters)."
    )
    small_description_ga = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Small Description (Irish)")
    )

    # --- Full Descriptions & Updates ---
    description = SummernoteTextField(default="", blank=True)
    description_ga = SummernoteTextField(default="", blank=True, null=True, verbose_name=_("Description (Irish)"))

    update = SummernoteTextField(default="", blank=True, editable=True)
    update_ga = SummernoteTextField(default="", blank=True, null=True, verbose_name=_("Update (Irish)"))

    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name='actions'
    )

    status = models.CharField(
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.NOT_STARTED,
    )

    # --- Approval workflow ---
    is_approved = models.BooleanField(default=False)
    # FIREWALL: Irish text only goes live when a Superuser checks this
    is_ga_approved = models.BooleanField(default=False, verbose_name=_("Irish Content Approved"))

    # --- Attribution & Timestamps (Existing) ---
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="actions_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="actions_updated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_small_description(self):
        """Always switches to Irish immediately if text exists."""
        from django.utils.translation import get_language
        if get_language() == 'ga' and self.small_description_ga:
            return self.small_description_ga
        return self.small_description

    @property
    def display_description(self):
        """Always switches to Irish immediately if text exists."""
        from django.utils.translation import get_language
        if get_language() == 'ga' and self.description_ga:
            return self.description_ga
        return self.description

    @property
    def display_update(self):
        if not self.is_approved:
            return "" # Hides the progress text while waiting for approval
        from django.utils.translation import get_language
        if get_language() == 'ga' and self.update_ga:
            return self.update_ga
        return self.update if self.update else ""



    def __str__(self):
        return self.title

    