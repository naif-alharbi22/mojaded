"""
Utility functions for rendering toasts with HTMX OOB swaps.
"""

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import translation


def render_toast(message, type="success", language="ar", close_modal=True):
    """
    Render a toast notification HTML using HTMX OOB swap.

    Args:
        message: The message to display in the toast
        type: The type of toast (success, error, warning, info)
        close_modal: Whether to close the modal when toast is shown (default: True)

    Returns:
        HTML string with OOB swap directive
    """
    return render_to_string(
        "components/toast.html",
        {
            "type": type,
            "message": message,
            "language": language,
            "close_modal": close_modal,
        },
    )


def toast_response(message, type="success", name_trigger="refresh", close_modal=True):
    """
    Return an HttpResponse with a toast notification.

    Args:
        message: The message to display in the toast
        type: The type of toast (success, error, warning, info)
        name_trigger: The HTMX trigger name (default: "refresh")
        close_modal: Whether to close the modal when toast is shown (default: True)

    Returns:
        HttpResponse with toast HTML (OOB) and HX-Trigger: refresh
    """
    try:
        language = translation.get_language()
    except Exception:
        language = "ar"

    toast_html = render_toast(message, type, close_modal=close_modal, language=language)

    headers = {"HX-Trigger": name_trigger}

    if close_modal is False:
        headers["HX-Reswap"] = "none"

    return HttpResponse(toast_html, headers=headers)
