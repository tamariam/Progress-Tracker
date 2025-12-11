from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django_summernote.fields import SummernoteTextField


class Theme(models.Model):
    title = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.title


class Objective(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = SummernoteTextField(default="", blank=True)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='objectives')

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class ActionStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not started"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED   = "COMPLETED",   "Completed"


class Action(models.Model):
    title = models.CharField(max_length=200, unique=True)

    # Short summary for cards/lists
    small_description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Short summary (max 255 characters)."
    )

    description = SummernoteTextField(default="", blank=True)
    update = SummernoteTextField(default="", blank=True, editable=True)

    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name='actions'
    )

    # Explicit status + fast boolean
    status = models.CharField(
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.NOT_STARTED,
    )

    # Approval workflow
    is_approved = models.BooleanField(default=False)

    # Attribution
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="actions_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="actions_updated",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    