from django.urls import path
from . import views
app_name = "subscriptions"

urlpatterns = [
    path("account-inactive/", views.account_inactive, name="account_inactive"),
    path("" , views.subscriptions, name="subscriptions"),
    path("new-subscriptions/", views.new_subscriptions, name="new_subscriptions"),
    path("edit-subscription/<int:subscription_id>/", views.edit_subscription, name="edit_subscription"),
    path("plans/", views.plans_view, name="plans"),
    path("plans/new/", views.new_plan, name="new_plan"),
    path("plans/edit/<int:plan_id>/", views.edit_plan, name="edit_plan"),
]
