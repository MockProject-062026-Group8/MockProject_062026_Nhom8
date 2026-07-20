# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("activate-account/", views.activate_account, name="activate_account")
]