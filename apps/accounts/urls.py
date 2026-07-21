from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('2-step-verification/', views.login_view, name='2step_verification'),
    path('forgot-password/', views.login_view, name='forgot_password'),
    path('account-activation/<str:token>/', views.activation_view, name='account_activation'),
]