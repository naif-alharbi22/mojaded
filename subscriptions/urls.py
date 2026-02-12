from django.urls import path
from .views import account_inactive

app_name = "subscriptions"

urlpatterns = [
    path("account-inactive/", account_inactive, name="account_inactive"),
]
