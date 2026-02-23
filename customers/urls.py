from django.urls import path
from .views import customers_view , new_customer

app_name = "customers"

urlpatterns = [
    path("", customers_view, name="customers"),
    path("new-customer/", new_customer, name="new_customer"),
]
