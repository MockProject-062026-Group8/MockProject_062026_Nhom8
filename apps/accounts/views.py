# pyrefly: ignore [missing-import]
from django.shortcuts import render


def login_view(request):
    return render(request, "accounts/login.html")

def two_step_verification_view(request):
    return render(request, "accounts/2step_verification.html")

def activation_view(request, token):
    return render(request, 'accounts/account_activation.html', {'token': token})