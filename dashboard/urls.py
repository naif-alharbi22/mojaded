from django.urls import path
from .views import view_dashboard

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", view_dashboard, name="dashboard"),
]
