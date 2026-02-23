from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone



class OrganizationAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            organization = getattr(request.user, "organization", None)

            if organization and organization.status != "active":

                allowed_paths = [
                    reverse("account_inactive"),
                    reverse("logout"),
                ]

                if request.path not in allowed_paths:
                    return redirect("account_inactive")

        return self.get_response(request)

class PlatformAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if (
            path.startswith(settings.STATIC_URL)
            or path.startswith(settings.MEDIA_URL)
            or path.startswith("/admin/")
            or path == "/favicon.ico"
        ):
            return self.get_response(request)

        public_paths = {reverse("landing"), reverse("login"), reverse("account_inactive")}

        is_app_area = path not in public_paths

        if is_app_area:
            if not request.user.is_authenticated:
                return redirect(f"{reverse('login')}?next={path}")

            organization = getattr(request.user, "organization", None)
            if organization and organization.status != "active":
                return redirect("account_inactive")

        else:
            if path not in public_paths :
                return redirect("login")

        return self.get_response(request)
    

class FixedTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate("Asia/Riyadh")  
        response = self.get_response(request)
        timezone.deactivate()
        return response