from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

def landing_page(request):
    return render(request, "landing.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة")
            return render(request, "login.html", {"next": next_url})

        organization = getattr(user, "organization", None)
        if organization and organization.status != "active":
            messages.error(request, "حساب مؤسستك غير مفعّل")
            return redirect("account_inactive")

        login(request, user)

        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        return redirect("dashboard:dashboard")

    return render(request, "login.html", {"next": next_url})