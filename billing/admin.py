from django.contrib import admin
from common.admin import TenantModelAdmin
from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(TenantModelAdmin):
    list_display = ["id", "subscription", "invoice_type", "amount", "status", "issue_date", "due_date", "organization"]
    list_filter = ["status", "invoice_type"]
