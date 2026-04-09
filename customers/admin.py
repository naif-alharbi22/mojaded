from django.contrib import admin
from common.admin import TenantModelAdmin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(TenantModelAdmin):
    list_display = ["name", "email", "phone", "organization", "created_at"]
    search_fields = ["name", "email", "phone"]
