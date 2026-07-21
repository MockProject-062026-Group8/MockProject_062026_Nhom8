from django.urls import path
from . import views

app_name = 'accounts_api'
urlpatterns = [
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('activation/<str:token>/', views.ActivationAPIView.as_view(), name='activation'),
]