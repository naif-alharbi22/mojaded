from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from accounts.models import User, PasswordResetCode
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


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "البريد الإلكتروني مطلوب")
            return render(request, "forgot_password.html")

        # Don't reveal whether the email exists — always behave the same
        user = User.objects.filter(email=email).first()
        if user:
            # Throttle: don't allow more than 1 code per 60 seconds
            recent = PasswordResetCode.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timezone.timedelta(seconds=60),
            ).exists()

            if not recent:
                reset_code = PasswordResetCode.create_for_user(user)
                send_reset_code_email(user, reset_code.code)

        # Stash the email in session so the verify page can use it
        request.session["password_reset_email"] = email
        messages.success(
            request,
            "إذا كان البريد مسجلًا لدينا، فقد تم إرسال رمز التحقق إليه."
        )
        return redirect("verify_code")

    return render(request, "forgot_password.html")


def verify_code_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    email = request.session.get("password_reset_email")
    if not email:
        return redirect("forgot_password")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        if not code or len(code) != 6:
            messages.error(request, "الرمز غير صحيح")
            return render(request, "verify_code.html", {"email": email})

        user = User.objects.filter(email=email).first()
        reset_code = None
        if user:
            reset_code = PasswordResetCode.objects.filter(
                user=user, code=code, used=False
            ).order_by("-created_at").first()

        if not reset_code or not reset_code.is_valid():
            messages.error(request, "الرمز غير صحيح أو منتهي الصلاحية")
            return render(request, "verify_code.html", {"email": email})

        # Mark code as verified — store the reset_code id in session for the next step
        request.session["password_reset_code_id"] = reset_code.id
        return redirect("reset_password")

    return render(request, "verify_code.html", {"email": email})


def reset_password_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    code_id = request.session.get("password_reset_code_id")
    if not code_id:
        return redirect("forgot_password")

    reset_code = PasswordResetCode.objects.filter(id=code_id, used=False).first()
    if not reset_code or not reset_code.is_valid():
        messages.error(request, "انتهت صلاحية الجلسة، حاول مرة أخرى")
        request.session.pop("password_reset_code_id", None)
        request.session.pop("password_reset_email", None)
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        errors = []
        if len(password) < 6:
            errors.append("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
        if password != password2:
            errors.append("كلمة المرور غير متطابقة")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "reset_password.html")

        with transaction.atomic():
            user = reset_code.user
            user.set_password(password)
            user.save()

            reset_code.used = True
            reset_code.save()

        request.session.pop("password_reset_code_id", None)
        request.session.pop("password_reset_email", None)

        messages.success(request, "تم تغيير كلمة المرور بنجاح، يمكنك تسجيل الدخول الآن")
        return redirect("login")

    return render(request, "reset_password.html")


def send_reset_code_email(user, code):
    subject = "رمز إعادة تعيين كلمة المرور — مُجدد"
    context = {"user": user, "code": code, "ttl_minutes": 10}

    text_body = render_to_string("emails/password_reset.txt", context)
    html_body = render_to_string("emails/password_reset.html", context)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=False,
    )


def logout_view(request):
    logout(request)
    return redirect("landing")