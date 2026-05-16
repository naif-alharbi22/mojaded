import secrets
import string

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from accounts.models import Role, User
from accounts.permissions import (
    PERMISSION_GROUPS,
    PERMISSION_LABELS,
    has_permission,
    is_organization_owner,
    permission_denied_response,
    require_permission,
)
from common.toast_utils import toast_response
from setting.forms import EditUserForm, NewUserForm, OrganizationForm, RoleForm, SubscriptionStatusForm
from subscriptions.models import SubscriptionStatus
from django.db.models import Q


# ---------- helpers ----------

def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _users_qs(organization):
    return User.objects.filter(organization=organization).select_related("role").order_by(
        "-id"
    )


def _roles_qs(organization):
    return (
        Role.objects.filter(organization=organization)
        .annotate(user_count=Count("users"))
        .order_by("-is_system", "name")
    )


def _statuses_qs(organization):
    return (
        SubscriptionStatus.objects
        .filter(Q(Organization=organization) | Q(Organization__isnull=True))
        .order_by("-is_default", "name")
    )


# ---------- main settings page ----------

@require_permission("settings.view")
def view_settings(request):
    org = request.user.organization

    if request.method == "POST":
        if not has_permission(request.user, "settings.edit"):
            return permission_denied_response(request, "settings.edit")
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الإعدادات بنجاح", type="success", close_modal=False)
    else:
        form = OrganizationForm(instance=org)

    # Make sure system roles exist for orgs that pre-date this feature.
    Role.ensure_system_roles(org)

    users = _users_qs(org)
    roles = _roles_qs(org)
    subscription_statuses = _statuses_qs(org)

    return render(request, "setting/index.html", {
        "form": form,
        "organization": org,
        "users": users,
        "roles": roles,
        "permission_groups": PERMISSION_GROUPS,
        "subscription_statuses": subscription_statuses,
    })


# ---------- users ----------

@require_permission("users.view")
def users_list(request):
    org = request.organization
    users = _users_qs(org)
    return render(request, "setting/_users_table.html", {
        "users": users,
        "organization": org,
    })


@require_permission("users.create")
def new_user(request):
    org = request.organization

    if request.method == "POST":
        form = NewUserForm(request.POST, organization=org)
        if form.is_valid():
            password = _generate_password()
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=password,
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
            )
            user.organization = org
            user.role = form.cleaned_data.get("role")
            user.save()
            return render(request, "setting/_password_modal.html", {
                "created_user": user,
                "password": password,
            })
    else:
        form = NewUserForm(organization=org)

    return render(request, "setting/_user_modal.html", {
        "form": form,
        "organization": org,
    })


@require_permission("users.edit")
def edit_user(request, user_id):
    org = request.organization
    target = User.objects.filter(id=user_id, organization=org).first()
    if target is None:
        return permission_denied_response(request, "users.edit")

    is_owner = is_organization_owner(target)

    if request.method == "POST":
        form = EditUserForm(request.POST, organization=org, user=target)
        if form.is_valid():
            target.first_name = form.cleaned_data.get("first_name", "")
            target.last_name = form.cleaned_data.get("last_name", "")
            if not is_owner:
                target.role = form.cleaned_data.get("role")
                target.is_active = form.cleaned_data.get("is_active", True)
            target.save()
            return toast_response("تم تحديث المستخدم بنجاح", type="success", name_trigger="usersChanged")
    else:
        form = EditUserForm(
            organization=org,
            user=target,
            initial={
                "first_name": target.first_name,
                "last_name": target.last_name,
                "role": target.role_id,
                "is_active": target.is_active,
            },
        )

    return render(request, "setting/_user_modal.html", {
        "form": form,
        "organization": org,
        "target_user": target,
        "is_owner": is_owner,
    })


@require_http_methods(["DELETE", "POST"])
@require_permission("users.delete")
def delete_user(request, user_id):
    org = request.organization
    target = User.objects.filter(id=user_id, organization=org).first()
    if target is None:
        return permission_denied_response(request, "users.delete")

    if is_organization_owner(target):
        return toast_response("لا يمكن حذف مالك المنشأة", type="error")
    if target.id == request.user.id:
        return toast_response("لا يمكنك حذف حسابك", type="error")

    target.delete()
    return toast_response("تم حذف المستخدم بنجاح", type="success", name_trigger="usersChanged")


# ---------- roles ----------

@require_permission("settings.view")
def roles_list(request):
    org = request.organization
    roles = _roles_qs(org)
    return render(request, "setting/_roles_grid.html", {
        "roles": roles,
    })


@require_permission("settings.edit")
def new_role(request):
    org = request.organization

    if request.method == "POST":
        form = RoleForm(request.POST, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم إنشاء الدور بنجاح", type="success", name_trigger="rolesChanged")
    else:
        form = RoleForm(organization=org)

    return render(request, "setting/_role_modal.html", {
        "form": form,
        "permission_groups": PERMISSION_GROUPS,
        "selected_permissions": set(form["permissions"].value() or []),
    })


@require_permission("settings.edit")
def edit_role(request, role_id):
    org = request.organization
    role = Role.objects.filter(id=role_id, organization=org).first()
    if role is None:
        return permission_denied_response(request, "settings.edit")

    if request.method == "POST":
        form = RoleForm(request.POST, instance=role, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الدور بنجاح", type="success", name_trigger="rolesChanged")
    else:
        form = RoleForm(instance=role, organization=org)

    selected = set(form["permissions"].value() or role.permissions or [])

    return render(request, "setting/_role_modal.html", {
        "form": form,
        "role": role,
        "permission_groups": PERMISSION_GROUPS,
        "selected_permissions": selected,
    })


@require_http_methods(["DELETE", "POST"])
@require_permission("settings.edit")
def delete_role(request, role_id):
    org = request.organization
    role = Role.objects.filter(id=role_id, organization=org).first()
    if role is None:
        return permission_denied_response(request, "settings.edit")
    if role.is_system:
        return toast_response("لا يمكن حذف دور النظام", type="error")
    if role.users.exists():
        return toast_response("هذا الدور مُستخدم — انقل المستخدمين أولًا", type="error")

    role.delete()
    return toast_response("تم حذف الدور بنجاح", type="success", name_trigger="rolesChanged")


# ---------- subscription statuses ----------

@require_permission("settings.view")
def statuses_list(request):
    org = request.organization
    statuses = _statuses_qs(org)
    return render(request, "setting/_statuses_table.html", {
        "subscription_statuses": statuses,
    })


@require_permission("settings.edit")
def new_status(request):
    org = request.organization

    if request.method == "POST":
        form = SubscriptionStatusForm(request.POST, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم إنشاء الحالة بنجاح", type="success", name_trigger="statusesChanged")
    else:
        form = SubscriptionStatusForm(organization=org)

    return render(request, "setting/_status_modal.html", {
        "form": form,
    })


@require_permission("settings.edit")
def edit_status(request, status_id):
    org = request.organization
    status = SubscriptionStatus.objects.filter(id=status_id, Organization=org).first()
    if status is None:
        return permission_denied_response(request, "settings.edit")

    if request.method == "POST":
        form = SubscriptionStatusForm(request.POST, instance=status, organization=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الحالة بنجاح", type="success", name_trigger="statusesChanged")
    else:
        form = SubscriptionStatusForm(instance=status, organization=org)

    return render(request, "setting/_status_modal.html", {
        "form": form,
        "status": status,
    })


@require_http_methods(["DELETE", "POST"])
@require_permission("settings.edit")
def delete_status(request, status_id):
    org = request.organization
    status = SubscriptionStatus.objects.filter(id=status_id, Organization=org).first()
    if status is None:
        return permission_denied_response(request, "settings.edit")
    if status.subscription_set.exists():
        return toast_response("هذه الحالة مُستخدمة — انقل الاشتراكات أولًا", type="error")

    status.delete()
    return toast_response("تم حذف الحالة بنجاح", type="success", name_trigger="statusesChanged")
