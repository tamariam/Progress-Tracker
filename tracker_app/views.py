from django.shortcuts import render
from.models import Theme, Action    



# Create your views here.
def home(request):
    print("--- The 'home' view is being executed. ---")
    themes = Theme.objects.all().prefetch_related('actions')
    return render(request, 'tracker_app/home.html', {'themes': themes})
