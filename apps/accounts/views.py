# pyrefly: ignore [missing-import]
from django.shortcuts import render


def login_view(request):
    return render(request, "accounts/login.html")

def activation_view(request, token):
    return render(request, 'accounts/account_activation.html', {'token': token})