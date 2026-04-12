from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.db import transaction
from accounts.models import User
from organizations.models import Organization

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

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        org_name = request.POST.get("org_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        errors = []

        if not org_name:
            errors.append("اسم المنشأة مطلوب")
        if not username:
            errors.append("اسم المستخدم مطلوب")
        if not email:
            errors.append("البريد الإلكتروني مطلوب")
        if not password:
            errors.append("كلمة المرور مطلوبة")
        if password != password2:
            errors.append("كلمة المرور غير متطابقة")
        if len(password) < 6:
            errors.append("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
        if User.objects.filter(username=username).exists():
            errors.append("اسم المستخدم مستخدم بالفعل")
        if User.objects.filter(email=email).exists():
            errors.append("البريد الإلكتروني مستخدم بالفعل")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "register.html", {
                "org_name": org_name,
                "username": username,
                "email": email,
            })

        # Create org + user in a transaction
        with transaction.atomic():
            # Generate unique slug
            base_slug = slugify(org_name, allow_unicode=True) or "org"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            org = Organization.objects.create(
                name=org_name,
                slug=slug,
                owner=user,
                status="active",
            )

            user.organization = org
            user.save()

        login(request, user)
        return redirect("dashboard:dashboard")

    return render(request, "register.html")


def logout_view(request):
    logout(request)
    return redirect("landing")