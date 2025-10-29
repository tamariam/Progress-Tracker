from django.contrib import admin
from tracker_app.models import Theme,Action

# Register your models here.
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'progress', 'is_complete', 'theme')
    search_fields = ('title', 'description')
    list_filter = ('is_complete', 'theme')
    list_editable = ('progress',)

admin.site.register(Theme, ThemeAdmin)
admin.site.register(Action, ActionAdmin)