# pyrefly: ignore [missing-import]
from django.shortcuts import render

def activate_account(request):
    return render(request, "accounts/activate_account.html")


def login_view(request):
    return render(request, "accounts/login.html")