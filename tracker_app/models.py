# Cr# Import necessary modules from Django's core

from django.db import models
from django_summernote.fields import SummernoteTextField

# Define the Theme model
class Theme(models.Model):
    title = models.CharField(max_length=200,unique=True)

    def __str__(self):
        return self.title

#Define the Objectives model
class Objective(models.Model):
    title=models.CharField(max_length=200,unique=True)
    description = SummernoteTextField(default="")
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='objectives')

    def __str__(self):
        return self.title

# Define the Action model
class Action(models.Model):
    title = models.CharField(max_length=200,unique=True)
    description = SummernoteTextField(default="")
    update = SummernoteTextField(blank=True,editable=True)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, related_name='actions')
    is_progress = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        # Automatically update is_progress based on update
        if self.update.strip() != "":
            self.is_progress = True
        else:
            self.is_progress = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
