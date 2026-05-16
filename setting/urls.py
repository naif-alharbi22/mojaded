from django.urls import path

from . import views

app_name = "setting"

urlpatterns = [
    path("", views.view_settings, name="view_settings"),

    # Users
    path("users/", views.users_list, name="users_list"),
    path("users/new/", views.new_user, name="new_user"),
    path("users/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),

    # Roles
    path("roles/", views.roles_list, name="roles_list"),
    path("roles/new/", views.new_role, name="new_role"),
    path("roles/<int:role_id>/edit/", views.edit_role, name="edit_role"),
    path("roles/<int:role_id>/delete/", views.delete_role, name="delete_role"),

    # Subscription statuses
    path("statuses/", views.statuses_list, name="statuses_list"),
    path("statuses/new/", views.new_status, name="new_status"),
    path("statuses/<int:status_id>/edit/", views.edit_status, name="edit_status"),
    path("statuses/<int:status_id>/delete/", views.delete_status, name="delete_status"),
]
