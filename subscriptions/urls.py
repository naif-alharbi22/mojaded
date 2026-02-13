from django.urls import path
from . import views
app_name = "subscriptions"

urlpatterns = [
    path("account-inactive/", views.account_inactive, name="account_inactive"),
    path("" , views.subscriptions, name="subscriptions"),
]
