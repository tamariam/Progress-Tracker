from django.db import models

# Cr# Import necessary modules from Django's core
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Define the Theme model
class Theme(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


# Define the Action model
class Action(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    progress = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    is_complete = models.BooleanField(default=False)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='actions')

    def save(self, *args, **kwargs):
        # Automatically update is_complete based on progress
        if self.progress == 100:
            self.is_complete = True
        else:
            self.is_complete = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
