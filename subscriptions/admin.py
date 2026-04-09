from django.contrib import admin
from common.admin import TenantModelAdmin
from .models import Plan, Subscription, AddOn, SubscriptionAddOn


class SubscriptionAddOnInline(admin.TabularInline):
    model = SubscriptionAddOn
    extra = 0


@admin.register(Plan)
class PlanAdmin(TenantModelAdmin):
    list_display = ["name", "amount", "billing_cycle", "organization"]
    search_fields = ["name"]


@admin.register(Subscription)
class SubscriptionAdmin(TenantModelAdmin):
    list_display = ["id", "customer", "plan", "status", "start_date", "next_billing_date", "organization"]
    list_filter = ["status", "subscription_type"]
    search_fields = ["customer__name"]
    inlines = [SubscriptionAddOnInline]


@admin.register(AddOn)
class AddOnAdmin(TenantModelAdmin):
    list_display = ["name", "amount", "billing_type", "organization"]
