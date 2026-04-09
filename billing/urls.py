from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_view, name="billing"),
    path("new/", views.new_invoice, name="new_invoices"),
    path("edit/<int:invoice_id>/", views.edit_invoice, name="edit_invoice"),
]
