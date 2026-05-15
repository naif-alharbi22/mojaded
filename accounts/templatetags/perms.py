from django import template

from accounts.permissions import has_permission

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, codename):
    """{% has_perm "customers.create" as can_create %} → True/False."""
    request = context.get("request")
    if request is None:
        return False
    return has_permission(request.user, codename)


@register.filter(name="has_perm")
def has_perm_filter(user, codename):
    """{% if request.user|has_perm:"customers.create" %}"""
    return has_permission(user, codename)
