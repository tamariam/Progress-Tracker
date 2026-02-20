from django.utils import translation
from django.http import HttpResponseRedirect


class AdminEnglishMiddleware:
    """Force English locale for Django admin only."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/ga/admin/'):
            return HttpResponseRedirect(request.get_full_path().replace('/ga/admin/', '/en/admin/', 1))

        if "/admin/" in request.path:
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        response = self.get_response(request)
        return response
