from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from tracker_app.models import Objective, Theme,Action

# Register your models here.
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title',)
    search_fields = ('title',)

class ObjectiveAdmin(SummernoteModelAdmin):
    list_display = ('id', 'title', 'theme')
    search_fields = ('title', 'description')            

class ActionAdmin(SummernoteModelAdmin):
    list_display = ('id', 'title','description', 'update', 'is_progress', 'objective')
    search_fields = ('title', 'description')
    list_filter = ('is_progress', 'objective')
    list_editable = ('update',)

admin.site.register(Theme, ThemeAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Objective, ObjectiveAdmin)