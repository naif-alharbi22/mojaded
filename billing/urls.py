from django.urls import path
from .views import billing_view , new_invoices

app_name = "billing"

urlpatterns = [
    path("", billing_view, name="billing"),
    path("new-invoices/", new_invoices, name="new_invoices"),
]
