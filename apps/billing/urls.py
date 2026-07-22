from django.urls import path
from . import views

app_name = 'billing'
urlpatterns = [
    path('cost-billing/', views.billing_panel, name='cost_billing_panel'),
]