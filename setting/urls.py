from django.urls import path
import setting.views as setting_views

app_name = "setting"

urlpatterns = [
    path("", setting_views.view_settings, name="view_settings"),
]
