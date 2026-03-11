from django.urls import path
from .views import billing_view 

app_name = "billing"

urlpatterns = [
    path("", billing_view, name="billing"),
]
