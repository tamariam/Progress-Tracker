from django.utils import translation


class AdminEnglishMiddleware:
    """Force English locale for Django admin only."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "/admin/" in request.path:
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        response = self.get_response(request)
        return response
