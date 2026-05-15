"""
Permission catalog for organization-scoped role-based access control.

Permissions are flat string codenames in the form `<feature>.<action>`.
The catalog below is the single source of truth — UI, validation, and
checks should all read from it instead of hard-coding strings.

The organization owner (organization.owner) always passes every check
and never has a Role assigned.
"""

from functools import wraps

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

PERMISSION_GROUPS = [
    {
        "key": "customers",
        "label": "العملاء",
        "icon": "users",
        "permissions": [
            ("customers.view",   "عرض العملاء"),
            ("customers.create", "إضافة عميل"),
            ("customers.edit",   "تعديل عميل"),
            ("customers.delete", "حذف عميل"),
        ],
    },
    {
        "key": "subscriptions",
        "label": "الاشتراكات",
        "icon": "credit-card",
        "permissions": [
            ("subscriptions.view",   "عرض الاشتراكات"),
            ("subscriptions.create", "إضافة اشتراك"),
            ("subscriptions.edit",   "تعديل اشتراك"),
            ("subscriptions.delete", "حذف اشتراك"),
        ],
    },
    {
        "key": "plans",
        "label": "الباقات",
        "icon": "box",
        "permissions": [
            ("plans.view",   "عرض الباقات"),
            ("plans.create", "إضافة باقة"),
            ("plans.edit",   "تعديل باقة"),
            ("plans.delete", "حذف باقة"),
        ],
    },
    {
        "key": "billing",
        "label": "الفواتير",
        "icon": "receipt",
        "permissions": [
            ("billing.view",   "عرض الفواتير"),
            ("billing.create", "إنشاء فاتورة"),
            ("billing.edit",   "تعديل فاتورة"),
            ("billing.delete", "حذف فاتورة"),
        ],
    },
    {
        "key": "users",
        "label": "المستخدمون",
        "icon": "user-cog",
        "permissions": [
            ("users.view",   "عرض المستخدمين"),
            ("users.create", "إضافة مستخدم"),
            ("users.edit",   "تعديل مستخدم"),
            ("users.delete", "حذف مستخدم"),
        ],
    },
    {
        "key": "settings",
        "label": "الإعدادات",
        "icon": "settings",
        "permissions": [
            ("settings.view", "عرض الإعدادات"),
            ("settings.edit", "تعديل الإعدادات"),
        ],
    },
]


ALL_PERMISSIONS = [code for group in PERMISSION_GROUPS for code, _ in group["permissions"]]

PERMISSION_LABELS = {
    code: label for group in PERMISSION_GROUPS for code, label in group["permissions"]
}


SYSTEM_ROLES = [
    {
        "slug": "admin",
        "name": "مسؤول",
        "description": "صلاحيات كاملة عدا حذف المنشأة",
        "permissions": list(ALL_PERMISSIONS),
    },
    {
        "slug": "manager",
        "name": "محرر بيانات",
        "description": "إدخال وتعديل البيانات دون إدارة المستخدمين أو الإعدادات",
        "permissions": [
            "customers.view", "customers.create", "customers.edit",
            "subscriptions.view", "subscriptions.create", "subscriptions.edit",
            "plans.view", "plans.create", "plans.edit",
            "billing.view", "billing.create", "billing.edit",
            "settings.view",
        ],
    },
    {
        "slug": "viewer",
        "name": "مشاهد",
        "description": "اطلاع فقط على البيانات دون أي تعديل",
        "permissions": [
            "customers.view",
            "subscriptions.view",
            "plans.view",
            "billing.view",
            "settings.view",
        ],
    },
]


def is_organization_owner(user):
    org = getattr(user, "organization", None)
    if not org:
        return False
    return org.owner_id == user.id


def has_permission(user, codename):
    """Return True if user has the given permission.

    The organization owner always returns True. Other users must have a role
    whose permissions list contains the codename. Unknown codenames return
    False (fail closed).
    """
    if not user or not user.is_authenticated:
        return False
    if codename not in PERMISSION_LABELS:
        return False
    if is_organization_owner(user):
        return True
    role = getattr(user, "role", None)
    if role is None:
        return False
    return codename in (role.permissions or [])


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def permission_denied_response(request, codename=None, message=None):
    """Build the appropriate "no permission" response for the request.

    HTMX requests get a modal (rendered as an OOB swap into
    `#permission-modal-mount`) plus a toast, with `HX-Reswap: none`
    so the originally-targeted element is left untouched. Regular page
    requests are redirected to the dedicated access-denied page.
    """
    label = PERMISSION_LABELS.get(codename, "") if codename else ""
    context = {
        "permission": codename,
        "permission_label": label,
        "message": message or "ليس لديك صلاحية للقيام بهذا الإجراء",
    }

    if _is_htmx(request):
        modal_html = render_to_string(
            "components/_no_permission_modal.html", context, request=request
        )
        toast_html = render_to_string(
            "components/toast.html",
            {
                "type": "error",
                "message": context["message"],
                "language": "ar",
                "close_modal": False,
            },
            request=request,
        )
        response = HttpResponse(modal_html + toast_html, status=200)
        response["HX-Reswap"] = "none"
        return response

    return render(request, "access_denied.html", context, status=200)


def require_permission(codename):
    """View decorator that gates a view behind a permission codename.

    Usage:
        @require_permission("customers.create")
        def new_customer(request): ...
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, codename):
                return permission_denied_response(request, codename)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*codenames):
    """View decorator: allow if the user holds ANY of the given codenames."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not any(has_permission(request.user, c) for c in codenames):
                return permission_denied_response(request, codenames[0] if codenames else None)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
